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

    def query(
        self, question: str, *, limit: int = 5, account_id: str | None = None
    ) -> list[MemoryHit]: ...

    def healthy(self) -> bool: ...


# Tokens that carry no retrieval signal; dropped before overlap scoring.
_STOPWORDS = frozenset(
    {
        "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
        "with", "at", "by", "from", "as", "is", "are", "was", "were", "be",
        "been", "it", "its", "this", "that", "these", "those", "what", "which",
        "who", "whom", "how", "when", "where", "why", "show", "find", "list",
        "me", "my", "our", "your", "their", "has", "have", "had", "do", "does",
        "did", "will", "would", "can", "could", "should", "about", "into",
        "over", "any", "all", "new", "recent", "account", "accounts", "signal",
        "signals",
    }
)


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    out: set[str] = set()
    token = []
    for ch in text.lower():
        if ch.isalnum():
            token.append(ch)
        else:
            if token:
                word = "".join(token)
                if len(word) > 2 and word not in _STOPWORDS:
                    out.add(word)
                token = []
    if token:
        word = "".join(token)
        if len(word) > 2 and word not in _STOPWORDS:
            out.add(word)
    return out


def _packet_haystack(record: dict[str, Any]) -> str:
    parts = [
        record.get("title"),
        record.get("body"),
        record.get("fact"),
        record.get("inference"),
        record.get("relationship"),
    ]
    meta = record.get("metadata")
    if isinstance(meta, dict):
        parts.append(str(meta.get("signal_type")))
        parts.append(str(meta.get("modality")))
    return " ".join(p for p in parts if p)


class JsonlMemoryService:
    """File-backed memory with real retrieval.

    Each packet is written twice:

    - `scan_<scan_id>.jsonl` keeps the per-scan trace (unchanged behaviour
      relied on by the live panel and existing tests).
    - `account_<account_id>.jsonl` is a durable, append-only rollup that
      accumulates every web *and* conversation packet for an account across
      scans. This is what makes memory queryable over time without Cognee.

    `query()` scores rollup packets by keyword overlap with the question plus
    a small recency bonus, so the brief can be grounded in account history
    rather than a single run.
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

    def _account_path_for(self, account_id: str) -> Path:
        return self.base_dir / f"account_{account_id}.jsonl"

    def remember(self, packet: MemoryPacket) -> str:
        record = asdict(packet)
        line = json.dumps(record, ensure_ascii=False)

        path = self._path_for(packet.scan_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

        # Durable cross-scan, cross-modal rollup for retrieval.
        if packet.account_id:
            apath = self._account_path_for(packet.account_id)
            with apath.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

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

    def query(
        self, question: str, *, limit: int = 5, account_id: str | None = None
    ) -> list[MemoryHit]:
        """Return the most relevant stored packets for an account.

        Without an `account_id` there is no rollup to search, so we return
        an empty list (the previous stub contract).
        """
        if not account_id:
            return []
        apath = self._account_path_for(account_id)
        if not apath.exists():
            return []

        q_tokens = _tokenize(question)
        records: list[dict[str, Any]] = []
        for raw in apath.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                records.append(json.loads(raw))
            except json.JSONDecodeError:
                continue

        scored: list[tuple[float, int, MemoryHit]] = []
        for idx, rec in enumerate(records):
            haystack = _packet_haystack(rec)
            p_tokens = _tokenize(haystack)
            overlap = len(q_tokens & p_tokens) if q_tokens else 0
            # Recency bonus: later packets (appended later) rank slightly higher
            # so a tie breaks toward the most recent observation.
            recency = idx / max(len(records), 1)
            # When the question is empty/generic, fall back to recency ordering.
            score = float(overlap) + recency * 0.5
            if q_tokens and overlap == 0:
                continue
            hit = MemoryHit(
                score=round(score, 4),
                text=_packet_summary(rec),
                metadata={
                    "backend": "jsonl",
                    "title": rec.get("title"),
                    "evidence_url": rec.get("evidence_url"),
                    "observed_at": rec.get("observed_at"),
                    "written_at": rec.get("written_at"),
                    "scan_id": rec.get("scan_id"),
                    "signal_id": rec.get("signal_id"),
                    "dataset": rec.get("dataset"),
                    "modality": (rec.get("metadata") or {}).get("modality", "web"),
                    "signal_type": (rec.get("metadata") or {}).get("signal_type"),
                },
            )
            scored.append((score, idx, hit))

        if q_tokens and not scored:
            # No keyword overlap with anything: fall back to most-recent packets
            # so the brief still gets historical context.
            scored = [
                (idx / max(len(records), 1), idx, MemoryHit(
                    score=round(idx / max(len(records), 1), 4),
                    text=_packet_summary(rec),
                    metadata={
                        "backend": "jsonl",
                        "title": rec.get("title"),
                        "evidence_url": rec.get("evidence_url"),
                        "observed_at": rec.get("observed_at"),
                        "written_at": rec.get("written_at"),
                        "scan_id": rec.get("scan_id"),
                        "signal_id": rec.get("signal_id"),
                        "dataset": rec.get("dataset"),
                        "modality": (rec.get("metadata") or {}).get("modality", "web"),
                        "signal_type": (rec.get("metadata") or {}).get("signal_type"),
                    },
                ))
                for idx, rec in enumerate(records)
            ]

        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return [hit for _score, _idx, hit in scored[:limit]]

    def healthy(self) -> bool:
        return self.base_dir.exists()


def _packet_summary(record: dict[str, Any]) -> str:
    """Compact one-line text for a stored packet used in graph context."""
    title = (record.get("title") or "").strip()
    fact = (record.get("fact") or "").strip()
    inference = (record.get("inference") or "").strip()
    body = (record.get("body") or "").strip()
    detail = fact or body
    parts = [p for p in (title, detail) if p]
    text = " — ".join(parts) if parts else title
    if inference:
        text = f"{text} (inference: {inference})"
    return text[:400]


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
        if not settings.cognee_configured():
            log.warning("memory.cognee_not_configured_falling_back_to_jsonl")
            return JsonlMemoryService(
                base_dir,
                event_logger=event_logger,
                replayed=replayed,
            )
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
