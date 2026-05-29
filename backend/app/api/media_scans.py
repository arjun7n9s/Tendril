"""Media scan endpoints (multimodal signal engine)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.jobs.media_scan_runner import run_media_scan
from app.models.account import Account
from app.models.conversation_signal import ConversationSignal
from app.models.enums import (
    MediaScanMode,
    MediaScanStage,
    MediaSourceStatus,
    TranscriptionStatus,
)
from app.models.media_asset import MediaAsset
from app.models.media_scan_event import MediaScanEvent
from app.models.media_scan_job import MediaScanJob
from app.models.media_source import MediaSource
from app.models.transcript import Transcript
from app.schemas.media import (
    ConversationSignalList,
    ConversationSignalRead,
    MediaScanCounts,
    MediaScanCreateRequest,
    MediaScanCreateResponse,
    MediaScanEventList,
    MediaScanEventRead,
    MediaScanRead,
    MediaSourceRead,
    TranscriptRead,
)

router = APIRouter(tags=["media-scans"])

_NON_TERMINAL = {
    MediaScanStage.queued,
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
}


def _compute_counts(db: Session, job_id: str) -> MediaScanCounts:
    discovered = (
        db.scalar(
            select(func.count()).select_from(MediaSource).where(
                MediaSource.media_scan_job_id == job_id
            )
        )
        or 0
    )
    selected = (
        db.scalar(
            select(func.count()).select_from(MediaSource).where(
                MediaSource.media_scan_job_id == job_id,
                MediaSource.status.in_(
                    [
                        MediaSourceStatus.selected,
                        MediaSourceStatus.resolved,
                        MediaSourceStatus.transcribed,
                        MediaSourceStatus.extracted,
                    ]
                ),
            )
        )
        or 0
    )
    signals = (
        db.scalar(
            select(func.count()).select_from(ConversationSignal).where(
                ConversationSignal.media_scan_job_id == job_id
            )
        )
        or 0
    )
    # Transcripts + cache hits are derived from assets linked to this job's sources.
    asset_ids = [
        a
        for (a,) in db.execute(
            select(MediaSource.media_asset_id).where(
                MediaSource.media_scan_job_id == job_id,
                MediaSource.media_asset_id.is_not(None),
            )
        ).all()
    ]
    transcripts = 0
    cache_hits = 0
    if asset_ids:
        transcripts = (
            db.scalar(
                select(func.count(func.distinct(Transcript.id))).where(
                    Transcript.media_asset_id.in_(asset_ids)
                )
            )
            or 0
        )
        cache_hits = (
            db.scalar(
                select(func.count()).select_from(MediaAsset).where(
                    MediaAsset.id.in_(asset_ids),
                    MediaAsset.transcription_status == TranscriptionStatus.reused,
                )
            )
            or 0
        )
    memory_writes = (
        db.scalar(
            select(func.count()).select_from(MediaScanEvent).where(
                MediaScanEvent.media_scan_job_id == job_id,
                MediaScanEvent.event_type == "memory_write",
            )
        )
        or 0
    )
    return MediaScanCounts(
        sources_discovered=discovered,
        sources_selected=selected,
        transcripts=transcripts,
        cache_hits=cache_hits,
        conversation_signals=signals,
        memory_writes=memory_writes,
    )


def _enforce_timeout(db: Session, job: MediaScanJob, settings: Settings) -> None:
    if job.status not in _NON_TERMINAL:
        return
    started = job.started_at or job.updated_at
    if started is None:
        return
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    age = (datetime.now(UTC) - started).total_seconds()
    if age <= settings.media_scan_phase_timeout_seconds:
        return
    job.status = MediaScanStage.failed
    job.last_error = f"stage_timeout:{job.current_stage.value}"
    job.completed_at = datetime.now(UTC)
    db.add(job)
    db.commit()


def _job_to_read(db: Session, job: MediaScanJob) -> MediaScanRead:
    return MediaScanRead(
        id=job.id,
        account_id=job.account_id,
        mode=job.mode,
        status=job.status,
        current_stage=job.current_stage,
        progress_percent=job.progress_percent,
        attempt_count=job.attempt_count,
        last_error=job.last_error,
        score_delta=job.score_delta,
        cost_estimate_usd=job.cost_estimate_usd or 0.0,
        stage_state_json=job.stage_state_json,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
        counts=_compute_counts(db, job.id),
    )


@router.post(
    "/api/v1/accounts/{account_id}/media-scans",
    response_model=MediaScanCreateResponse,
    status_code=201,
)
def create_media_scan(
    account_id: str,
    body: MediaScanCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MediaScanCreateResponse:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")

    if body.force_refresh:
        cutoff = datetime.now(UTC) - timedelta(
            seconds=settings.media_scan_phase_timeout_seconds * 4
        )
        in_flight = db.scalars(
            select(MediaScanJob).where(
                MediaScanJob.account_id == account_id,
                MediaScanJob.status.in_(list(_NON_TERMINAL)),
                MediaScanJob.created_at >= cutoff,
            )
        ).all()
        for j in in_flight:
            j.status = MediaScanStage.failed
            j.last_error = "superseded_by_force_refresh"
            j.completed_at = datetime.now(UTC)
            db.add(j)
        db.commit()

    # Mode coercion: live needs SIGNALGRAPH_MOCK_MODE=false. Provider gaps are
    # tolerated at runtime (the pipeline degrades to fixtures/heuristics).
    mode = body.mode
    if mode == MediaScanMode.live and settings.signalgraph_mock_mode:
        mode = MediaScanMode.mock

    job = MediaScanJob(
        account_id=account_id,
        mode=mode,
        status=MediaScanStage.queued,
        current_stage=MediaScanStage.queued,
        stage_state_json={},
        progress_percent=0,
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(run_media_scan, job.id)
    return MediaScanCreateResponse(media_scan_id=job.id, status=job.status, mode=job.mode)


@router.get("/api/v1/media-scans/{scan_id}", response_model=MediaScanRead)
def get_media_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MediaScanRead:
    job = db.get(MediaScanJob, scan_id)
    if job is None:
        raise HTTPException(status_code=404, detail="media_scan_not_found")
    _enforce_timeout(db, job, settings)
    return _job_to_read(db, job)


@router.get("/api/v1/media-scans/{scan_id}/events", response_model=MediaScanEventList)
def get_media_scan_events(
    scan_id: str,
    after_sequence: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
) -> MediaScanEventList:
    job = db.get(MediaScanJob, scan_id)
    if job is None:
        raise HTTPException(status_code=404, detail="media_scan_not_found")
    rows = db.scalars(
        select(MediaScanEvent)
        .where(
            MediaScanEvent.media_scan_job_id == scan_id,
            MediaScanEvent.sequence > after_sequence,
        )
        .order_by(MediaScanEvent.sequence)
        .limit(limit)
    ).all()
    total = (
        db.scalar(
            select(func.count()).select_from(MediaScanEvent).where(
                MediaScanEvent.media_scan_job_id == scan_id
            )
        )
        or 0
    )
    return MediaScanEventList(
        items=[MediaScanEventRead.model_validate(e) for e in rows],
        total=total,
    )


@router.post("/api/v1/media-scans/{scan_id}/resume", response_model=MediaScanCreateResponse)
def resume_media_scan(
    scan_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> MediaScanCreateResponse:
    """Resume a failed or stalled scan from its last incomplete stage."""
    job = db.get(MediaScanJob, scan_id)
    if job is None:
        raise HTTPException(status_code=404, detail="media_scan_not_found")
    if job.status == MediaScanStage.completed:
        raise HTTPException(status_code=409, detail="media_scan_already_completed")
    # Reset only the terminal failure flag; stage_state_json is preserved so the
    # runner resumes idempotently from where it left off.
    job.status = MediaScanStage.queued
    job.last_error = None
    db.add(job)
    db.commit()
    background_tasks.add_task(run_media_scan, job.id)
    return MediaScanCreateResponse(media_scan_id=job.id, status=job.status, mode=job.mode)


@router.get(
    "/api/v1/accounts/{account_id}/media-sources",
    response_model=list[MediaSourceRead],
)
def list_account_media_sources(
    account_id: str,
    latest_only: bool = True,
    db: Session = Depends(get_db),
) -> list[MediaSourceRead]:
    if latest_only:
        latest_job = db.scalar(
            select(MediaScanJob)
            .where(MediaScanJob.account_id == account_id)
            .order_by(MediaScanJob.created_at.desc())
        )
        if latest_job is None:
            return []
        rows = db.scalars(
            select(MediaSource)
            .where(MediaSource.media_scan_job_id == latest_job.id)
            .order_by(MediaSource.rank_score.desc().nullslast())
        ).all()
    else:
        rows = db.scalars(
            select(MediaSource)
            .where(MediaSource.account_id == account_id)
            .order_by(MediaSource.created_at.desc())
        ).all()
    return [MediaSourceRead.model_validate(r) for r in rows]


@router.get(
    "/api/v1/accounts/{account_id}/conversation-signals",
    response_model=ConversationSignalList,
)
def list_account_conversation_signals(
    account_id: str,
    latest_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> ConversationSignalList:
    stmt = select(ConversationSignal).where(ConversationSignal.account_id == account_id)
    count_stmt = (
        select(func.count())
        .select_from(ConversationSignal)
        .where(ConversationSignal.account_id == account_id)
    )
    if latest_only:
        latest_job = db.scalar(
            select(MediaScanJob)
            .where(MediaScanJob.account_id == account_id)
            .order_by(MediaScanJob.created_at.desc())
        )
        if latest_job is None:
            return ConversationSignalList(items=[], total=0)
        stmt = stmt.where(ConversationSignal.media_scan_job_id == latest_job.id)
        count_stmt = count_stmt.where(
            ConversationSignal.media_scan_job_id == latest_job.id
        )
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(
            ConversationSignal.confidence.desc(),
            ConversationSignal.created_at.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return ConversationSignalList(
        items=[ConversationSignalRead.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/api/v1/transcripts/{transcript_id}", response_model=TranscriptRead)
def get_transcript(transcript_id: str, db: Session = Depends(get_db)) -> TranscriptRead:
    transcript = db.get(Transcript, transcript_id)
    if transcript is None:
        raise HTTPException(status_code=404, detail="transcript_not_found")
    return TranscriptRead.model_validate(transcript)
