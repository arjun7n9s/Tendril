"""Accounts endpoints (Phase 1 + Phase 2 enrichment)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.models.brief import Brief
from app.models.enums import AccountStatus
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal
from app.schemas.account import AccountListResponse, AccountRead
from app.schemas.brief import BriefRead, ScoreRead
from app.schemas.scan import ScanRead
from app.schemas.signal import SignalRead

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=AccountListResponse)
def list_accounts(
    status: AccountStatus | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> AccountListResponse:
    stmt = select(Account)
    count_stmt = select(func.count()).select_from(Account)

    if status is not None:
        stmt = stmt.where(Account.status == status)
        count_stmt = count_stmt.where(Account.status == status)

    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(func.lower(Account.name).like(like), func.lower(Account.domain).like(like))
        )
        count_stmt = count_stmt.where(
            or_(func.lower(Account.name).like(like), func.lower(Account.domain).like(like))
        )

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Account.name).limit(limit).offset(offset)).all()
    return AccountListResponse(
        items=[AccountRead.model_validate(a) for a in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{account_id}")
def get_account(account_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")

    latest_scan = db.scalar(
        select(Scan).where(Scan.account_id == account_id).order_by(Scan.created_at.desc())
    )
    latest_score = db.scalar(
        select(Score).where(Score.account_id == account_id).order_by(Score.created_at.desc())
    )
    latest_brief = db.scalar(
        select(Brief).where(Brief.account_id == account_id).order_by(Brief.created_at.desc())
    )
    recent_signals = db.scalars(
        select(Signal)
        .where(Signal.account_id == account_id)
        .order_by(Signal.created_at.desc())
        .limit(10)
    ).all()

    return {
        "account": AccountRead.model_validate(account).model_dump(mode="json"),
        "latest_scan": (
            ScanRead(
                id=latest_scan.id,
                account_id=latest_scan.account_id,
                scan_type=latest_scan.scan_type,
                status=latest_scan.status,
                mode=latest_scan.mode,
                progress_percent=latest_scan.progress_percent,
                error_message=latest_scan.error_message,
                started_at=latest_scan.started_at,
                completed_at=latest_scan.completed_at,
                created_at=latest_scan.created_at,
                updated_at=latest_scan.updated_at,
            ).model_dump(mode="json")
            if latest_scan
            else None
        ),
        "latest_score": (
            ScoreRead.model_validate(latest_score).model_dump(mode="json")
            if latest_score
            else None
        ),
        "latest_brief": (
            BriefRead.model_validate(latest_brief).model_dump(mode="json")
            if latest_brief
            else None
        ),
        "recent_signals": [
            SignalRead.model_validate(s).model_dump(mode="json") for s in recent_signals
        ],
    }
