"""Crash recovery for durable media scans.

The pipeline persists per-stage progress, but a process that dies mid-stage
leaves a job stuck in a non-terminal state with nothing to resume it. This
reclaimer closes that gap: it finds non-terminal jobs whose liveness heartbeat
has gone stale (i.e. no running worker is touching them) and re-enqueues them.
Because every stage is idempotent and resumes from `stage_state_json`, and
because a submitted Speechmatics job id is persisted before waiting, re-enqueue
is safe and never double-bills.

Run at startup (to reclaim anything orphaned by the last shutdown/crash) and
periodically from the watchtower loop.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.logging_setup import get_logger
from app.models.enums import MediaScanStage
from app.models.media_scan_job import MediaScanJob

log = get_logger("media_reclaimer")

_TERMINAL = (MediaScanStage.completed, MediaScanStage.failed)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def find_stalled_jobs(
    db: Session, *, now: datetime | None = None, settings: Settings | None = None
) -> list[MediaScanJob]:
    """Non-terminal jobs whose heartbeat is older than the stall threshold.

    The threshold is the stage timeout — a healthy worker refreshes the
    heartbeat at every stage boundary, so exceeding a full stage timeout
    without a heartbeat means the worker is gone.
    """
    settings = settings or get_settings()
    now = now or datetime.now(UTC)
    threshold = now - timedelta(seconds=settings.media_scan_phase_timeout_seconds)

    candidates = db.scalars(
        select(MediaScanJob).where(MediaScanJob.status.notin_(_TERMINAL))
    ).all()

    stalled: list[MediaScanJob] = []
    for job in candidates:
        # Use heartbeat if present, else started_at/updated_at as a fallback.
        marker = _aware(job.last_heartbeat_at) or _aware(job.started_at) or _aware(
            job.updated_at
        )
        if marker is None or marker <= threshold:
            stalled.append(job)
    return stalled


def reclaim_stalled_jobs(db: Session, *, enqueue, settings: Settings | None = None) -> list[str]:
    """Re-enqueue stalled jobs. Returns the reclaimed job ids.

    `enqueue` is a callable `(job_id) -> None` so the caller controls how the
    durable runner is scheduled (thread pool, background task, etc.).
    """
    settings = settings or get_settings()
    stalled = find_stalled_jobs(db, settings=settings)
    reclaimed: list[str] = []
    for job in stalled:
        # Touch the heartbeat so we don't reclaim the same job repeatedly while
        # the re-enqueued worker spins up.
        job.last_heartbeat_at = datetime.now(UTC)
        db.add(job)
        reclaimed.append(job.id)
    if reclaimed:
        db.commit()
        for job_id in reclaimed:
            try:
                enqueue(job_id)
            except Exception as exc:
                log.warning("media_reclaimer.enqueue_failed", job_id=job_id, error=str(exc))
        log.info("media_reclaimer.reclaimed", count=len(reclaimed))
    return reclaimed
