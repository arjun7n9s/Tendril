"""Watchtower subscription for an account.

The autonomous watchtower periodically re-scans watched accounts for new
public conversations and alerts the rep when something material surfaces.
Each row is one account's watch schedule and state.
"""

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import MediaScanMode

if TYPE_CHECKING:
    from app.models.account import Account


class AccountWatch(TimestampMixin, Base):
    __tablename__ = "account_watches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "watch"))
    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), nullable=False, unique=True, index=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    mode: Mapped[MediaScanMode] = mapped_column(
        String(16), default=MediaScanMode.mock, nullable=False
    )
    interval_seconds: Mapped[int] = mapped_column(Integer, default=86400, nullable=False)
    last_scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_media_scan_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    account: Mapped[Account] = relationship("Account")
