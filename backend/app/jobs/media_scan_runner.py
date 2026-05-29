"""Durable media-scan pipeline orchestrator.

Walks the stages:

    discover_sources -> rank_sources -> resolve_media -> hash_media ->
    transcribe -> scrub_transcript -> extract_signals -> write_memory ->
    score_account -> notify -> completed

Each stage is idempotent and records its completion (plus any outputs needed by
later stages) in `MediaScanJob.stage_state_json`. The runner skips stages that
are already recorded, so a process restart or a `resume` call continues from the
last incomplete stage instead of starting over — and CAS dedup guarantees the
expensive transcribe stage never double-bills.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_sessionmaker
from app.logging_setup import get_logger
from app.models.account import Account
from app.models.conversation_signal import ConversationSignal
from app.models.enums import (
    MediaScanMode,
    MediaScanStage,
    MediaSourceStatus,
    NotificationType,
    PrivacyStatus,
)
from app.models.helpers import as_str
from app.models.media_asset import MediaAsset
from app.models.media_scan_job import MediaScanJob
from app.models.media_source import MediaSource
from app.models.transcript import Transcript
from app.services.conversation_extractor import extract_conversation_signals
from app.services.cost import (
    estimate_llm_calls_usd,
    estimate_transcription_usd,
    would_exceed_budget,
)
from app.services.media_discovery import discover_sources_live, discover_sources_mock
from app.services.media_memory import write_conversation_memory
from app.services.media_ranking import rank_sources
from app.services.media_resolution import resolve_and_hash
from app.services.media_scan_events import MediaScanEventLogger
from app.services.media_scoring import compute_score_delta
from app.services.notifications import create_notification
from app.services.pii_scrubber import scrub_segments
from app.services.scorer import load_default_icp
from app.services.transcription import transcribe_source

log = get_logger("media_scan_runner")

# Stage execution order and progress weighting.
_STAGE_ORDER: list[MediaScanStage] = [
    MediaScanStage.discover_sources,
    MediaScanStage.rank_sources,
    MediaScanStage.resolve_media,
    MediaScanStage.hash_media,
    MediaScanStage.transcribe,
    MediaScanStage.scrub_transcript,
    MediaScanStage.extract_signals,
    MediaScanStage.write_memory,
    MediaScanStage.score_account,
    MediaScanStage.notify,
]

_STAGE_PROGRESS = {
    MediaScanStage.discover_sources: 10,
    MediaScanStage.rank_sources: 20,
    MediaScanStage.resolve_media: 30,
    MediaScanStage.hash_media: 40,
    MediaScanStage.transcribe: 60,
    MediaScanStage.scrub_transcript: 70,
    MediaScanStage.extract_signals: 85,
    MediaScanStage.write_memory: 92,
    MediaScanStage.score_account: 97,
    MediaScanStage.notify: 100,
}


def _now() -> datetime:
    return datetime.now(UTC)


def run_media_scan(job_id: str) -> None:
    """Entry point for FastAPI BackgroundTasks. Opens its own session."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        job = db.get(MediaScanJob, job_id)
        if job is None:
            log.warning("media_scan_runner.missing_job", job_id=job_id)
            return
        if job.status == MediaScanStage.completed:
            log.info("media_scan_runner.skip_completed", job_id=job_id)
            return

        events = MediaScanEventLogger(db, job_id)
        job.attempt_count = (job.attempt_count or 0) + 1
        job.started_at = job.started_at or _now()
        job.last_error = None
        db.add(job)
        db.commit()

        try:
            _execute(db, job, events)
        except Exception as exc:
            log.error("media_scan_runner.failed", job_id=job_id, error=str(exc))
            job.status = MediaScanStage.failed
            job.last_error = f"{type(exc).__name__}: {exc}"
            db.add(job)
            try:
                events.error(
                    "media scan failed (resumable)",
                    error=str(exc),
                    error_type=type(exc).__name__,
                    failed_stage=as_str(job.current_stage),
                )
            except Exception:
                pass
            db.commit()


def _state(job: MediaScanJob) -> dict:
    return dict(job.stage_state_json or {})


def _record_stage(db: Session, job: MediaScanJob, stage: MediaScanStage, output: dict) -> None:
    state = _state(job)
    state[stage.value] = {"done": True, **output}
    job.stage_state_json = state
    job.current_stage = stage
    job.progress_percent = _STAGE_PROGRESS.get(stage, job.progress_percent)
    db.add(job)
    db.commit()


