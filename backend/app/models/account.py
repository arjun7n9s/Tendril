"""Account model: companies being tracked."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import AccountStatus

if TYPE_CHECKING:
    from app.models.brief import Brief
    from app.models.evidence import EvidenceDocument
    from app.models.outreach import OutreachDraft
    from app.models.person import Person
    from app.models.scan import Scan
    from app.models.score import Score
    from app.models.signal import Signal
    from app.models.source import Source


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "acc"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[AccountStatus] = mapped_column(
        String(32), default=AccountStatus.target, nullable=False
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    people_current: Mapped[list[Person]] = relationship(
        "Person", back_populates="current_company", foreign_keys="Person.current_company_id"
    )
    people_previous: Mapped[list[Person]] = relationship(
        "Person", back_populates="previous_company", foreign_keys="Person.previous_company_id"
    )
    scans: Mapped[list[Scan]] = relationship("Scan", back_populates="account")
    sources: Mapped[list[Source]] = relationship("Source", back_populates="account")
    evidence_documents: Mapped[list[EvidenceDocument]] = relationship(
        "EvidenceDocument", back_populates="account"
    )
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="account")
    scores: Mapped[list[Score]] = relationship("Score", back_populates="account")
    briefs: Mapped[list[Brief]] = relationship("Brief", back_populates="account")
    outreach_drafts: Mapped[list[OutreachDraft]] = relationship(
        "OutreachDraft", back_populates="account"
    )
