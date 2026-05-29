"""Media / multimodal signal engine schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    MediaScanEventType,
    MediaScanMode,
    MediaScanStage,
    MediaSourceStatus,
    MediaSourceType,
    PrivacyStatus,
    SignalType,
    TranscriptProvider,
)
from app.schemas.common import ORMModel, TimestampedModel


class MediaScanCreateRequest(BaseModel):
    mode: MediaScanMode = MediaScanMode.mock
    max_sources: int = Field(default=3, ge=1, le=10)
    force_refresh: bool = False


class MediaScanCreateResponse(BaseModel):
    media_scan_id: str
    status: MediaScanStage
    mode: MediaScanMode


class MediaScanCounts(BaseModel):
    sources_discovered: int = 0
    sources_selected: int = 0
    transcripts: int = 0
    cache_hits: int = 0
    conversation_signals: int = 0
    memory_writes: int = 0


class MediaScanRead(TimestampedModel):
    id: str
    account_id: str
    mode: MediaScanMode
    status: MediaScanStage
    current_stage: MediaScanStage
    progress_percent: int
    attempt_count: int
    last_error: str | None = None
    score_delta: int | None = None
    stage_state_json: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    counts: MediaScanCounts = Field(default_factory=MediaScanCounts)


class MediaScanEventRead(ORMModel):
    id: str
    media_scan_job_id: str
    sequence: int
    stage: MediaScanStage | None = None
    event_type: MediaScanEventType
    message: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaScanEventList(BaseModel):
    items: list[MediaScanEventRead]
    total: int


class MediaSourceRead(TimestampedModel):
    id: str
    account_id: str
    media_scan_job_id: str | None = None
    media_asset_id: str | None = None
    source_url: str
    source_type: MediaSourceType
    title: str | None = None
    description: str | None = None
    publisher: str | None = None
    speaker_names_json: list[str] | None = None
    published_at: datetime | None = None
    duration_seconds: int | None = None
    transcript_available: bool
    discovery_query: str | None = None
    rank_score: float | None = None
    rank_reason: str | None = None
    status: MediaSourceStatus
    metadata_json: dict[str, Any] | None = None


class ConversationSignalRead(TimestampedModel):
    id: str
    media_scan_job_id: str
    account_id: str
    media_source_id: str | None = None
    media_asset_id: str | None = None
    transcript_id: str | None = None
    signal_type: SignalType
    title: str
    summary: str | None = None
    fact_text: str | None = None
    inference_text: str | None = None
    recommended_action: str | None = None
    source_url: str
    quote_text: str | None = None
    quote_start_seconds: float | None = None
    quote_end_seconds: float | None = None
    speaker_label: str | None = None
    observed_at: date | None = None
    confidence: float
    recency_days: int | None = None
    privacy_status: PrivacyStatus
    metadata_json: dict[str, Any] | None = None


class ConversationSignalList(BaseModel):
    items: list[ConversationSignalRead]
    total: int


class TranscriptSegment(BaseModel):
    start: float | None = None
    end: float | None = None
    speaker: str | None = None
    text: str | None = None
    privacy_status: str | None = None


class TranscriptRead(TimestampedModel):
    id: str
    media_asset_id: str
    provider: TranscriptProvider
    language: str | None = None
    scrubbed_text: str | None = None
    segments_json: list[dict[str, Any]] | None = None
    confidence: float | None = None
    pii_status: PrivacyStatus
    pii_findings_json: dict[str, Any] | None = None
