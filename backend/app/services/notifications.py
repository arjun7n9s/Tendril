"""Notification helpers for the in-app notification center.

The Watchtower's near-term delivery channel. The media pipeline writes
notifications here when a scan completes, a meaningful signal emerges, or a
score changes materially. WebSocket / email / Slack / Web Push layer on later.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import NotificationType
from app.models.notification import Notification


def create_notification(
    db: Session,
    *,
    notification_type: NotificationType,
    title: str,
    body: str | None = None,
    account_id: str | None = None,
    link: str | None = None,
    metadata: dict | None = None,
) -> Notification:
    notif = Notification(
        account_id=account_id,
        notification_type=notification_type,
        title=title,
        body=body,
        link=link,
        metadata_json=metadata or {},
    )
    db.add(notif)
    db.flush()
    return notif
