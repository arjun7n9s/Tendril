"""Signals endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.enums import SignalType
from app.models.score import Score
from app.models.signal import Signal
from app.schemas.signal import SignalList, SignalRead

router = APIRouter(tags=["signals"])


def _signal_query(
    *,
    account_id: str | None = None,
    scan_id: str | None = None,
    signal_type: SignalType | None = None,
    min_confidence: float | None = None,
    sales_ready: bool | None = None,
):
    stmt = select(Signal)
    count_stmt = select(func.count()).select_from(Signal)
    where_clauses = []
    if account_id:
        where_clauses.append(Signal.account_id == account_id)
    if scan_id:
        where_clauses.append(Signal.scan_id == scan_id)
    if signal_type:
        where_clauses.append(Signal.signal_type == signal_type)
    if min_confidence is not None:
        where_clauses.append(Signal.confidence >= min_confidence)
    if sales_ready is not None:
        # Join with the latest score row per scan to enforce sales_ready filter.
        sales_ready_scan_ids = select(Score.scan_id).where(Score.sales_ready.is_(sales_ready))
        where_clauses.append(Signal.scan_id.in_(sales_ready_scan_ids))
    if where_clauses:
        stmt = stmt.where(and_(*where_clauses))
        count_stmt = count_stmt.where(and_(*where_clauses))
    return stmt, count_stmt


@router.get("/api/v1/signals", response_model=SignalList)
def list_signals(
    account_id: str | None = None,
    scan_id: str | None = None,
    signal_type: SignalType | None = None,
    min_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
    sales_ready: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SignalList:
    stmt, count_stmt = _signal_query(
        account_id=account_id,
        scan_id=scan_id,
        signal_type=signal_type,
        min_confidence=min_confidence,
        sales_ready=sales_ready,
    )
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(Signal.confidence.desc(), Signal.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return SignalList(
        items=[SignalRead.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/api/v1/accounts/{account_id}/signals", response_model=SignalList)
def list_account_signals(
    account_id: str,
    signal_type: SignalType | None = None,
    min_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SignalList:
    stmt, count_stmt = _signal_query(
        account_id=account_id,
        signal_type=signal_type,
        min_confidence=min_confidence,
    )
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(Signal.confidence.desc(), Signal.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return SignalList(
        items=[SignalRead.model_validate(r) for r in rows],
        total=total,
    )
