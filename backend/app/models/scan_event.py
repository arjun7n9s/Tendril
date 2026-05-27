"""Chronological trace of events emitted during a scan.

Frontend's premium live panel renders these in real time. Every external
call (Bright Data, AI/ML API, MemoryService) writes one row.

Sanitization rule: `metadata_json` may include zone name, target host,
http status, ms, content-length. Never bearer tokens, embedded URL auth,
Browser WS endpoints, or any credential value.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base_columns import TimestampMixin, gen_id
from app.models.enums import ScanEventType, ScanStatus

if TYPE_CHECKING:
    from app.models.scan import Scan


class ScanEvent(TimestampMixin, Base):
    __tablename__ = "scan_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=partial(gen_id, "evt"))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[ScanStatus | None] = mapped_column(String(32), nullable=True)
    event_type: Mapped[ScanEventType] = mapped_column(String(48), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    scan: Mapped[Scan] = relationship("Scan", back_populates="events")
