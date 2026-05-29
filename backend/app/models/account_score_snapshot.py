"""Unified, modality-aware account actionability score.

The web `scores` table is keyed to a single web `scan` (its `scan_id` is
NOT NULL). To let *both* web scans and media scans contribute to one headline
number — without a destructive migration on `scores` — we record the account's
current actionability score as a snapshot here, decoupled from any single scan.

Each snapshot stores the four rubric components plus a `source` describing what
produced it (web scan vs. media scan) and an optional delta breakdown, so the
UI can say "78 (+14 from spoken evidence)".
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id

if TYPE_CHECKING:
    from app.models.account import Account


class AccountScoreSnapshot(TimestampMixin, Base):
    __tablename__ = "account_score_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "snap"))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    fit_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timing_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relationship_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    sales_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # "web_scan" | "media_scan"
    source: Mapped[str] = mapped_column(String(32), default="web_scan", nullable=False)
    # Originating scan/job id for traceability.
    origin_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Contribution from conversation signals over the prior snapshot, when this
    # snapshot was produced by a media scan.
    conversation_delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reasoning_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    account: Mapped[Account] = relationship("Account")
