"""Fetched evidence documents."""

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import FetchMethod, FetchStatus

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.scan import Scan
    from app.models.signal import Signal
    from app.models.source import Source


class EvidenceDocument(TimestampMixin, Base):
    __tablename__ = "evidence_documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "ev"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetch_status: Mapped[FetchStatus] = mapped_column(
        String(16), default=FetchStatus.success, nullable=False
    )
    fetch_method: Mapped[FetchMethod] = mapped_column(String(32), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    scan: Mapped[Scan] = relationship("Scan", back_populates="evidence_documents")
    source: Mapped[Source | None] = relationship("Source", back_populates="evidence_documents")
    account: Mapped[Account] = relationship("Account", back_populates="evidence_documents")
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="evidence_document")
