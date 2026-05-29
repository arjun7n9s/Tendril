"""The "Today" feed — an opinionated, prioritized daily queue.

The product promise is *a daily queue of account changes that are current,
explainable, and safe to act on*. This endpoint delivers exactly that: the
accounts that became most actionable recently, ranked, each with a one-line
why-now and the evidence that moved them.

Ranking inputs (all already computed elsewhere):
- the unified score snapshot total (higher = more actionable),
- whether the most recent movement came from fresh spoken evidence,
- recency of the latest scan/snapshot.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.models.account_score_snapshot import AccountScoreSnapshot
from app.models.brief import Brief
from app.models.conversation_signal import ConversationSignal
from app.models.scan import Scan
from app.schemas.today import TodayFeedItem, TodayFeedResponse

router = APIRouter(tags=["today"])


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


@router.get("/api/v1/today", response_model=TodayFeedResponse)
def get_today_feed(
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(get_db),
) -> TodayFeedResponse:
    now = datetime.now(UTC)

    # Latest snapshot per account (the headline actionability score).
    snapshots = db.scalars(
        select(AccountScoreSnapshot).order_by(AccountScoreSnapshot.created_at.desc())
    ).all()
    latest_by_account: dict[str, AccountScoreSnapshot] = {}
    for snap in snapshots:
        latest_by_account.setdefault(snap.account_id, snap)

    items: list[tuple[float, TodayFeedItem]] = []
    for account_id, snap in latest_by_account.items():
        account = db.get(Account, account_id)
        if account is None:
            continue

        created = _aware(snap.created_at) or now
        age_hours = max(0.0, (now - created).total_seconds() / 3600.0)
        # Recency weight: full credit within a day, decaying over a week.
        recency = max(0.0, 1.0 - age_hours / 168.0)

        spoken = snap.source == "media_scan" and (snap.conversation_delta or 0) > 0

        # Priority: score dominates, fresh spoken movement and recency boost it.
        priority = (
            snap.total_score
            + (15 if spoken else 0)
            + recency * 10
            + (8 if snap.sales_ready else 0)
        )

        why_now = _why_now(db, account_id, snap, spoken)
        reason_tags = _reason_tags(snap, spoken)

        items.append(
            (
                priority,
                TodayFeedItem(
                    account_id=account.id,
                    account_name=account.name,
                    domain=account.domain,
                    total_score=snap.total_score,
                    sales_ready=snap.sales_ready,
                    source=snap.source,
                    conversation_delta=snap.conversation_delta,
                    why_now=why_now,
                    reason_tags=reason_tags,
                    updated_at=created.isoformat(),
                ),
            )
        )

    items.sort(key=lambda x: x[0], reverse=True)
    ranked = [item for _priority, item in items[:limit]]
    return TodayFeedResponse(items=ranked, total=len(items), generated_at=now.isoformat())


def _why_now(
    db: Session, account_id: str, snap: AccountScoreSnapshot, spoken: bool
) -> str:
    # Prefer a fresh spoken signal's narrative when the score moved on audio.
    if spoken:
        sig = db.scalar(
            select(ConversationSignal)
            .where(ConversationSignal.account_id == account_id)
            .order_by(
                ConversationSignal.confidence.desc(),
                ConversationSignal.created_at.desc(),
            )
        )
        if sig is not None:
            return sig.summary or sig.title

    # Otherwise fall back to the latest brief's why-now.
    latest_scan = db.scalar(
        select(Scan).where(Scan.account_id == account_id).order_by(Scan.created_at.desc())
    )
    if latest_scan is not None:
        brief = db.scalar(
            select(Brief)
            .where(Brief.scan_id == latest_scan.id)
            .order_by(Brief.created_at.desc())
        )
        if brief is not None and brief.why_now:
            return brief.why_now

    if snap.sales_ready:
        return "Crossed the sales-ready threshold."
    return "Recent activity raised this account's actionability."


def _reason_tags(snap: AccountScoreSnapshot, spoken: bool) -> list[str]:
    tags: list[str] = []
    if snap.sales_ready:
        tags.append("sales-ready")
    if spoken:
        tags.append("spoken-evidence")
    if (snap.conversation_delta or 0) > 0:
        tags.append(f"+{snap.conversation_delta} score")
    if not tags:
        tags.append("updated")
    return tags
