"""Computed actionability score for an account scan."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.scan import Scan


class Score(TimestampMixin, Base):
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "scr"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    fit_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timing_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relationship_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sales_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score_reasoning_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    scan: Mapped[Scan] = relationship("Scan", back_populates="scores")
    account: Mapped[Account] = relationship("Account", back_populates="scores")
