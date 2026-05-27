"""Structured GTM findings extracted from evidence."""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import SignalType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.evidence import EvidenceDocument
    from app.models.person import Person
    from app.models.scan import Scan


class Signal(TimestampMixin, Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "sig"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    person_id: Mapped[str | None] = mapped_column(ForeignKey("people.id"), nullable=True)
    signal_type: Mapped[SignalType] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    fact_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    inference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_url: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("evidence_documents.id"), nullable=True
    )
    observed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    recency_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    scan: Mapped[Scan] = relationship("Scan", back_populates="signals")
    account: Mapped[Account] = relationship("Account", back_populates="signals")
    person: Mapped[Person | None] = relationship("Person", back_populates="signals")
    evidence_document: Mapped[EvidenceDocument | None] = relationship(
        "EvidenceDocument", back_populates="signals"
    )
