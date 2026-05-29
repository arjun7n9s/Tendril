"""Autonomous watchtower scheduling.

The watchtower periodically re-scans watched accounts. The scheduling logic
is factored as pure, testable functions; the actual timing loop lives in
`jobs/watchtower_runner.py` and just calls `tick()` on an interval.

Design choices for safety:
- Watching is opt-in per account (`AccountWatch.enabled`).
- The whole subsystem is gated by `WATCHTOWER_ENABLED` (off by default).
- Each tick enqueues at most `batch_size` scans so a backlog can't fan out
  into a credit-burning storm.
- Scheduled scans default to mock mode unless the watch explicitly opts into
  live and the global mock gate is off.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.logging_setup import get_logger
from app.models.account import Account
from app.models.account_watch import AccountWatch
from app.models.enums import MediaScanMode, MediaScanStage
from app.models.media_scan_job import MediaScanJob

log = get_logger("watchtower")


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite drops tzinfo on read; coerce naive timestamps to UTC."""
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


@dataclass
class WatchUpsert:
    enabled: bool = True
    mode: MediaScanMode | None = None
    interval_seconds: int | None = None


def upsert_watch(
    db: Session,
    *,
    account_id: str,
    payload: WatchUpsert,
    settings: Settings | None = None,
) -> AccountWatch:
    """Create or update an account's watch subscription."""
    settings = settings or get_settings()
    watch = db.scalar(select(AccountWatch).where(AccountWatch.account_id == account_id))
    if watch is None:
        watch = AccountWatch(
            account_id=account_id,
            enabled=payload.enabled,
            mode=payload.mode or MediaScanMode(settings.watchtower_default_mode),
            interval_seconds=payload.interval_seconds
            or settings.watchtower_default_interval_seconds,
            next_due_at=_now(),  # eligible on the next tick
        )
        db.add(watch)
    else:
        watch.enabled = payload.enabled
        if payload.mode is not None:
            watch.mode = payload.mode
        if payload.interval_seconds is not None:
            watch.interval_seconds = payload.interval_seconds
        if watch.next_due_at is None:
            watch.next_due_at = _now()
    db.flush()
    return watch


def _has_active_scan(db: Session, account_id: str) -> bool:
    """True if the account already has a non-terminal media scan in flight."""
    terminal = (MediaScanStage.completed, MediaScanStage.failed)
    existing = db.scalar(
        select(MediaScanJob.id)
        .where(
            MediaScanJob.account_id == account_id,
            MediaScanJob.status.notin_(terminal),
        )
        .limit(1)
    )
    return existing is not None


def find_due_watches(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int = 2,
) -> list[AccountWatch]:
    """Return enabled watches whose next_due_at has passed, oldest first."""
    now = now or _now()
    rows = db.scalars(
        select(AccountWatch)
        .where(
            AccountWatch.enabled.is_(True),
            or_(AccountWatch.next_due_at.is_(None), AccountWatch.next_due_at <= now),
        )
        .order_by(AccountWatch.next_due_at.asc().nullsfirst())
    ).all()

    due: list[AccountWatch] = []
    for watch in rows:
        if len(due) >= limit:
            break
        # Skip accounts that already have a scan running so the watchtower
        # never piles scans on top of each other.
        if _has_active_scan(db, watch.account_id):
            continue
        due.append(watch)
    return due


def schedule_next(watch: AccountWatch, *, now: datetime | None = None) -> None:
    """Advance a watch's schedule after it has been dispatched."""
    now = now or _now()
    watch.last_scanned_at = now
    watch.next_due_at = now + timedelta(seconds=max(60, watch.interval_seconds))


@dataclass
class TickResult:
    enabled: bool
    considered: int
    dispatched: int
    job_ids: list[str]


def tick(
    db: Session,
    *,
    enqueue,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> TickResult:
    """Run one watchtower cycle.

    `enqueue` is a callable `(job_id) -> None` that schedules the durable
    runner (e.g. a thread/background task). Injecting it keeps this function
    pure and unit-testable without spinning real background work.
    """
    settings = settings or get_settings()
    now = now or _now()

    if not settings.watchtower_enabled:
        return TickResult(enabled=False, considered=0, dispatched=0, job_ids=[])

    due = find_due_watches(db, now=now, limit=settings.watchtower_batch_size)
    job_ids: list[str] = []

    for watch in due:
        account = db.get(Account, watch.account_id)
        if account is None:
            watch.enabled = False
            watch.last_error = "account_not_found"
            db.add(watch)
            continue

        mode = watch.mode
        if mode == MediaScanMode.live and settings.signalgraph_mock_mode:
            mode = MediaScanMode.mock

        job = MediaScanJob(
            account_id=watch.account_id,
            mode=mode,
            status=MediaScanStage.queued,
            current_stage=MediaScanStage.queued,
            stage_state_json={},
            progress_percent=0,
        )
        db.add(job)
        db.flush()

        watch.last_media_scan_job_id = job.id
        schedule_next(watch, now=now)
        db.add(watch)
        job_ids.append(job.id)

    db.commit()

    # Enqueue outside the DB write so a slow scheduler can't hold the txn.
    for job_id in job_ids:
        try:
            enqueue(job_id)
        except Exception as exc:
            log.warning("watchtower.enqueue_failed", job_id=job_id, error=str(exc))

    if job_ids:
        log.info("watchtower.tick", considered=len(due), dispatched=len(job_ids))

    return TickResult(
        enabled=True,
        considered=len(due),
        dispatched=len(job_ids),
        job_ids=job_ids,
    )
