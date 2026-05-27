"""Scan-related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ScanEventType, ScanMode, ScanStatus, ScanType
from app.schemas.common import ORMModel, TimestampedModel


class ScanCreateRequest(BaseModel):
    scan_type: ScanType = ScanType.account_watchtower
    mode: ScanMode = ScanMode.mock
    max_sources: int = Field(default=8, ge=1, le=20)
    force_refresh: bool = False


class ScanCreateResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    mode: ScanMode


class ScanCounts(BaseModel):
    discovered: int = 0
    selected: int = 0
    fetched: int = 0
    failed: int = 0
    signals: int = 0
    bright_data_calls: int = 0
    aiml_calls: int = 0
    memory_writes: int = 0


class ScanRead(TimestampedModel):
    id: str
    account_id: str
    scan_type: ScanType
    status: ScanStatus
    mode: ScanMode
    progress_percent: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    counts: ScanCounts = Field(default_factory=ScanCounts)


class ScanEventRead(ORMModel):
    id: str
    scan_id: str
    sequence: int
    phase: ScanStatus | None = None
    event_type: ScanEventType
    message: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanEventList(BaseModel):
    items: list[ScanEventRead]
    total: int
