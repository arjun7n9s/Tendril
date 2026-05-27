"""AI/ML-powered signal extractor.

Replaces Phase 3's `_placeholder_live_extract` with a real call to the
AIML extraction model. Strict validation per the implementation plan:

- evidence_url must be present
- confidence must be >= 0.45
- signals referencing sensitive personal attributes are dropped
- signals must use a known signal_type or are coerced to "other"

A failure to extract from one document does not fail the scan.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.logging_setup import get_logger
from app.models.account import Account
from app.models.enums import FetchStatus, ScanStatus, SignalType
from app.models.evidence import EvidenceDocument
from app.models.icp import ICPProfile
from app.models.scan import Scan
from app.models.signal import Signal
from app.prompts import load_prompt, render_prompt
from app.services.aiml_client import AimlClient, AimlExtractionError
from app.services.scan_events import ScanEventLogger

log = get_logger("extractor")

_VALID_SIGNAL_TYPES = {t.value for t in SignalType}

_SENSITIVE_TERMS = (
    "religion",
    "religious",
    "ethnic",
    "race ",
    "racial",
    "sexual orientation",
    "gender identity",
    "political",
    "health condition",
    "medical history",
    "disability",
)

_FORBIDDEN_PHRASES = (
    "i saw you",
    "i noticed you",
    "i saw your",
    "i noticed your",
)

# Aggressive cap so a giant page does not blow context. Models handle 8k
# input fine; we keep it tight to control cost.
_MAX_CONTENT_CHARS = 8000


@dataclass
class ExtractionRejection:
    evidence_url: str
    reason: str


def _looks_sensitive(text: str | None) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(term in lower for term in _SENSITIVE_TERMS)


def _has_forbidden_phrase(text: str | None) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(p in lower for p in _FORBIDDEN_PHRASES)


def _coerce_signal_type(raw: Any) -> SignalType:
    if isinstance(raw, str) and raw in _VALID_SIGNAL_TYPES:
        return SignalType(raw)
    return SignalType.other


def _parse_observed_at(raw: Any) -> date:
    if isinstance(raw, str):
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


def _truncate_for_prompt(text: str | None) -> str:
    if not text:
        return ""
    if len(text) <= _MAX_CONTENT_CHARS:
        return text
    return text[: _MAX_CONTENT_CHARS] + "\n\n[content truncated]"


def _validate_signal(
    raw: dict[str, Any], evidence_url: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (validated_signal, rejection_reason)."""
    if not isinstance(raw, dict):
        return None, "not_a_dict"

    declared_url = raw.get("evidence_url")
    if not isinstance(declared_url, str) or not declared_url.strip():
        return None, "missing_evidence_url"
    # The model must cite the same URL that produced the page.
    if declared_url.strip() != evidence_url:
        return None, "evidence_url_mismatch"

    confidence_raw = raw.get("confidence")
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        return None, "confidence_not_numeric"
    if confidence < 0.45:
        return None, "confidence_below_threshold"
    confidence = max(0.0, min(1.0, confidence))

    title = (raw.get("title") or "").strip()
    if not title:
        return None, "missing_title"

    fact_text = (raw.get("fact_text") or "").strip() or None
    inference_text = (raw.get("inference_text") or "").strip() or None
    summary = (raw.get("summary") or "").strip() or None
    recommended_action = (raw.get("recommended_action") or "").strip() or None

    combined = " ".join(
        s for s in (title, summary, fact_text, inference_text, recommended_action) if s
    )
    if _looks_sensitive(combined):
        return None, "sensitive_personal_content"
    if _has_forbidden_phrase(combined):
        return None, "forbidden_phrase"

    signal_type = _coerce_signal_type(raw.get("signal_type"))
    observed_at = _parse_observed_at(raw.get("observed_at"))

    return (
        {
            "signal_type": signal_type,
            "title": title[:512],
            "summary": summary,
            "fact_text": fact_text,
            "inference_text": inference_text,
            "recommended_action": recommended_action,
            "evidence_url": declared_url.strip(),
            "observed_at": observed_at,
            "confidence": confidence,
        },
        None,
    )


