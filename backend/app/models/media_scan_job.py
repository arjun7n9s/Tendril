"""Durable media-scan pipeline state.

Unlike the web `Scan`, a media scan can take minutes and must survive process
restarts. `current_stage` + `stage_state_json` capture exactly how far the
pipeline progressed so it can resume idempotently from the last incomplete
stage instead of starting over.
"""

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import MediaScanMode, MediaScanStage

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.media_scan_event import MediaScanEvent
    from app.models.media_source import MediaSource


class MediaScanJob(TimestampMixin, Base):
    __tablename__ = "media_scan_jobs"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(gen_id, "mscan")
    )
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    mode: Mapped[MediaScanMode] = mapped_column(
        String(16), default=MediaScanMode.mock, nullable=False
    )
    status: Mapped[MediaScanStage] = mapped_column(
        String(32), default=MediaScanStage.queued, nullable=False, index=True
    )
    current_stage: Mapped[MediaScanStage] = mapped_column(
        String(32), default=MediaScanStage.queued, nullable=False
    )
    # Map of completed stage name -> serialized output (ids, counts, flags).
    stage_state_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped[Account] = relationship("Account")
    media_sources: Mapped[list[MediaSource]] = relationship(
        "MediaSource", back_populates="media_scan_job"
    )
    events: Mapped[list[MediaScanEvent]] = relationship(
        "MediaScanEvent",
        back_populates="media_scan_job",
        order_by="MediaScanEvent.sequence",
        cascade="all, delete-orphan",
    )
