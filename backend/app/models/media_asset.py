"""Content-addressable media asset.

A `media_asset` is the durable identity of a piece of audio/video, keyed by a
SHA-256 hash of its normalized bytes (`media_hash`). The same episode mentioned
across multiple accounts maps to one asset, so transcription is paid for once.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import MediaDownloadStatus, TranscriptionStatus

if TYPE_CHECKING:
    from app.models.transcript import Transcript


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=partial(gen_id, "masset")
    )
    # Content-addressable identity. Unique so the same payload dedups.
    media_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    byte_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    download_status: Mapped[MediaDownloadStatus] = mapped_column(
        String(24), default=MediaDownloadStatus.pending, nullable=False
    )
    transcription_status: Mapped[TranscriptionStatus] = mapped_column(
        String(24), default=TranscriptionStatus.pending, nullable=False
    )
    speechmatics_job_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transcript_id: Mapped[str | None] = mapped_column(
        ForeignKey("transcripts.id"), nullable=True
    )

    transcripts: Mapped[list[Transcript]] = relationship(
        "Transcript",
        back_populates="media_asset",
        foreign_keys="Transcript.media_asset_id",
    )
