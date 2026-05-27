"""Outreach schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.models.enums import OutreachStatus, OutreachTone
from app.schemas.common import TimestampedModel


class OutreachRead(TimestampedModel):
    id: str
    scan_id: str
    account_id: str
    person_id: str | None = None
    subject: str
    body: str
    tone: OutreachTone
    status: OutreachStatus
    guardrail_notes_json: list[Any] | None = None
    reviewer_feedback: str | None = None


class OutreachList(BaseModel):
    items: list[OutreachRead]
    total: int


class OutreachReject(BaseModel):
    feedback: str | None = None


class OutreachPatch(BaseModel):
    subject: str | None = None
    body: str | None = None
    tone: OutreachTone | None = None
