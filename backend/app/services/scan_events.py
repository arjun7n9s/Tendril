"""Helper that writes ScanEvent rows with auto-incrementing sequence.

Every external call (Bright Data, AI/ML API, MemoryService) and every
phase transition writes one row through this helper. Both metadata and
the human-readable message are sanitized before they land in the DB,
so a careless f-string that includes a target URL or token never leaks.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import ScanEventType, ScanStatus
from app.models.scan_event import ScanEvent
from app.services.sanitization import host_of, sanitize_metadata, sanitize_url

# Conservative URL detector. Matches http(s) and ws(s) URLs, including
# those with embedded user:pass. Captures everything until the first
# whitespace or quote, so we can replace with the host-only form.
_URL_IN_MESSAGE_RE = re.compile(
    r"""(?P<url>(?:https?|wss?)://[^\s"'<>)\]]+)""",
    re.IGNORECASE,
)


def _sanitize_message(message: str) -> str:
    """Replace any full URL embedded in a message with a host-only form.

    Keeps message readability ("fetched ramp.com") while ensuring no
    query strings, embedded credentials, or full paths leak through
    scan_events into frontend responses or logs.
    """
    if not message:
        return message

    def _replace(match: re.Match[str]) -> str:
        raw = match.group("url")
        host = host_of(raw)
        if host:
            return host
        return sanitize_url(raw)

    return _URL_IN_MESSAGE_RE.sub(_replace, message)


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
            message=_sanitize_message(message),
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
