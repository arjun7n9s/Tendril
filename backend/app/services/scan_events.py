"""Helper that writes ScanEvent rows with auto-incrementing sequence.

Every external call (Bright Data, AI/ML API, MemoryService) and every
phase transition writes one row through this helper. Metadata is
sanitized before it lands in the DB.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import ScanEventType, ScanStatus
from app.models.scan_event import ScanEvent
from app.services.sanitization import sanitize_metadata


class ScanEventLogger:
    """Convenience wrapper around the scan_events table.

    Holds a per-instance sequence counter. Initialize one logger per
    scan_runner invocation.
    """

    def __init__(self, db: Session, scan_id: str) -> None:
        self.db = db
        self.scan_id = scan_id
        # Resume sequence numbering from whatever's already persisted.
        existing = (
            db.scalar(
                select(func.max(ScanEvent.sequence)).where(ScanEvent.scan_id == scan_id)
            )
            or 0
        )
        self._next_sequence = int(existing) + 1

    def emit(
        self,
        event_type: ScanEventType,
        message: str,
        *,
        phase: ScanStatus | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ScanEvent:
        event = ScanEvent(
            scan_id=self.scan_id,
            sequence=self._next_sequence,
            phase=phase,
            event_type=event_type,
            message=message,
            metadata_json=sanitize_metadata(metadata) or None,
        )
        self._next_sequence += 1
        self.db.add(event)
        self.db.flush()
        return event

    # Convenience wrappers
    def phase_started(self, phase: ScanStatus, message: str | None = None) -> ScanEvent:
        return self.emit(
            ScanEventType.phase_started,
            message or f"phase started: {phase.value}",
            phase=phase,
        )

    def phase_completed(
        self, phase: ScanStatus, *, message: str | None = None, **counts: Any
    ) -> ScanEvent:
        return self.emit(
            ScanEventType.phase_completed,
            message or f"phase completed: {phase.value}",
            phase=phase,
            metadata=counts or None,
        )

    def warning(self, message: str, **metadata: Any) -> ScanEvent:
        return self.emit(ScanEventType.warning, message, metadata=metadata or None)

    def error(self, message: str, **metadata: Any) -> ScanEvent:
        return self.emit(ScanEventType.error, message, metadata=metadata or None)

    def info(self, message: str, **metadata: Any) -> ScanEvent:
        return self.emit(ScanEventType.info, message, metadata=metadata or None)

    def bright_data_call(
        self,
        message: str,
        *,
        phase: ScanStatus | None = None,
        replayed: bool = False,
        **metadata: Any,
    ) -> ScanEvent:
        event_type = (
            ScanEventType.bright_data_call_replayed
            if replayed
            else ScanEventType.bright_data_call
        )
        return self.emit(event_type, message, phase=phase, metadata=metadata or None)

    def aiml_call(
        self,
        message: str,
        *,
        phase: ScanStatus | None = None,
        replayed: bool = False,
        **metadata: Any,
    ) -> ScanEvent:
        event_type = (
            ScanEventType.aiml_call_replayed if replayed else ScanEventType.aiml_call
        )
        return self.emit(event_type, message, phase=phase, metadata=metadata or None)
