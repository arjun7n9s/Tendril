"""Notification center schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.models.enums import NotificationType
from app.schemas.common import TimestampedModel


class NotificationRead(TimestampedModel):
    id: str
    account_id: str | None = None
    notification_type: NotificationType
    title: str
    body: str | None = None
    link: str | None = None
    read: bool
    metadata_json: dict[str, Any] | None = None


class NotificationList(BaseModel):
    items: list[NotificationRead]
    total: int
    unread: int
