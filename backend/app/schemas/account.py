"""Account-related schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.models.enums import AccountStatus
from app.schemas.common import TimestampedModel


class AccountRead(TimestampedModel):
    id: str
    name: str
    domain: str | None = None
    industry: str | None = None
    company_size: str | None = None
    region: str | None = None
    status: AccountStatus
    metadata_json: dict[str, Any] | None = None


class AccountListResponse(BaseModel):
    items: list[AccountRead]
    total: int
    limit: int
    offset: int