def _build_user_prompt(
    *,
    account: Account,
    icp: ICPProfile | None,
    evidence: EvidenceDocument,
    today: date,
) -> str:
    return render_prompt(
        "extract_signals.user.md",
        account_name=account.name,
        account_domain=account.domain or "",
        account_industry=account.industry or "",
        icp_tech_keywords=", ".join((icp.tech_keywords_json or []) if icp else []),
        icp_pain_keywords=", ".join((icp.pain_keywords_json or []) if icp else []),
        icp_competitor_keywords=", ".join(
            (icp.competitor_keywords_json or []) if icp else []
        ),
        evidence_url=evidence.url,
        evidence_title=evidence.title or "",
        today=today.isoformat(),
        evidence_content=_truncate_for_prompt(evidence.content_markdown),
    )


async def extract_signals_for_evidence(
    *,
    aiml: AimlClient,
    account: Account,
    icp: ICPProfile | None,
    evidence: EvidenceDocument,
) -> tuple[list[dict[str, Any]], list[ExtractionRejection], int]:
    """Returns (validated_signals, rejections, duration_ms)."""
    system_prompt = load_prompt("extract_signals.system.md")
    user_prompt = _build_user_prompt(
        account=account, icp=icp, evidence=evidence, today=date.today()
    )

    try:
        payload, meta = await aiml.complete_json(
            slot="extraction",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except AimlExtractionError as exc:
        return [], [ExtractionRejection(evidence.url, f"non_json_response: {exc}")], 0

    raw_signals = payload.get("signals") if isinstance(payload, dict) else None
    if not isinstance(raw_signals, list):
        return [], [ExtractionRejection(evidence.url, "missing_signals_array")], meta.duration_ms

    validated: list[dict[str, Any]] = []
    rejections: list[ExtractionRejection] = []
    for raw in raw_signals:
        sig, reason = _validate_signal(raw, evidence_url=evidence.url)
        if sig is None:
            rejections.append(ExtractionRejection(evidence.url, reason or "rejected"))
            continue
        validated.append(sig)
    return validated, rejections, meta.duration_ms


async def extract_signals_live(
    db: Session,
    *,
    scan: Scan,
    account: Account,
    icp: ICPProfile | None,
    evidence_rows: list[EvidenceDocument],
    aiml: AimlClient,
    events: ScanEventLogger,
) -> list[Signal]:
    """Run live extraction across every successfully fetched evidence document.

    Persists Signal rows for all validated outputs. Rejections are recorded
    as scan_events with a sanitized reason. One document failing does not
    fail the scan.
    """
    persisted: list[Signal] = []
    for ev in evidence_rows:
        if ev.fetch_status != FetchStatus.success or not ev.content_markdown:
            continue
        try:
            validated, rejections, duration_ms = await extract_signals_for_evidence(
                aiml=aiml, account=account, icp=icp, evidence=ev
            )
        except Exception as exc:  # noqa: BLE001
            events.warning(
                "extraction call failed",
                evidence_id=ev.id,
                error_type=type(exc).__name__,
            )
            continue

        for s in validated:
            sig = Signal(
                scan_id=scan.id,
                account_id=account.id,
                person_id=None,
                signal_type=s["signal_type"],
                title=s["title"],
                summary=s["summary"],
                fact_text=s["fact_text"],
                inference_text=s["inference_text"],
                recommended_action=s["recommended_action"],
                evidence_url=s["evidence_url"],
                evidence_document_id=ev.id,
                observed_at=s["observed_at"],
                confidence=s["confidence"],
                recency_days=_recency_days(s["observed_at"]),
                metadata_json={"source": "live_extractor"},
            )
            db.add(sig)
            persisted.append(sig)

        events.aiml_call(
            message=(
                f"extracted {len(validated)} valid / {len(validated) + len(rejections)} "
                f"raw signals from {ev.url}"
            ),
            phase=ScanStatus.extracting,
            tool="aiml_extractor",
            evidence_id=ev.id,
            valid_signal_count=len(validated),
            rejected_signal_count=len(rejections),
            duration_ms=duration_ms,
        )

        if rejections:
            for r in rejections:
                events.warning(
                    "rejected extracted signal",
                    evidence_id=ev.id,
                    reason=r.reason,
                )
    db.flush()
    return persisted


def _recency_days(observed_at: date) -> int:
    return max(0, (date.today() - observed_at).days)
