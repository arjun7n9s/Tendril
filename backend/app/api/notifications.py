"""Notification center endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationList, NotificationRead

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
def list_notifications(
    unread_only: bool = Query(default=False),
    account_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> NotificationList:
    stmt = select(Notification)
    count_stmt = select(func.count()).select_from(Notification)
    if unread_only:
        stmt = stmt.where(Notification.read.is_(False))
        count_stmt = count_stmt.where(Notification.read.is_(False))
    if account_id:
        stmt = stmt.where(Notification.account_id == account_id)
        count_stmt = count_stmt.where(Notification.account_id == account_id)

    total = db.scalar(count_stmt) or 0
    unread = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.read.is_(False))
        )
        or 0
    )
    rows = db.scalars(
        stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return NotificationList(
        items=[NotificationRead.model_validate(n) for n in rows],
        total=total,
        unread=unread,
    )


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: str, db: Session = Depends(get_db)) -> NotificationRead:
    notif = db.get(Notification, notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="notification_not_found")
    notif.read = True
    db.add(notif)
    db.commit()
    return NotificationRead.model_validate(notif)


@router.post("/read-all")
def mark_all_read(
    account_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    stmt = select(Notification).where(Notification.read.is_(False))
    if account_id:
        stmt = stmt.where(Notification.account_id == account_id)
    rows = db.scalars(stmt).all()
    now = datetime.now(UTC)
    for n in rows:
        n.read = True
        n.updated_at = now
        db.add(n)
    db.commit()
    return {"updated": len(rows)}
