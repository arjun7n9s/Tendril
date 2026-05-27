"""Signal/source/evidence schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import FetchMethod, FetchStatus, SignalType, SourceType
from app.schemas.common import ORMModel, TimestampedModel


class SignalRead(TimestampedModel):
    id: str
    scan_id: str
    account_id: str
    person_id: str | None = None
    signal_type: SignalType
    title: str
    summary: str | None = None
    fact_text: str | None = None
    inference_text: str | None = None
    recommended_action: str | None = None
    evidence_url: str
    evidence_document_id: str | None = None
    observed_at: date | None = None
    confidence: float
    recency_days: int | None = None
    metadata_json: dict[str, Any] | None = None


class SignalList(BaseModel):
    items: list[SignalRead]
    total: int


class SourceRead(TimestampedModel):
    id: str
    scan_id: str
    account_id: str
    url: str
    source_type: SourceType
    discovery_query: str | None = None
    rank: int
    selected_for_scrape: bool


class EvidenceRead(ORMModel):
    id: str
    scan_id: str
    source_id: str | None = None
    account_id: str
    url: str
    title: str | None = None
    content_markdown: str | None = None
    content_hash: str | None = None
    fetched_at: datetime | None = None
    fetch_status: FetchStatus
    fetch_method: FetchMethod
    http_status: int | None = None
    metadata_json: dict[str, Any] | None = None
