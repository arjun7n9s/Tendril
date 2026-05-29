"""Today feed schemas."""

from __future__ import annotations

from pydantic import BaseModel


class TodayFeedItem(BaseModel):
    account_id: str
    account_name: str
    domain: str | None = None
    total_score: int
    sales_ready: bool
    source: str
    conversation_delta: int | None = None
    why_now: str
    reason_tags: list[str]
    updated_at: str


class TodayFeedResponse(BaseModel):
    items: list[TodayFeedItem]
    total: int
    generated_at: str
