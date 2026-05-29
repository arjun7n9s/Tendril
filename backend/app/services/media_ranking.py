"""Source ranking — the cheap gate before expensive transcription.

Uses Featherless (a low-cost open model) to score candidate sources and pick
the top N worth processing. If Featherless is unavailable, falls back to a
deterministic heuristic so the pipeline always produces a ranking.
"""

from __future__ import annotations

import json
from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.logging_setup import get_logger
from app.models.account import Account
from app.models.enums import MediaScanStage, MediaSourceStatus, MediaSourceType
from app.models.icp import ICPProfile
from app.models.media_source import MediaSource
from app.prompts import load_prompt, render_prompt
from app.services.media_scan_events import MediaScanEventLogger

log = get_logger("media_ranking")

# Deterministic priors by source type for the heuristic fallback.
_TYPE_PRIOR = {
    MediaSourceType.earnings_call: 0.9,
    MediaSourceType.youtube: 0.8,
    MediaSourceType.webinar: 0.72,
    MediaSourceType.interview: 0.7,
    MediaSourceType.conference: 0.6,
    MediaSourceType.podcast: 0.8,
    MediaSourceType.other: 0.5,
}


def _heuristic_score(src: MediaSource) -> float:
    score = _TYPE_PRIOR.get(src.source_type, 0.5)
    if src.transcript_available:
        score += 0.05
    # Recency: prefer sources published in the last ~30 days.
    if src.published_at is not None:
        try:
            from datetime import UTC, datetime

            age_days = (datetime.now(UTC) - src.published_at).days
            if age_days <= 30:
                score += 0.05
            elif age_days >= 120:
                score -= 0.1
        except Exception:
            pass
    return max(0.0, min(1.0, score))


def _apply_heuristic(
    db: Session,
    *,
    sources: list[MediaSource],
    max_select: int,
    events: MediaScanEventLogger,
) -> list[MediaSource]:
    scored = sorted(sources, key=_heuristic_score, reverse=True)
    for idx, src in enumerate(scored):
        src.rank_score = _heuristic_score(src)
        if idx < max_select:
            src.status = MediaSourceStatus.selected
            src.rank_reason = "heuristic: high-value source type / recency"
        else:
            src.status = MediaSourceStatus.skipped
            src.rank_reason = "heuristic: capped below selection threshold"
        db.add(src)
    db.flush()
    events.info(
        "ranked sources via heuristic fallback",
        selected=min(max_select, len(scored)),
        total=len(scored),
    )
    return [s for s in scored if s.status == MediaSourceStatus.selected]


async def rank_sources(
    db: Session,
    *,
    account: Account,
    icp: ICPProfile | None,
    sources: list[MediaSource],
    events: MediaScanEventLogger,
    max_select: int,
) -> list[MediaSource]:
    """Rank and select sources. Featherless first, heuristic fallback."""
    if not sources:
        return []

    settings = get_settings()
    if not settings.featherless_configured():
        return _apply_heuristic(db, sources=sources, max_select=max_select, events=events)

    candidates = [
        {
            "source_url": s.source_url,
            "source_type": s.source_type.value,
            "title": s.title or "",
            "publisher": s.publisher or "",
            "transcript_available": s.transcript_available,
            "published_at": s.published_at.isoformat() if s.published_at else None,
        }
        for s in sources
    ]

    try:
        from app.services.featherless_client import FeatherlessClient

        system_prompt = load_prompt("rank_media_sources.system.md")
        user_prompt = render_prompt(
            "rank_media_sources.user.md",
            account_name=account.name,
            account_domain=account.domain or "",
            account_industry=account.industry or "",
            icp_tech_keywords=", ".join((icp.tech_keywords_json or []) if icp else []),
            icp_pain_keywords=", ".join((icp.pain_keywords_json or []) if icp else []),
            today=date.today().isoformat(),
            candidates_json=json.dumps(candidates, ensure_ascii=False),
            max_select=max_select,
        )
        async with FeatherlessClient() as fc:
            payload, meta = await fc.complete_json(
                system_prompt=system_prompt, user_prompt=user_prompt
            )
    except Exception as exc:
        events.warning(
            "Featherless ranking failed; using heuristic",
            error_type=type(exc).__name__,
        )
        return _apply_heuristic(db, sources=sources, max_select=max_select, events=events)

    rankings = payload.get("rankings") if isinstance(payload, dict) else None
    if not isinstance(rankings, list) or not rankings:
        return _apply_heuristic(db, sources=sources, max_select=max_select, events=events)

    by_url = {s.source_url: s for s in sources}
    selected: list[MediaSource] = []
    # Sort model rankings by score desc and honor the cap.
    ordered = sorted(
        rankings,
        key=lambda r: float(r.get("rank_score", 0.0)) if isinstance(r, dict) else 0.0,
        reverse=True,
    )
    selected_count = 0
    for r in ordered:
        if not isinstance(r, dict):
            continue
        src = by_url.get(r.get("source_url", ""))
        if src is None:
            continue
        try:
            src.rank_score = max(0.0, min(1.0, float(r.get("rank_score", 0.0))))
        except (TypeError, ValueError):
            src.rank_score = 0.0
        src.rank_reason = str(r.get("rank_reason", ""))[:512]
        wants = bool(r.get("select")) and selected_count < max_select
        if wants:
            src.status = MediaSourceStatus.selected
            selected.append(src)
            selected_count += 1
        else:
            src.status = MediaSourceStatus.skipped
        db.add(src)

    # If the model selected nothing, fall back to top-N by its own scores.
    if not selected:
        for src in sorted(sources, key=lambda s: s.rank_score or 0.0, reverse=True)[:max_select]:
            src.status = MediaSourceStatus.selected
            selected.append(src)
            db.add(src)

    db.flush()
    events.featherless_call(
        f"ranked {len(sources)} sources, selected {len(selected)}",
        stage=MediaScanStage.rank_sources,
        model=meta.model,
        duration_ms=meta.duration_ms,
        selected=len(selected),
    )
    return selected
