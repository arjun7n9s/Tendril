"""Chronological, sanitized trace of a media scan.

Mirrors `scan_events` for the web pipeline. Every external call
(Bright Data, Featherless, AIMLAPI, Speechmatics, memory) and every stage
transition writes one row. Metadata is sanitized before persistence so no
credential ever leaks into the trace.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import MediaScanEventType, MediaScanStage

if TYPE_CHECKING:
    from app.models.media_scan_job import MediaScanJob


class MediaScanEvent(TimestampMixin, Base):
    __tablename__ = "media_scan_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "mevt"))
    media_scan_job_id: Mapped[str] = mapped_column(
        ForeignKey("media_scan_jobs.id"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[MediaScanStage | None] = mapped_column(String(32), nullable=True)
    event_type: Mapped[MediaScanEventType] = mapped_column(String(48), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    media_scan_job: Mapped[MediaScanJob] = relationship(
        "MediaScanJob", back_populates="events"
    )
