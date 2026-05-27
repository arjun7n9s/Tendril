"""Person model: champions, contacts, public authors."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import RoleType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.outreach import OutreachDraft
    from app.models.signal import Signal


class Person(TimestampMixin, Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "per"))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    current_company_id: Mapped[str | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    previous_company_id: Mapped[str | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, unique=False)
    public_profile_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    personal_site_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    role_type: Mapped[RoleType] = mapped_column(String(32), default=RoleType.unknown, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    current_company: Mapped[Account | None] = relationship(
        "Account", foreign_keys=[current_company_id], back_populates="people_current"
    )
    previous_company: Mapped[Account | None] = relationship(
        "Account", foreign_keys=[previous_company_id], back_populates="people_previous"
    )
    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="person")
    outreach_drafts: Mapped[list[OutreachDraft]] = relationship(
        "OutreachDraft", back_populates="person"
    )
