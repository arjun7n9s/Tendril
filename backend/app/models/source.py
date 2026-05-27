"""Candidate URLs discovered for a scan."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import SourceType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.evidence import EvidenceDocument
    from app.models.scan import Scan


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "src"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        String(32), default=SourceType.other, nullable=False
    )
    discovery_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    selected_for_scrape: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scan: Mapped[Scan] = relationship("Scan", back_populates="sources")
    account: Mapped[Account] = relationship("Account", back_populates="sources")
    evidence_documents: Mapped[list[EvidenceDocument]] = relationship(
        "EvidenceDocument", back_populates="source"
    )
