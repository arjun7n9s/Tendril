"""Brief + score schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.common import TimestampedModel


class BriefRead(TimestampedModel):
    id: str
    scan_id: str
    account_id: str
    title: str
    executive_summary: str | None = None
    why_now: str | None = None
    key_evidence_json: list[dict[str, Any]] | None = None
    risks_json: list[str] | None = None
    recommended_next_steps_json: list[str] | None = None


class ScoreRead(TimestampedModel):
    id: str
    scan_id: str
    account_id: str
    fit_score: int
    timing_score: int
    relationship_score: int
    evidence_score: int
    total_score: int
    sales_ready: bool
    score_reasoning_json: dict[str, Any] | None = None


class AccountDetail(BaseModel):
    """Enriched account detail returned by GET /accounts/{id}."""

    account: Any  # AccountRead but importing creates a cycle; resolved at use site.
    latest_scan: Any | None = None
    latest_score: ScoreRead | None = None
    latest_brief: BriefRead | None = None
    recent_signals: list[Any] = []
