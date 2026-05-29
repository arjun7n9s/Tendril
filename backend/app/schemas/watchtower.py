"""Watchtower schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import MediaScanMode
from app.schemas.common import TimestampedModel


class WatchUpsertRequest(BaseModel):
    enabled: bool = True
    mode: MediaScanMode | None = None
    interval_seconds: int | None = Field(default=None, ge=300, le=2_592_000)


class AccountWatchRead(TimestampedModel):
    id: str
    account_id: str
    enabled: bool
    mode: MediaScanMode
    interval_seconds: int
    last_scanned_at: datetime | None = None
    next_due_at: datetime | None = None
    last_media_scan_job_id: str | None = None
    consecutive_failures: int
    last_error: str | None = None


class WatchListResponse(BaseModel):
    items: list[AccountWatchRead]
    total: int
    watchtower_enabled: bool


class TickResponse(BaseModel):
    enabled: bool
    considered: int
    dispatched: int
    job_ids: list[str]
