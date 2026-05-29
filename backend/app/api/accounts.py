"""Accounts endpoints (Phase 1 + Phase 2 enrichment)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
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


def _latest_score_subquery():
    """Subquery returning the latest score row per account."""
    inner = (
        select(
            Score.account_id.label("account_id"),
            func.max(Score.created_at).label("max_created"),
        )
        .group_by(Score.account_id)
        .subquery()
    )
    return inner


@router.get("", response_model=AccountListResponse)
def list_accounts(
    status: AccountStatus | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    sales_ready: bool | None = Query(
        default=None,
        description="Filter by latest score's sales_ready flag",
    ),
    near_miss: bool | None = Query(
        default=None,
        description=(
            "When true, return accounts whose latest score is 55-69 and "
            "not sales_ready. When false, return accounts that are sales_ready "
            "or scored below 55."
        ),
    ),
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

    if sales_ready is not None or near_miss is not None:
        latest = _latest_score_subquery()
        join_condition = and_(
            Score.account_id == latest.c.account_id,
            Score.created_at == latest.c.max_created,
        )
        stmt = stmt.join(Score, Score.account_id == Account.id).join(
            latest, join_condition
        )
        count_stmt = count_stmt.join(Score, Score.account_id == Account.id).join(
            latest, join_condition
        )
        if sales_ready is not None:
            stmt = stmt.where(Score.sales_ready.is_(sales_ready))
            count_stmt = count_stmt.where(Score.sales_ready.is_(sales_ready))
        if near_miss is True:
            stmt = stmt.where(Score.sales_ready.is_(False)).where(
                Score.total_score >= 55, Score.total_score <= 69
            )
            count_stmt = count_stmt.where(Score.sales_ready.is_(False)).where(
                Score.total_score >= 55, Score.total_score <= 69
            )
        elif near_miss is False:
            stmt = stmt.where(
                or_(Score.sales_ready.is_(True), Score.total_score < 55)
            )
            count_stmt = count_stmt.where(
                or_(Score.sales_ready.is_(True), Score.total_score < 55)
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

    # Unified, modality-aware headline score (web + media). Falls back to the
    # web score below when no snapshot exists yet.
    from app.models.account_score_snapshot import AccountScoreSnapshot

    latest_snapshot = db.scalar(
        select(AccountScoreSnapshot)
        .where(AccountScoreSnapshot.account_id == account_id)
        .order_by(AccountScoreSnapshot.created_at.desc())
    )

    # Phase 7: scope score / brief / signals to the latest scan when one
    # exists, so repeated runs in a single demo DB don't pollute the
    # account view with stale rows. Fall back to the account-level
    # latest values if no scan exists yet.
    if latest_scan is not None:
        latest_score = db.scalar(
            select(Score)
            .where(Score.scan_id == latest_scan.id)
            .order_by(Score.created_at.desc())
        )
        latest_brief = db.scalar(
            select(Brief)
            .where(Brief.scan_id == latest_scan.id)
            .order_by(Brief.created_at.desc())
        )
        recent_signals = db.scalars(
            select(Signal)
            .where(Signal.scan_id == latest_scan.id)
            .order_by(Signal.confidence.desc(), Signal.created_at.desc())
            .limit(10)
        ).all()
    else:
        latest_score = db.scalar(
            select(Score)
            .where(Score.account_id == account_id)
            .order_by(Score.created_at.desc())
        )
        latest_brief = db.scalar(
            select(Brief)
            .where(Brief.account_id == account_id)
            .order_by(Brief.created_at.desc())
        )
        recent_signals = []

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
        "latest_score_snapshot": (
            {
                "id": latest_snapshot.id,
                "account_id": latest_snapshot.account_id,
                "fit_score": latest_snapshot.fit_score,
                "timing_score": latest_snapshot.timing_score,
                "relationship_score": latest_snapshot.relationship_score,
                "evidence_score": latest_snapshot.evidence_score,
                "total_score": latest_snapshot.total_score,
                "sales_ready": latest_snapshot.sales_ready,
                "source": latest_snapshot.source,
                "conversation_delta": latest_snapshot.conversation_delta,
                "reasoning_json": latest_snapshot.reasoning_json,
                "created_at": latest_snapshot.created_at.isoformat()
                if latest_snapshot.created_at
                else None,
            }
            if latest_snapshot
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
