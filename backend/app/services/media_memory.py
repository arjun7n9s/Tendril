"""Memory writes for conversation signals.

Reuses the existing pluggable MemoryService (JSONL/Cognee). Only scrubbed,
structured, evidence-backed content is written. Every packet carries the source
URL, transcript id, quote timestamp, and privacy status so memory stays
auditable and outreach never touches sensitive text.
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.models.account import Account
from app.models.conversation_signal import ConversationSignal
from app.models.enums import MediaScanStage, PrivacyStatus
from app.models.helpers import as_str
from app.services.media_scan_events import MediaScanEventLogger
from app.services.memory_service import MemoryPacket, build_memory_service

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = PROJECT_ROOT / "var" / "memory"


def write_conversation_memory(
    *,
    job_id: str,
    account: Account,
    signals: list[ConversationSignal],
    events: MediaScanEventLogger,
) -> int:
    """Write scrubbed conversation signals to the memory layer.

    Sensitive-blocked signals are never written. Returns the number written.
    """
    settings = get_settings()
    # The media event logger is not a ScanEventLogger, so we don't pass it to
    # the memory service (which expects the web logger). Memory-write events are
    # emitted here against the media trace instead.
    memory = build_memory_service(MEMORY_DIR)
    written = 0
    for sig in signals:
        if sig.privacy_status == PrivacyStatus.sensitive_blocked:
            events.warning(
                "skipped memory write for sensitive-flagged signal",
                stage=MediaScanStage.write_memory,
                signal_id=sig.id,
            )
            continue
        packet = MemoryPacket(
            scan_id=job_id,
            account_id=account.id,
            dataset=f"{settings.cognee_dataset_prefix}_conversations",
            title=f"{account.name}: {sig.title}",
            body=sig.summary or sig.fact_text or sig.title,
            fact=sig.fact_text,
            inference=sig.inference_text,
            relationship=f"Account: {account.name}",
            evidence_url=sig.source_url,
            observed_at=sig.observed_at.isoformat() if sig.observed_at else None,
            signal_id=sig.id,
            metadata={
                "modality": "conversation",
                "signal_type": as_str(sig.signal_type),
                "confidence": sig.confidence,
                "transcript_id": sig.transcript_id,
                "quote_start_seconds": sig.quote_start_seconds,
                "quote_end_seconds": sig.quote_end_seconds,
                "speaker_label": sig.speaker_label,
                "privacy_status": as_str(sig.privacy_status),
            },
        )
        try:
            memory.remember(packet)
            written += 1
            events.memory_write(
                f"memory_write: {sig.title}",
                stage=MediaScanStage.write_memory,
                signal_id=sig.id,
                privacy_status=as_str(sig.privacy_status),
            )
        except Exception as exc:
            events.warning(
                "memory write failed",
                stage=MediaScanStage.write_memory,
                error_type=type(exc).__name__,
            )
    return written
