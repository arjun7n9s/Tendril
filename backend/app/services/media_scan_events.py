"""Media-scan event logger.

Mirrors `ScanEventLogger` for the durable media pipeline. Sequence numbers
resume from whatever is already persisted, so a resumed job keeps appending to
the same trace. Messages and metadata are sanitized exactly like the web
pipeline so no credential ever lands in the DB or the frontend.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import MediaScanEventType, MediaScanStage
from app.models.media_scan_event import MediaScanEvent
from app.services.sanitization import sanitize_metadata
from app.services.scan_events import _sanitize_message

_STAGE_START_MESSAGES = {
    MediaScanStage.discover_sources: "Discovering public conversations",
    MediaScanStage.rank_sources: "Ranking sources by GTM signal potential",
    MediaScanStage.resolve_media: "Resolving cheapest transcript/media path",
    MediaScanStage.hash_media: "Hashing media and checking transcript cache",
    MediaScanStage.transcribe: "Transcribing audio",
    MediaScanStage.scrub_transcript: "Scrubbing transcript for PII",
    MediaScanStage.extract_signals: "Extracting conversation signals",
    MediaScanStage.write_memory: "Writing scrubbed evidence to memory",
    MediaScanStage.score_account: "Refreshing account score",
    MediaScanStage.notify: "Notifying rep",
}

_STAGE_DONE_MESSAGES = {
    MediaScanStage.discover_sources: "Source discovery complete",
    MediaScanStage.rank_sources: "Ranking complete",
    MediaScanStage.resolve_media: "Media resolution complete",
    MediaScanStage.hash_media: "Media hashing complete",
    MediaScanStage.transcribe: "Transcription complete",
    MediaScanStage.scrub_transcript: "PII scrubbing complete",
    MediaScanStage.extract_signals: "Signal extraction complete",
    MediaScanStage.write_memory: "Memory updated",
    MediaScanStage.score_account: "Score refreshed",
    MediaScanStage.notify: "Notifications sent",
}


class MediaScanEventLogger:
    """Convenience wrapper around the media_scan_events table."""

    def __init__(self, db: Session, job_id: str) -> None:
        self.db = db
        self.job_id = job_id
        existing = (
            db.scalar(
                select(func.max(MediaScanEvent.sequence)).where(
                    MediaScanEvent.media_scan_job_id == job_id
                )
            )
            or 0
        )
        self._next_sequence = int(existing) + 1

    def emit(
        self,
        event_type: MediaScanEventType,
        message: str,
        *,
        stage: MediaScanStage | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MediaScanEvent:
        event = MediaScanEvent(
            media_scan_job_id=self.job_id,
            sequence=self._next_sequence,
            stage=stage,
            event_type=event_type,
            message=_sanitize_message(message),
            metadata_json=sanitize_metadata(metadata) or None,
        )
        self._next_sequence += 1
        self.db.add(event)
        self.db.flush()
        return event

    # ---- Convenience wrappers ----

    def stage_started(self, stage: MediaScanStage, message: str | None = None) -> MediaScanEvent:
        return self.emit(
            MediaScanEventType.stage_started,
            message or _STAGE_START_MESSAGES.get(stage, f"stage started: {stage.value}"),
            stage=stage,
        )

    def stage_completed(
        self, stage: MediaScanStage, *, message: str | None = None, **counts: Any
    ) -> MediaScanEvent:
        return self.emit(
            MediaScanEventType.stage_completed,
            message or _STAGE_DONE_MESSAGES.get(stage, f"stage completed: {stage.value}"),
            stage=stage,
            metadata=counts or None,
        )

    def stage_skipped(self, stage: MediaScanStage, *, reason: str) -> MediaScanEvent:
        return self.emit(
            MediaScanEventType.stage_skipped,
            f"stage skipped: {stage.value} ({reason})",
            stage=stage,
            metadata={"reason": reason},
        )

    def cache_hit(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(MediaScanEventType.cache_hit, message, stage=stage, metadata=metadata or None)

    def bright_data_call(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(
            MediaScanEventType.bright_data_call, message, stage=stage, metadata=metadata or None
        )

    def featherless_call(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(
            MediaScanEventType.featherless_call, message, stage=stage, metadata=metadata or None
        )

    def aiml_call(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(MediaScanEventType.aiml_call, message, stage=stage, metadata=metadata or None)

    def speechmatics_call(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(
            MediaScanEventType.speechmatics_call, message, stage=stage, metadata=metadata or None
        )

    def memory_write(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(
            MediaScanEventType.memory_write, message, stage=stage, metadata=metadata or None
        )

    def pii_redaction(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(
            MediaScanEventType.pii_redaction, message, stage=stage, metadata=metadata or None
        )

    def notification(self, message: str, *, stage: MediaScanStage | None = None, **metadata: Any):
        return self.emit(
            MediaScanEventType.notification, message, stage=stage, metadata=metadata or None
        )

    def warning(self, message: str, **metadata: Any) -> MediaScanEvent:
        return self.emit(MediaScanEventType.warning, message, metadata=metadata or None)

    def error(self, message: str, **metadata: Any) -> MediaScanEvent:
        return self.emit(MediaScanEventType.error, message, metadata=metadata or None)

    def info(self, message: str, **metadata: Any) -> MediaScanEvent:
        return self.emit(MediaScanEventType.info, message, metadata=metadata or None)
