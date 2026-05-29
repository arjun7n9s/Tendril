"""In-app notification center entries.

The Watchtower's near-term delivery channel. Background discovery and media
scans write notifications here; the frontend renders them in a bell/feed.
WebSocket / email / Slack / Web Push are later channels layered on the same
table.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import NotificationType

if TYPE_CHECKING:
    from app.models.account import Account


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "ntf"))
    account_id: Mapped[str | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True, index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        String(32), default=NotificationType.info, nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional deep-link target, e.g. /accounts/<id> or a media scan id.
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    account: Mapped[Account | None] = relationship("Account")