def _is_done(job: MediaScanJob, stage: MediaScanStage) -> bool:
    return bool(_state(job).get(stage.value, {}).get("done"))


class _BudgetExceeded(RuntimeError):
    """Raised when a scan's projected cost would exceed the per-scan ceiling."""


def _accrue_cost(db: Session, job: MediaScanJob, amount_usd: float) -> None:
    job.cost_estimate_usd = round((job.cost_estimate_usd or 0.0) + amount_usd, 4)
    db.add(job)


def _execute(db: Session, job: MediaScanJob, events: MediaScanEventLogger) -> None:
    settings = get_settings()
    account = db.get(Account, job.account_id)
    if account is None:
        raise RuntimeError(f"account_not_found:{job.account_id}")

    icp = load_default_icp(db)
    live = job.mode == MediaScanMode.live
    max_sources = settings.media_scan_max_sources

    log.info(
        "media_scan_runner.start",
        job_id=job.id,
        account=account.name,
        mode=as_str(job.mode),
        resume_from=as_str(job.current_stage),
    )

    # ---------- Stage: discover_sources ----------
    if not _is_done(job, MediaScanStage.discover_sources):
        events.stage_started(MediaScanStage.discover_sources)
        sources: list[MediaSource] = []
        if live:
            sources = asyncio.run(
                discover_sources_live(db, job=job, account=account, icp=icp, events=events)
            )
            if not sources:
                events.warning("live discovery empty; using mock fixtures")
                sources = discover_sources_mock(db, job=job, account=account, events=events)
        else:
            sources = discover_sources_mock(db, job=job, account=account, events=events)
        db.commit()
        events.stage_completed(MediaScanStage.discover_sources, discovered=len(sources))
        _record_stage(db, job, MediaScanStage.discover_sources, {"discovered": len(sources)})
    else:
        events.stage_skipped(MediaScanStage.discover_sources, reason="already_done")

    # ---------- Stage: rank_sources ----------
    if not _is_done(job, MediaScanStage.rank_sources):
        events.stage_started(MediaScanStage.rank_sources)
        all_sources = _job_sources(db, job)
        selected = asyncio.run(
            rank_sources(
                db,
                account=account,
                icp=icp,
                sources=all_sources,
                events=events,
                max_select=max_sources,
            )
        )
        db.commit()
        events.stage_completed(MediaScanStage.rank_sources, selected=len(selected))
        _accrue_cost(db, job, estimate_llm_calls_usd(1, settings=settings))
        db.commit()
        _record_stage(
            db,
            job,
            MediaScanStage.rank_sources,
            {"selected_ids": [s.id for s in selected]},
        )
    else:
        events.stage_skipped(MediaScanStage.rank_sources, reason="already_done")

    selected_ids = _state(job).get(MediaScanStage.rank_sources.value, {}).get("selected_ids", [])
    selected_sources = [db.get(MediaSource, sid) for sid in selected_ids]
    selected_sources = [s for s in selected_sources if s is not None]

    # ---------- Stage: resolve_media + hash_media (CAS) ----------
    if not _is_done(job, MediaScanStage.hash_media):
        events.stage_started(MediaScanStage.resolve_media)
        cache_hits = 0
        for src in selected_sources:
            resolved = resolve_and_hash(db, source=src, events=events)
            if resolved.cache_hit:
                cache_hits += 1
            src.status = MediaSourceStatus.resolved
            db.add(src)
        db.commit()
        events.stage_completed(MediaScanStage.resolve_media, resolved=len(selected_sources))
        _record_stage(db, job, MediaScanStage.resolve_media, {"resolved": len(selected_sources)})
        events.stage_started(MediaScanStage.hash_media)
        events.stage_completed(MediaScanStage.hash_media, cache_hits=cache_hits)
        _record_stage(db, job, MediaScanStage.hash_media, {"cache_hits": cache_hits})
    else:
        events.stage_skipped(MediaScanStage.hash_media, reason="already_done")

    # ---------- Stage: transcribe ----------
    if not _is_done(job, MediaScanStage.transcribe):
        events.stage_started(MediaScanStage.transcribe)

        # Budget gate: project ASR cost for sources that still need
        # transcription (cache hits cost nothing) plus one extraction call per
        # source, and hard-stop before spending if it would exceed the ceiling.
        projected = job.cost_estimate_usd or 0.0
        to_transcribe: list[MediaSource] = []
        for src in selected_sources:
            if src.media_asset_id is None:
                continue
            asset = db.get(MediaAsset, src.media_asset_id)
            if asset is None:
                continue
            needs_asr = asset.transcript_id is None
            if needs_asr:
                to_transcribe.append(src)
                projected += estimate_transcription_usd(
                    src.duration_seconds, settings=settings
                )
            projected += estimate_llm_calls_usd(1, settings=settings)

        if would_exceed_budget(projected, settings=settings):
            events.error(
                "projected cost exceeds per-scan budget; stopping before "
                "transcription (resumable after raising the budget)",
                projected_usd=round(projected, 4),
                budget_usd=settings.media_scan_budget_usd,
            )
            db.commit()
            raise _BudgetExceeded(
                f"projected ${projected:.2f} exceeds budget "
                f"${settings.media_scan_budget_usd:.2f}"
            )

        transcript_map: dict[str, str] = {}  # source_id -> transcript_id
        for src in selected_sources:
            if src.media_asset_id is None:
                continue
            asset = db.get(MediaAsset, src.media_asset_id)
            if asset is None:
                continue
            needs_asr = asset.transcript_id is None
            result = transcribe_source(
                db, source=src, asset=asset, events=events, live=live
            )
            if result is not None:
                transcript_map[src.id] = result.transcript.id
                src.status = MediaSourceStatus.transcribed
                db.add(src)
                # Accrue ASR cost only when we actually transcribed (not reused).
                if needs_asr and not result.reused:
                    _accrue_cost(
                        db,
                        job,
                        estimate_transcription_usd(src.duration_seconds, settings=settings),
                    )
        db.commit()
        events.stage_completed(MediaScanStage.transcribe, transcribed=len(transcript_map))
        _record_stage(db, job, MediaScanStage.transcribe, {"transcript_map": transcript_map})
    else:
        events.stage_skipped(MediaScanStage.transcribe, reason="already_done")

    transcript_map = _state(job).get(MediaScanStage.transcribe.value, {}).get("transcript_map", {})

    # ---------- Stage: scrub_transcript ----------
    if not _is_done(job, MediaScanStage.scrub_transcript):
        events.stage_started(MediaScanStage.scrub_transcript)
        scrubbed_count = 0
        sensitive_count = 0
        for transcript_id in set(transcript_map.values()):
            transcript = db.get(Transcript, transcript_id)
            if transcript is None or transcript.scrubbed_text is not None:
                continue
            segments, findings, sensitive = scrub_segments(transcript.segments_json or [])
            from app.services.pii_scrubber import scrub_text

            raw_scrub = scrub_text(transcript.raw_text)
            transcript.scrubbed_text = raw_scrub.scrubbed_text
            transcript.segments_json = segments
            transcript.pii_findings_json = findings
            transcript.pii_status = (
                PrivacyStatus.sensitive_blocked
                if sensitive
                else (PrivacyStatus.scrubbed if findings else PrivacyStatus.clean)
            )
            if not settings.media_transcript_retention_raw:
                transcript.raw_text = None  # drop raw unless retention enabled
            db.add(transcript)
            scrubbed_count += 1
            if sensitive:
                sensitive_count += 1
            if findings:
                events.pii_redaction(
                    "redacted identifiers from transcript",
                    stage=MediaScanStage.scrub_transcript,
                    findings=findings,
                    transcript_id=transcript.id,
                )
        db.commit()
        events.stage_completed(
            MediaScanStage.scrub_transcript,
            scrubbed=scrubbed_count,
            sensitive_flagged=sensitive_count,
        )
        _record_stage(db, job, MediaScanStage.scrub_transcript, {"scrubbed": scrubbed_count})
    else:
        events.stage_skipped(MediaScanStage.scrub_transcript, reason="already_done")

    # ---------- Stage: extract_signals ----------
    if not _is_done(job, MediaScanStage.extract_signals):
        events.stage_started(MediaScanStage.extract_signals)
        total_signals = 0
        for src in selected_sources:
            transcript_id = transcript_map.get(src.id)
            if not transcript_id:
                continue
            transcript = db.get(Transcript, transcript_id)
            if transcript is None:
                continue
            signals = asyncio.run(
                extract_conversation_signals(
                    db,
                    job_id=job.id,
                    account=account,
                    icp=icp,
                    source=src,
                    transcript=transcript,
                    events=events,
                    live=live,
                )
            )
            if signals:
                src.status = MediaSourceStatus.extracted
                db.add(src)
            total_signals += len(signals)
            _accrue_cost(db, job, estimate_llm_calls_usd(1, settings=settings))
        db.commit()
        events.stage_completed(
            MediaScanStage.extract_signals,
            signals=total_signals,
            cost_estimate_usd=round(job.cost_estimate_usd or 0.0, 4),
        )
        _record_stage(db, job, MediaScanStage.extract_signals, {"signals": total_signals})
    else:
        events.stage_skipped(MediaScanStage.extract_signals, reason="already_done")

    all_signals = _job_signals(db, job)

    # ---------- Stage: write_memory ----------
    if not _is_done(job, MediaScanStage.write_memory):
        events.stage_started(MediaScanStage.write_memory)
        written = write_conversation_memory(
            job_id=job.id, account=account, signals=all_signals, events=events
        )
        db.commit()
        events.stage_completed(MediaScanStage.write_memory, memory_writes=written)
        _record_stage(db, job, MediaScanStage.write_memory, {"memory_writes": written})
    else:
        events.stage_skipped(MediaScanStage.write_memory, reason="already_done")

    # ---------- Stage: score_account ----------
    if not _is_done(job, MediaScanStage.score_account):
        events.stage_started(MediaScanStage.score_account)
        delta = compute_score_delta(db, account=account, signals=all_signals)
        job.score_delta = delta.delta
        db.add(job)
        # Unified snapshot: layer the conversation delta onto the account's
        # latest score so the headline number actually moves.
        from app.services.account_scoring import record_media_snapshot

        record_media_snapshot(
            db,
            account_id=account.id,
            delta=delta.delta,
            new_total=delta.new_total,
            sales_ready=delta.sales_ready,
            origin_id=job.id,
            explanation=delta.explanation,
        )
        db.commit()
        events.stage_completed(
            MediaScanStage.score_account,
            delta=delta.delta,
            new_total=delta.new_total,
            sales_ready=delta.sales_ready,
        )
        _record_stage(
            db,
            job,
            MediaScanStage.score_account,
            {
                "delta": delta.delta,
                "new_total": delta.new_total,
                "previous_total": delta.previous_total,
                "sales_ready": delta.sales_ready,
                "explanation": delta.explanation,
            },
        )
    else:
        events.stage_skipped(MediaScanStage.score_account, reason="already_done")

    score_state = _state(job).get(MediaScanStage.score_account.value, {})

    # ---------- Stage: notify ----------
    if not _is_done(job, MediaScanStage.notify):
        events.stage_started(MediaScanStage.notify)
        signal_count = len(all_signals)
        delta = score_state.get("delta", 0)
        title = f"{account.name}: {signal_count} conversation signal(s) found"
        body_bits = []
        if delta:
            body_bits.append(f"Score moved +{delta} from spoken evidence.")
        top = max(all_signals, key=lambda s: s.confidence, default=None)
        if top is not None:
            body_bits.append(f"Top signal: {top.title}")
        create_notification(
            db,
            notification_type=NotificationType.media_scan_completed,
            title=title,
            body=" ".join(body_bits) or "Media scan complete.",
            account_id=account.id,
            link=f"/accounts/{account.id}",
            metadata={"media_scan_job_id": job.id, "signal_count": signal_count},
        )
        if score_state.get("sales_ready"):
            create_notification(
                db,
                notification_type=NotificationType.score_change,
                title=f"{account.name} is now sales-ready",
                body="Conversation signals pushed this account over the sales-ready threshold.",
                account_id=account.id,
                link=f"/accounts/{account.id}",
                metadata={"media_scan_job_id": job.id},
            )
        db.commit()
        events.notification("notifications created", stage=MediaScanStage.notify)
        events.stage_completed(MediaScanStage.notify)
        _record_stage(db, job, MediaScanStage.notify, {"notified": True})
    else:
        events.stage_skipped(MediaScanStage.notify, reason="already_done")

    # ---------- Done ----------
    job.status = MediaScanStage.completed
    job.current_stage = MediaScanStage.completed
    job.progress_percent = 100
    job.completed_at = _now()
    db.add(job)
    events.info("media scan completed")
    db.commit()


def _job_sources(db: Session, job: MediaScanJob) -> list[MediaSource]:
    return list(
        db.scalars(
            select(MediaSource).where(MediaSource.media_scan_job_id == job.id)
        ).all()
    )


def _job_signals(db: Session, job: MediaScanJob) -> list[ConversationSignal]:
    return list(
        db.scalars(
            select(ConversationSignal).where(
                ConversationSignal.media_scan_job_id == job.id
            )
        ).all()
    )
