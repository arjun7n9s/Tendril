"""Cognee-backed MemoryService adapter.

Cognee is used as a local knowledge graph/vector memory layer. The scan
pipeline stays synchronous today, so this adapter contains the async bridge
and a JSONL fallback. A Cognee outage or config issue should not break a
demo scan.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from collections.abc import Awaitable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.models.enums import ScanEventType
from app.services.memory_service import JsonlMemoryService, MemoryHit, MemoryPacket, _host
from app.services.scan_events import ScanEventLogger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
COGNEE_VAR_DIR = PROJECT_ROOT / "backend" / "var" / "cognee"


class CogneeMemoryService:
    """Local Cognee implementation of the MemoryService protocol."""

    def __init__(
        self,
        *,
        dataset_prefix: str,
        fallback_dir: Path,
        event_logger: ScanEventLogger | None = None,
        replayed: bool = False,
    ) -> None:
        _configure_cognee_environment()

        import cognee

        self._cognee = cognee
        self.dataset_prefix = dataset_prefix or "signalgraph"
        self._event_logger = event_logger
        self._replayed = replayed
        self._fallback = JsonlMemoryService(
            fallback_dir / "fallback",
            event_logger=event_logger,
            replayed=replayed,
        )

    def remember(self, packet: MemoryPacket) -> str:
        dataset = packet.dataset or f"{self.dataset_prefix}_signals"
        try:
            _run_async(
                self._cognee.remember(
                    _packet_to_text(packet),
                    dataset_name=dataset,
                    self_improvement=False,
                    run_in_background=False,
                )
            )
            self._emit_write(packet, dataset)
            return packet.title
        except Exception:
            return self._fallback.remember(packet)

    def query(self, question: str, *, limit: int = 5) -> list[MemoryHit]:
        dataset = f"{self.dataset_prefix}_signals"
        try:
            raw_results = _run_async(
                self._cognee.recall(
                    question,
                    datasets=[dataset],
                    top_k=limit,
                    only_context=True,
                )
            )
        except Exception:
            return self._fallback.query(question, limit=limit)

        return _coerce_hits(raw_results, limit=limit)

    def healthy(self) -> bool:
        return COGNEE_VAR_DIR.exists()

    def _emit_write(self, packet: MemoryPacket, dataset: str) -> None:
        if self._event_logger is None:
            return

        event_type = (
            ScanEventType.memory_write_replayed if self._replayed else ScanEventType.memory_write
        )
        self._event_logger.emit(
            event_type,
            f"memory_write: {packet.title}",
            metadata={
                "backend": "cognee",
                "dataset": dataset,
                "evidence_host": _host(packet.evidence_url),
                "signal_id": packet.signal_id,
                "replayed": self._replayed,
            },
        )


def _configure_cognee_environment() -> None:
    """Set local-first Cognee defaults before importing Cognee."""
    settings = get_settings()
    data_dir = COGNEE_VAR_DIR / "data"
    system_dir = COGNEE_VAR_DIR / "system"
    cache_dir = COGNEE_VAR_DIR / "cache"
    logs_dir = COGNEE_VAR_DIR / "logs"
    for directory in (data_dir, system_dir, cache_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    _set_path_env_default("DATA_ROOT_DIRECTORY", data_dir)
    _set_path_env_default("SYSTEM_ROOT_DIRECTORY", system_dir)
    _set_path_env_default("CACHE_ROOT_DIRECTORY", cache_dir)
    _set_path_env_default("COGNEE_LOGS_DIR", logs_dir)
    os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
    os.environ.setdefault("CACHING", "false")
    os.environ.setdefault("EMBEDDING_PROVIDER", "fastembed")
    os.environ.setdefault("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    os.environ.setdefault("EMBEDDING_DIMENSIONS", "384")

    if settings.aiml_api_key:
        os.environ.setdefault("LLM_PROVIDER", "openai")
        os.environ.setdefault("LLM_API_KEY", settings.aiml_api_key)
        os.environ.setdefault("LLM_ENDPOINT", settings.aiml_api_base_url)
        os.environ.setdefault(
            "LLM_MODEL",
            settings.aiml_briefing_model or settings.aiml_extraction_model or "openai/gpt-4o-mini",
        )


def _set_path_env_default(key: str, default_path: Path) -> None:
    current = os.environ.get(key)
    if current and Path(current).is_absolute():
        return
    os.environ[key] = str(default_path)


def _packet_to_text(packet: MemoryPacket) -> str:
    fields = [
        f"# {packet.title}",
        f"Account ID: {packet.account_id}",
        f"Scan ID: {packet.scan_id}",
        f"Signal ID: {packet.signal_id or 'unknown'}",
        f"Body: {packet.body}",
    ]
    if packet.fact:
        fields.append(f"Fact: {packet.fact}")
    if packet.inference:
        fields.append(f"Inference: {packet.inference}")
    if packet.relationship:
        fields.append(f"Relationship: {packet.relationship}")
    if packet.evidence_url:
        fields.append(f"Evidence URL: {packet.evidence_url}")
    if packet.observed_at:
        fields.append(f"Observed at: {packet.observed_at}")
    if packet.metadata:
        fields.append(f"Metadata: {json.dumps(packet.metadata, sort_keys=True)}")
    fields.append(f"Envelope: {json.dumps(asdict(packet), default=str, sort_keys=True)}")
    return "\n".join(fields)


def _run_async(awaitable: Awaitable[Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    result: dict[str, Any] = {}

    def runner() -> None:
        try:
            result["value"] = asyncio.run(awaitable)
        except BaseException as exc:
            result["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")


def _coerce_hits(raw_results: Any, *, limit: int) -> list[MemoryHit]:
    if raw_results is None:
        return []
    if isinstance(raw_results, str):
        return [MemoryHit(score=1.0, text=raw_results, metadata={"backend": "cognee"})]
    if isinstance(raw_results, dict):
        raw_results = raw_results.get("results") or raw_results.get("data") or [raw_results]
    if not isinstance(raw_results, list):
        raw_results = list(raw_results) if hasattr(raw_results, "__iter__") else [raw_results]

    hits: list[MemoryHit] = []
    for item in raw_results[:limit]:
        text = _item_text(item)
        if not text:
            continue
        metadata = item if isinstance(item, dict) else {}
        score = float(metadata.get("score", 1.0)) if isinstance(metadata, dict) else 1.0
        hits.append(MemoryHit(score=score, text=text, metadata={"backend": "cognee", **metadata}))
    return hits


def _item_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("text", "content", "context", "chunk", "body"):
            value = item.get(key)
            if value:
                return str(value)
        return json.dumps(item, default=str, sort_keys=True)
    return str(item)
