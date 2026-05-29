"""Watchtower endpoints: manage account watches and trigger ticks."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.jobs.media_scan_runner import run_media_scan
from app.models.account import Account
from app.models.account_watch import AccountWatch
from app.schemas.watchtower import (
    AccountWatchRead,
    TickResponse,
    WatchListResponse,
    WatchUpsertRequest,
)
from app.services import watchtower as watchtower_service
from app.services.watchtower import WatchUpsert

router = APIRouter(tags=["watchtower"])


@router.get("/api/v1/watchtower/watches", response_model=WatchListResponse)
def list_watches(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> WatchListResponse:
    rows = db.scalars(select(AccountWatch).order_by(AccountWatch.next_due_at.asc())).all()
    total = db.scalar(select(func.count()).select_from(AccountWatch)) or 0
    return WatchListResponse(
        items=[AccountWatchRead.model_validate(r) for r in rows],
        total=total,
        watchtower_enabled=settings.watchtower_enabled,
    )


@router.put(
    "/api/v1/accounts/{account_id}/watch",
    response_model=AccountWatchRead,
)
def upsert_watch(
    account_id: str,
    body: WatchUpsertRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AccountWatchRead:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")
    watch = watchtower_service.upsert_watch(
        db,
        account_id=account_id,
        payload=WatchUpsert(
            enabled=body.enabled,
            mode=body.mode,
            interval_seconds=body.interval_seconds,
        ),
        settings=settings,
    )
    db.commit()
    return AccountWatchRead.model_validate(watch)


@router.get("/api/v1/accounts/{account_id}/watch", response_model=AccountWatchRead | None)
def get_watch(account_id: str, db: Session = Depends(get_db)) -> AccountWatchRead | None:
    watch = db.scalar(select(AccountWatch).where(AccountWatch.account_id == account_id))
    if watch is None:
        return None
    return AccountWatchRead.model_validate(watch)


@router.delete("/api/v1/accounts/{account_id}/watch", status_code=204)
def delete_watch(account_id: str, db: Session = Depends(get_db)) -> None:
    watch = db.scalar(select(AccountWatch).where(AccountWatch.account_id == account_id))
    if watch is not None:
        db.delete(watch)
        db.commit()


@router.post("/api/v1/watchtower/tick", response_model=TickResponse)
def manual_tick(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TickResponse:
    """Run one watchtower cycle on demand (useful for demos/tests).

    Dispatches due scans via FastAPI BackgroundTasks instead of the daemon
    loop's worker threads, so a manual tick works even when the loop is off.
    """
    result = watchtower_service.tick(
        db,
        enqueue=lambda job_id: background_tasks.add_task(run_media_scan, job_id),
        settings=settings,
    )
    return TickResponse(
        enabled=result.enabled,
        considered=result.considered,
        dispatched=result.dispatched,
        job_ids=result.job_ids,
    )
