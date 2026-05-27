"""AI-generated account briefs."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.scan import Scan


class Brief(TimestampMixin, Base):
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "br"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_now: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_evidence_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    risks_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    recommended_next_steps_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)

    scan: Mapped[Scan] = relationship("Scan", back_populates="briefs")
    account: Mapped[Account] = relationship("Account", back_populates="briefs")
