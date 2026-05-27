"""Human-reviewable outreach drafts."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import OutreachStatus, OutreachTone

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.person import Person
    from app.models.scan import Scan


class OutreachDraft(TimestampMixin, Base):
    __tablename__ = "outreach_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "out"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    person_id: Mapped[str | None] = mapped_column(ForeignKey("people.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[OutreachTone] = mapped_column(
        String(16), default=OutreachTone.warm, nullable=False
    )
    status: Mapped[OutreachStatus] = mapped_column(
        String(32), default=OutreachStatus.pending_review, nullable=False, index=True
    )
    guardrail_notes_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    reviewer_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    scan: Mapped[Scan] = relationship("Scan", back_populates="outreach_drafts")
    account: Mapped[Account] = relationship("Account", back_populates="outreach_drafts")
    person: Mapped[Person | None] = relationship("Person", back_populates="outreach_drafts")
