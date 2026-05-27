"""Scan model: a live, cached, or mock intelligence run."""

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import ScanMode, ScanStatus, ScanType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.brief import Brief
    from app.models.evidence import EvidenceDocument
    from app.models.outreach import OutreachDraft
    from app.models.scan_event import ScanEvent
    from app.models.score import Score
    from app.models.signal import Signal
    from app.models.source import Source


class Scan(TimestampMixin, Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "scan"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    scan_type: Mapped[ScanType] = mapped_column(
        String(32), default=ScanType.account_watchtower, nullable=False
    )
    status: Mapped[ScanStatus] = mapped_column(
        String(32), default=ScanStatus.queued, nullable=False, index=True
    )
    mode: Mapped[ScanMode] = mapped_column(String(16), default=ScanMode.mock, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped[Account] = relationship("Account", back_populates="scans")
    events: Mapped[list[ScanEvent]] = relationship(
        "ScanEvent",
        back_populates="scan",
        order_by="ScanEvent.sequence",
        cascade="all, delete-orphan",
    )
    sources: Mapped[list[Source]] = relationship("Source", back_populates="scan")
    evidence_documents: Mapped[list[EvidenceDocument]] = relationship(
        "EvidenceDocument", back_populates="scan"
    )
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="scan")
    scores: Mapped[list[Score]] = relationship("Score", back_populates="scan")
    briefs: Mapped[list[Brief]] = relationship("Brief", back_populates="scan")
    outreach_drafts: Mapped[list[OutreachDraft]] = relationship(
        "OutreachDraft", back_populates="scan"
    )
