"""ICP profile model."""

from __future__ import annotations

from functools import partial

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id


class ICPProfile(TimestampMixin, Base):
    __tablename__ = "icp_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "icp"))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    industries_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    company_sizes_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    regions_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    target_roles_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    tech_keywords_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    pain_keywords_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    competitor_keywords_json: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
