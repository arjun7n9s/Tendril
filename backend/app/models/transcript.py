"""Transcription output for a media asset.

Stores both `raw_text` (only when raw retention is enabled) and `scrubbed_text`
(PII-redacted). Only scrubbed content and structured signals are written to the
memory layer.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import PrivacyStatus, TranscriptProvider

if TYPE_CHECKING:
    from app.models.media_asset import MediaAsset


class Transcript(TimestampMixin, Base):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(gen_id, "tr")
    )
    media_asset_id: Mapped[str] = mapped_column(
        ForeignKey("media_assets.id"), nullable=False, index=True
    )
    provider: Mapped[TranscriptProvider] = mapped_column(String(32), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    scrubbed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # List of {start, end, speaker, text} dicts.
    segments_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    diarization_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    pii_status: Mapped[PrivacyStatus] = mapped_column(
        String(24), default=PrivacyStatus.clean, nullable=False
    )
    pii_findings_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    media_asset: Mapped[MediaAsset] = relationship(
        "MediaAsset",
        back_populates="transcripts",
        foreign_keys=[media_asset_id],
    )
