"""A discovered public spoken source for an account.

Represents a candidate conversation (podcast episode, YouTube talk, earnings
call, webinar) before we decide whether to spend money transcribing it.
"""

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import MediaSourceStatus, MediaSourceType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.media_asset import MediaAsset
    from app.models.media_scan_job import MediaScanJob


class MediaSource(TimestampMixin, Base):
    __tablename__ = "media_sources"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(gen_id, "msrc")
    )
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    media_scan_job_id: Mapped[str | None] = mapped_column(
        ForeignKey("media_scan_jobs.id"), nullable=True, index=True
    )
    media_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("media_assets.id"), nullable=True, index=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[MediaSourceType] = mapped_column(
        String(32), default=MediaSourceType.other, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    speaker_names_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transcript_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discovery_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MediaSourceStatus] = mapped_column(
        String(24), default=MediaSourceStatus.discovered, nullable=False
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    account: Mapped[Account] = relationship("Account")
    media_asset: Mapped[MediaAsset | None] = relationship("MediaAsset")
    media_scan_job: Mapped[MediaScanJob | None] = relationship(
        "MediaScanJob", back_populates="media_sources"
    )
