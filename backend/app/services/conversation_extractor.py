"""Conversation signal extraction.

Two-tier, cost-aware extraction over a scrubbed transcript:

1. **Relevance filter (cheap):** Featherless scores transcript chunks and drops
   the ones unlikely to contain GTM signals, so the expensive model only sees
   high-value text. Falls back to a keyword heuristic if Featherless is down.
2. **Structured extraction (strong):** AIMLAPI turns the surviving chunks into
   validated, timestamped `ConversationSignal` rows. In mock mode, deterministic
   fixtures stand in for the model.

Validation mirrors the web extractor: confidence floor, sensitive-content drop,
forbidden-phrase drop, known signal types only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.logging_setup import get_logger
from app.models.account import Account
from app.models.conversation_signal import ConversationSignal
from app.models.enums import MediaScanStage, PrivacyStatus, SignalType
from app.models.icp import ICPProfile
from app.models.media_source import MediaSource
from app.models.transcript import Transcript
from app.prompts import load_prompt, render_prompt
from app.services.media_fixtures import fixture_key_for_url, load_conversation_signals
from app.services.media_scan_events import MediaScanEventLogger

log = get_logger("conversation_extractor")

_VALID_SIGNAL_TYPES = {t.value for t in SignalType}
_MIN_CONFIDENCE = 0.45

_SENSITIVE_TERMS = (
    "religion",
    "religious",
    "ethnic",
    "racial",
    "sexual orientation",
    "gender identity",
    "political",
    "health condition",
    "medical history",
    "disability",
)
_FORBIDDEN_PHRASES = ("i saw you", "i noticed you", "i saw your", "i noticed your")

# Keywords that flag a chunk as likely signal-bearing in the heuristic filter.
_RELEVANCE_KEYWORDS = (
    "migrat", "vendor", "evaluat", "budget", "procure", "launch", "hiring",
    "hire", "reliability", "observability", "snowflake", "kafka", "priority",
    "initiative", "replace", "timeline", "quarter", "roadmap", "scale",
)


@dataclass
class ChunkRelevance:
    index: int
    relevant: bool
    score: float


def _looks_sensitive(text: str | None) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(t in lower for t in _SENSITIVE_TERMS)


def _has_forbidden_phrase(text: str | None) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(p in lower for p in _FORBIDDEN_PHRASES)


def _coerce_signal_type(raw: Any) -> SignalType:
    if isinstance(raw, str) and raw in _VALID_SIGNAL_TYPES:
        return SignalType(raw)
    return SignalType.other


def _heuristic_relevant_segments(segments: list[dict]) -> list[dict]:
    out = []
    for seg in segments:
        text = (seg.get("text") or "").lower()
        if any(k in text for k in _RELEVANCE_KEYWORDS):
            out.append(seg)
    return out or segments  # never starve the extractor entirely


async def _featherless_filter_segments(
    segments: list[dict],
    *,
    events: MediaScanEventLogger,
) -> list[dict]:
    """Cheap relevance gate. Returns the subset worth extracting from."""
    settings = get_settings()
    if not settings.featherless_configured() or not segments:
        return _heuristic_relevant_segments(segments)

    try:
        from app.services.featherless_client import FeatherlessClient

        numbered = [
            {"index": i, "text": s.get("text", "")} for i, s in enumerate(segments)
        ]
        system = (
            "You filter transcript chunks for B2B sales relevance. Return JSON "
            '{"relevant_indices": [int, ...]} listing only chunks that mention '
            "buying triggers: migrations, vendor evaluation/dissatisfaction, "
            "budget, hiring tied to a project, launches, timelines, or executive "
            "priorities. Be selective."
        )
        user = json.dumps(numbered, ensure_ascii=False)
        async with FeatherlessClient() as fc:
            payload, meta = await fc.complete_json(system_prompt=system, user_prompt=user)
        idxs = payload.get("relevant_indices") if isinstance(payload, dict) else None
        if isinstance(idxs, list) and idxs:
            keep = {int(i) for i in idxs if isinstance(i, (int, float))}
            filtered = [s for i, s in enumerate(segments) if i in keep]
            events.featherless_call(
                f"relevance filter kept {len(filtered)}/{len(segments)} chunks",
                stage=MediaScanStage.extract_signals,
                model=meta.model,
                duration_ms=meta.duration_ms,
            )
            return filtered or _heuristic_relevant_segments(segments)
    except Exception as exc:
        events.warning(
            "Featherless relevance filter failed; using heuristic",
            error_type=type(exc).__name__,
        )
    return _heuristic_relevant_segments(segments)


def _validate(raw: dict, *, segments: list[dict]) -> tuple[dict | None, str | None]:
    if not isinstance(raw, dict):
        return None, "not_a_dict"
    title = (raw.get("title") or "").strip()
    if not title:
        return None, "missing_title"
    try:
        confidence = float(raw.get("confidence"))
    except (TypeError, ValueError):
        return None, "confidence_not_numeric"
    if confidence < _MIN_CONFIDENCE:
        return None, "confidence_below_threshold"
    confidence = max(0.0, min(1.0, confidence))

    fact = (raw.get("fact_text") or "").strip() or None
    inference = (raw.get("inference_text") or "").strip() or None
    summary = (raw.get("summary") or "").strip() or None
    action = (raw.get("recommended_action") or "").strip() or None
    quote = (raw.get("quote_text") or "").strip() or None

    combined = " ".join(s for s in (title, summary, fact, inference, action, quote) if s)
    if _looks_sensitive(combined):
        return None, "sensitive_personal_content"
    if _has_forbidden_phrase(combined):
        return None, "forbidden_phrase"

    def _num(key: str) -> float | None:
        try:
            return float(raw.get(key))
        except (TypeError, ValueError):
            return None

    return (
        {
            "signal_type": _coerce_signal_type(raw.get("signal_type")),
            "title": title[:512],
            "summary": summary,
            "fact_text": fact,
            "inference_text": inference,
            "recommended_action": action,
            "quote_text": quote,
            "quote_start_seconds": _num("quote_start_seconds"),
            "quote_end_seconds": _num("quote_end_seconds"),
            "speaker_label": (raw.get("speaker_label") or "").strip()[:128] or None,
            "confidence": confidence,
        },
        None,
    )


def _persist_signals(
    db: Session,
    *,
    job_id: str,
    account: Account,
    source: MediaSource,
    transcript: Transcript,
    validated: list[dict],
    privacy_status: PrivacyStatus,
) -> list[ConversationSignal]:
    today = date.today()
    observed = source.published_at.date() if source.published_at else today
    recency = max(0, (today - observed).days)
    persisted: list[ConversationSignal] = []
    for s in validated:
        sig = ConversationSignal(
            media_scan_job_id=job_id,
            account_id=account.id,
            media_source_id=source.id,
            media_asset_id=source.media_asset_id,
            transcript_id=transcript.id,
            signal_type=s["signal_type"],
            title=s["title"],
            summary=s["summary"],
            fact_text=s["fact_text"],
            inference_text=s["inference_text"],
            recommended_action=s["recommended_action"],
            source_url=source.source_url,
            quote_text=s["quote_text"],
            quote_start_seconds=s["quote_start_seconds"],
            quote_end_seconds=s["quote_end_seconds"],
            speaker_label=s["speaker_label"],
            observed_at=observed,
            confidence=s["confidence"],
            recency_days=recency,
            privacy_status=privacy_status,
            metadata_json={"source": "conversation_extractor"},
        )
        db.add(sig)
        persisted.append(sig)
    db.flush()
    return persisted


async def extract_conversation_signals(
    db: Session,
    *,
    job_id: str,
    account: Account,
    icp: ICPProfile | None,
    source: MediaSource,
    transcript: Transcript,
    events: MediaScanEventLogger,
    live: bool,
) -> list[ConversationSignal]:
    """Extract validated, timestamped conversation signals for one source."""
    segments = transcript.segments_json or []
    privacy_status = transcript.pii_status or PrivacyStatus.scrubbed

    # Mock / fixture path: deterministic, no model spend.
    fixture_key = fixture_key_for_url(source.source_url) or (
        (source.metadata_json or {}).get("fixture_key") or ""
    )
    settings = get_settings()
    use_fixture = (not live) or not settings.aiml_configured()
    if use_fixture and fixture_key:
        raw_signals = load_conversation_signals(fixture_key)
        validated: list[dict] = []
        for raw in raw_signals:
            sig, _reason = _validate(raw, segments=segments)
            if sig is not None:
                validated.append(sig)
        persisted = _persist_signals(
            db,
            job_id=job_id,
            account=account,
            source=source,
            transcript=transcript,
            validated=validated,
            privacy_status=privacy_status,
        )
        events.info(
            f"extracted {len(persisted)} conversation signals (fixture)",
            stage=MediaScanStage.extract_signals,
            signal_count=len(persisted),
        )
        return persisted

    # Live path: cheap relevance filter, then strong structured extraction.
    relevant = await _featherless_filter_segments(segments, events=events)

    from app.services.aiml_client import (
        AimlClient,
        AimlExtractionError,
        AimlNotConfiguredError,
    )

    try:
        system_prompt = load_prompt("extract_conversation_signals.system.md")
        user_prompt = render_prompt(
            "extract_conversation_signals.user.md",
            account_name=account.name,
            account_domain=account.domain or "",
            account_industry=account.industry or "",
            icp_tech_keywords=", ".join((icp.tech_keywords_json or []) if icp else []),
            icp_competitor_keywords=", ".join(
                (icp.competitor_keywords_json or []) if icp else []
            ),
            source_title=source.title or "",
            source_publisher=source.publisher or "",
            source_url=source.source_url,
            today=date.today().isoformat(),
            segments_json=json.dumps(relevant, ensure_ascii=False),
        )
        async with AimlClient() as aiml:
            payload, meta = await aiml.complete_json(
                slot="extraction",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000,
            )
    except (AimlNotConfiguredError, AimlExtractionError) as exc:
        events.warning(
            "AIMLAPI conversation extraction failed",
            stage=MediaScanStage.extract_signals,
            error_type=type(exc).__name__,
        )
        # Fall back to fixtures if available so the demo still yields signals.
        if fixture_key:
            raw_signals = load_conversation_signals(fixture_key)
            validated = []
            for raw in raw_signals:
                sig, _r = _validate(raw, segments=segments)
                if sig is not None:
                    validated.append(sig)
            return _persist_signals(
                db,
                job_id=job_id,
                account=account,
                source=source,
                transcript=transcript,
                validated=validated,
                privacy_status=privacy_status,
            )
        return []

    raw_signals = payload.get("signals") if isinstance(payload, dict) else None
    if not isinstance(raw_signals, list):
        events.warning("extraction returned no signals array", stage=MediaScanStage.extract_signals)
        return []

    validated = []
    rejected = 0
    for raw in raw_signals:
        sig, _reason = _validate(raw, segments=segments)
        if sig is None:
            rejected += 1
            continue
        validated.append(sig)

    persisted = _persist_signals(
        db,
        job_id=job_id,
        account=account,
        source=source,
        transcript=transcript,
        validated=validated,
        privacy_status=privacy_status,
    )
    events.aiml_call(
        f"extracted {len(persisted)} valid / {len(raw_signals)} raw conversation signals",
        stage=MediaScanStage.extract_signals,
        model=meta.model,
        duration_ms=meta.duration_ms,
        valid=len(persisted),
        rejected=rejected,
    )
    return persisted
