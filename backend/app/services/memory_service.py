"""MemoryService interface and JSONL implementation.

Per refinement #1, every mock/live/cached scan writes through this
interface starting in Phase 2. The JSONL implementation is a no-op for
graph reasoning but persists packets in a Cognee-shaped envelope so the
real implementation slots in later without changes to the pipeline.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from app.models.enums import ScanEventType
from app.services.scan_events import ScanEventLogger


@dataclass
class MemoryPacket:
    """A single memory packet written into the graph layer.

    Mirrors the Cognee-shaped record described in the implementation
    plan, Section 8 step 5: account, signal, evidence, observed_at,
    fact, inference, relationship.
    """

    scan_id: str
    account_id: str
    dataset: str  # e.g. "signalgraph_signals" or "signalgraph_scan_<id>"
    title: str
    body: str
    fact: str | None = None
    inference: str | None = None
    relationship: str | None = None
    evidence_url: str | None = None
    observed_at: str | None = None
    signal_id: str | None = None
    person_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    written_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class MemoryHit:
    score: float
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryService(Protocol):
    """Pluggable memory layer.

    The Cognee implementation will satisfy this same protocol.
    """

    def remember(self, packet: MemoryPacket) -> str: ...

    def query(self, question: str, *, limit: int = 5) -> list[MemoryHit]: ...

    def healthy(self) -> bool: ...


class JsonlMemoryService:
    """Writes packets to `var/memory/scan_<scan_id>.jsonl`.

    Optionally emits a `memory_write` scan_event per packet.
    """

    def __init__(
        self,
        base_dir: Path,
        *,
        event_logger: ScanEventLogger | None = None,
        replayed: bool = False,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._event_logger = event_logger
        self._replayed = replayed

    def _path_for(self, scan_id: str) -> Path:
        return self.base_dir / f"scan_{scan_id}.jsonl"

    def remember(self, packet: MemoryPacket) -> str:
        path = self._path_for(packet.scan_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(packet), ensure_ascii=False) + "\n")

        if self._event_logger is not None:
            event_type = (
                ScanEventType.memory_write_replayed
                if self._replayed
                else ScanEventType.memory_write
            )
            self._event_logger.emit(
                event_type,
                f"memory_write: {packet.title}",
                metadata={
                    "dataset": packet.dataset,
                    "evidence_host": _host(packet.evidence_url),
                    "signal_id": packet.signal_id,
                    "replayed": self._replayed,
                },
            )

        return packet.title

    def query(self, question: str, *, limit: int = 5) -> list[MemoryHit]:
        # Stub: returns empty list. Cognee implementation replaces this.
        return []

    def healthy(self) -> bool:
        return self.base_dir.exists()


def _host(url: str | None) -> str | None:
    if not url:
        return None
    from app.services.sanitization import host_of

    return host_of(url)


def build_memory_service(
    base_dir: Path,
    *,
    event_logger: ScanEventLogger | None = None,
    replayed: bool = False,
) -> MemoryService:
    """Pick a MemoryService implementation based on settings.

    - `TENDRIL_MEMORY_BACKEND=jsonl` (default): writes to `var/memory/scan_<id>.jsonl`.
    - `TENDRIL_MEMORY_BACKEND=cognee`: returns the Cognee-backed adapter.
      If Cognee init fails, we log a warning and fall back to JSONL so the
      scan pipeline never breaks.

    Keeping this factory in one place means scan_runner and cache_runner
    do not need to know which backend is active.
    """
    from app.config import get_settings  # local import to avoid cycle
    from app.logging_setup import get_logger

    settings = get_settings()
    backend = (settings.tendril_memory_backend or "jsonl").lower()
    log = get_logger("memory")

    if backend == "cognee":
        try:
            from app.services.cognee_memory import (  # type: ignore[import-not-found]
                CogneeMemoryService,
            )

            return CogneeMemoryService(
                dataset_prefix=settings.cognee_dataset_prefix,
                fallback_dir=base_dir,
                event_logger=event_logger,
                replayed=replayed,
            )
        except Exception as exc:
            log.warning(
                "memory.cognee_init_failed_falling_back_to_jsonl",
                err=str(exc),
            )

    return JsonlMemoryService(
        base_dir,
        event_logger=event_logger,
        replayed=replayed,
    )
