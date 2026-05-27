"""Scan endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.jobs.scan_runner import run_scan
from app.models.account import Account
from app.models.enums import (
    FetchStatus,
    ScanEventType,
    ScanMode,
    ScanStatus,
)
from app.models.evidence import EvidenceDocument
from app.models.scan import Scan
from app.models.scan_event import ScanEvent
from app.models.signal import Signal
from app.models.source import Source
from app.schemas.scan import (
    ScanCounts,
    ScanCreateRequest,
    ScanCreateResponse,
    ScanEventList,
    ScanEventRead,
    ScanRead,
)
from app.schemas.signal import EvidenceRead, SourceRead

router = APIRouter(tags=["scans"])

_NON_TERMINAL = {
    ScanStatus.queued,
    ScanStatus.discovering,
    ScanStatus.scraping,
    ScanStatus.extracting,
    ScanStatus.graphing,
    ScanStatus.scoring,
    ScanStatus.briefing,
}


def _enforce_phase_timeout(db: Session, scan: Scan, settings: Settings) -> None:
    """Refinement #15 watchdog: mark stale scans as failed."""
    if scan.status not in _NON_TERMINAL:
        return
    started = scan.started_at or scan.updated_at
    if started is None:
        return
    age = (datetime.now(UTC) - started).total_seconds()
    if age <= settings.signalgraph_scan_phase_timeout_seconds:
        return
    scan.status = ScanStatus.failed
    scan.error_message = f"phase_timeout:{scan.status.value}"
    scan.completed_at = datetime.now(UTC)
    scan.progress_percent = 100
    db.add(scan)
    db.commit()


def _compute_counts(db: Session, scan_id: str) -> ScanCounts:
    discovered = db.scalar(select(func.count()).select_from(Source).where(Source.scan_id == scan_id)) or 0
    selected = db.scalar(
        select(func.count()).select_from(Source).where(
            Source.scan_id == scan_id, Source.selected_for_scrape.is_(True)
        )
    ) or 0
    fetched = db.scalar(
        select(func.count()).select_from(EvidenceDocument).where(
            EvidenceDocument.scan_id == scan_id,
            EvidenceDocument.fetch_status == FetchStatus.success,
        )
    ) or 0
    failed = db.scalar(
        select(func.count()).select_from(EvidenceDocument).where(
            EvidenceDocument.scan_id == scan_id,
            EvidenceDocument.fetch_status == FetchStatus.failed,
        )
    ) or 0
    signals = db.scalar(select(func.count()).select_from(Signal).where(Signal.scan_id == scan_id)) or 0

    bd_calls = db.scalar(
        select(func.count()).select_from(ScanEvent).where(
            ScanEvent.scan_id == scan_id,
            ScanEvent.event_type.in_(
                [ScanEventType.bright_data_call, ScanEventType.bright_data_call_replayed]
            ),
        )
    ) or 0
    aiml_calls = db.scalar(
        select(func.count()).select_from(ScanEvent).where(
            ScanEvent.scan_id == scan_id,
            ScanEvent.event_type.in_(
                [ScanEventType.aiml_call, ScanEventType.aiml_call_replayed]
            ),
        )
    ) or 0
    memory_writes = db.scalar(
        select(func.count()).select_from(ScanEvent).where(
            ScanEvent.scan_id == scan_id,
            ScanEvent.event_type.in_(
                [ScanEventType.memory_write, ScanEventType.memory_write_replayed]
            ),
        )
    ) or 0
    return ScanCounts(
        discovered=discovered,
        selected=selected,
        fetched=fetched,
        failed=failed,
        signals=signals,
        bright_data_calls=bd_calls,
        aiml_calls=aiml_calls,
        memory_writes=memory_writes,
    )


def _scan_to_read(db: Session, scan: Scan) -> ScanRead:
    return ScanRead(
        id=scan.id,
        account_id=scan.account_id,
        scan_type=scan.scan_type,
        status=scan.status,
        mode=scan.mode,
        progress_percent=scan.progress_percent,
        error_message=scan.error_message,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        counts=_compute_counts(db, scan.id),
    )


@router.post(
    "/api/v1/accounts/{account_id}/scans",
    response_model=ScanCreateResponse,
    status_code=201,
)
def create_scan(
    account_id: str,
    body: ScanCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ScanCreateResponse:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")

    # Force-refresh: cancel any in-flight scan for this account.
    if body.force_refresh:
        cutoff = datetime.now(UTC) - timedelta(seconds=settings.signalgraph_scan_phase_timeout_seconds * 4)
        in_flight = db.scalars(
            select(Scan).where(
                Scan.account_id == account_id,
                Scan.status.in_(list(_NON_TERMINAL)),
                Scan.created_at >= cutoff,
            )
        ).all()
        for s in in_flight:
            s.status = ScanStatus.failed
            s.error_message = "superseded_by_force_refresh"
            s.completed_at = datetime.now(UTC)
            s.progress_percent = 100
            db.add(s)
        db.commit()

    # Mode coercion: live without configured Bright Data falls back to mock.
    requested_mode = body.mode
    if requested_mode == ScanMode.live and not settings.bright_data_rest_configured():
        requested_mode = ScanMode.mock

    scan = Scan(
        account_id=account_id,
        scan_type=body.scan_type,
        status=ScanStatus.queued,
        mode=requested_mode,
        progress_percent=0,
    )
    db.add(scan)
    db.commit()

    background_tasks.add_task(run_scan, scan.id)

    return ScanCreateResponse(scan_id=scan.id, status=scan.status, mode=scan.mode)


@router.get("/api/v1/scans/{scan_id}", response_model=ScanRead)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ScanRead:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan_not_found")
    _enforce_phase_timeout(db, scan, settings)
    return _scan_to_read(db, scan)


@router.get("/api/v1/scans/{scan_id}/events", response_model=ScanEventList)
def get_scan_events(
    scan_id: str,
    after_sequence: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
) -> ScanEventList:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan_not_found")
    rows = db.scalars(
        select(ScanEvent)
        .where(ScanEvent.scan_id == scan_id, ScanEvent.sequence > after_sequence)
        .order_by(ScanEvent.sequence)
        .limit(limit)
    ).all()
    total = db.scalar(
        select(func.count()).select_from(ScanEvent).where(ScanEvent.scan_id == scan_id)
    ) or 0
    return ScanEventList(
        items=[ScanEventRead.model_validate(e) for e in rows],
        total=total,
    )


@router.get("/api/v1/scans/{scan_id}/sources", response_model=list[SourceRead])
def get_scan_sources(scan_id: str, db: Session = Depends(get_db)) -> list[SourceRead]:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan_not_found")
    rows = db.scalars(
        select(Source).where(Source.scan_id == scan_id).order_by(Source.rank)
    ).all()
    return [SourceRead.model_validate(r) for r in rows]


@router.get("/api/v1/scans/{scan_id}/evidence", response_model=list[EvidenceRead])
def get_scan_evidence(scan_id: str, db: Session = Depends(get_db)) -> list[EvidenceRead]:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan_not_found")
    rows = db.scalars(
        select(EvidenceDocument).where(EvidenceDocument.scan_id == scan_id)
    ).all()
    return [EvidenceRead.model_validate(r) for r in rows]
