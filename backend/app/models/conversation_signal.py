"""A GTM signal extracted from a public spoken conversation.

Kept separate from the web `signals` table on purpose: it carries
conversation-specific evidence (timestamped quotes, speaker labels, transcript
linkage, privacy status) and links to a `media_scan_job` rather than a web
`scan`. This avoids a destructive migration on the existing `signals` table.
"""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import PrivacyStatus, SignalType

if TYPE_CHECKING:
    from app.models.account import Account


class ConversationSignal(TimestampMixin, Base):
    __tablename__ = "conversation_signals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "csig"))
    media_scan_job_id: Mapped[str] = mapped_column(
        ForeignKey("media_scan_jobs.id"), nullable=False, index=True
    )
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    media_source_id: Mapped[str | None] = mapped_column(
        ForeignKey("media_sources.id"), nullable=True, index=True
    )
    media_asset_id: Mapped[str | None] = mapped_column(
        ForeignKey("media_assets.id"), nullable=True
    )
    transcript_id: Mapped[str | None] = mapped_column(
        ForeignKey("transcripts.id"), nullable=True
    )
    signal_type: Mapped[SignalType] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    fact_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    inference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Conversation-specific evidence.
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    quote_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_start_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    quote_end_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    speaker_label: Mapped[str | None] = mapped_column(String(128), nullable=True)

    observed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recency_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    privacy_status: Mapped[PrivacyStatus] = mapped_column(
        String(24), default=PrivacyStatus.scrubbed, nullable=False
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    account: Mapped[Account] = relationship("Account")
