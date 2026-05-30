"""Hosted Cognee Cloud REST adapter for the MemoryService protocol.

Tendril uses **Cognee Cloud** (the managed tenant configured in `.env`) as its
graph memory backend. This adapter talks to the tenant's HTTP API directly —
there is no local Cognee SDK / local graph store involved.

Cloud API (base URL = `COGNEE_API_URL`, auth via `X-Api-Key`):
- `POST /api/v1/remember`  multipart upload; ingests text and builds the graph.
- `POST /api/v1/search`    `{query, search_type, datasets}`; graph-grounded recall.

Design decisions:
- **Account-scoped datasets.** Each account gets its own dataset
  (`<prefix>_acct_<account_id>`) so recall returns *that account's* accumulated
  web + conversation memory, not a global blob. This mirrors the JSONL
  per-account rollup and is what makes the brief's "why now" account-specific.
- **Write-through to JSONL.** Every packet is also mirrored to the local JSONL
  rollup. That gives a safety net when the cloud is slow/unavailable, keeps the
  read-loop's query fallback populated, and provides a replayable local memory
  for an API-free demo.
- **Never breaks a scan.** Any cloud error degrades to the local rollup; the
  pipeline always proceeds.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from app.logging_setup import get_logger
from app.models.enums import ScanEventType
from app.services.memory_service import JsonlMemoryService, MemoryHit, MemoryPacket, _host
from app.services.scan_events import ScanEventLogger

log = get_logger("cognee_memory")

_DATASET_SAFE_RE = re.compile(r"[^a-zA-Z0-9_]+")


class CogneeMemoryService:
    """Cognee Cloud REST implementation of the MemoryService protocol."""

    def __init__(
        self,
        *,
        dataset_prefix: str,
        fallback_dir: Path,
        event_logger: ScanEventLogger | None = None,
        replayed: bool = False,
        client: httpx.Client | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = (settings.cognee_api_url or "").rstrip("/")
        self.api_key = settings.cognee_api_key
        self.dataset_prefix = dataset_prefix or "signalgraph"
        self.search_type = settings.cognee_search_type or "GRAPH_COMPLETION"
        self.run_in_background = settings.cognee_run_in_background
        self.timeout = max(1, settings.cognee_operation_timeout_seconds)
        self._event_logger = event_logger
        self._replayed = replayed
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=self.timeout, follow_redirects=True)
        # Silent local mirror (no event logger -> CogneeMemoryService emits the
        # single memory_write/memory event itself, so we don't double-count).
        self._fallback = JsonlMemoryService(fallback_dir / "fallback")

    # ---- public protocol ----

    def remember(self, packet: MemoryPacket) -> str:
        # 1) Always mirror locally first (cheap, supports fallback + offline demo).
        self._fallback.remember(packet)

        # 2) Write-through to Cognee Cloud.
        dataset = self._dataset_for(packet.account_id)
        cloud_ok = False
        try:
            self._remember_cloud(packet, dataset)
            cloud_ok = True
        except Exception as exc:  # never break a scan on memory
            log.warning("cognee_memory.remember_failed", error=str(exc)[:200])

        self._emit_write(packet, dataset, degraded=not cloud_ok)
        return packet.title

    def query(
        self, question: str, *, limit: int = 5, account_id: str | None = None
    ) -> list[MemoryHit]:
        dataset = self._dataset_for(account_id)
        try:
            hits = self._search_cloud(question, dataset=dataset, limit=limit)
        except Exception as exc:
            log.warning("cognee_memory.search_failed", error=str(exc)[:200])
            hits = []

        if hits:
            return hits
        # Cloud returned nothing usable (cold dataset, eventual consistency, or
        # an error): lean on the local rollup so the brief still has grounding.
        return self._fallback.query(question, limit=limit, account_id=account_id)

    def healthy(self) -> bool:
        return bool(self.base_url and self.api_key)

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    # ---- cloud calls ----

    def _headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.api_key}

    def _remember_cloud(self, packet: MemoryPacket, dataset: str) -> None:
        text = _packet_to_text(packet)
        files = {
            "data": (
                f"{packet.signal_id or 'packet'}.md",
                io.BytesIO(text.encode("utf-8")),
                "text/markdown",
            )
        }
        data = {
            "datasetName": dataset,
            "run_in_background": "true" if self.run_in_background else "false",
        }
        resp = self._client.post(
            f"{self.base_url}/api/v1/remember",
            headers=self._headers(),
            files=files,
            data=data,
        )
        resp.raise_for_status()

    def _search_cloud(
        self, question: str, *, dataset: str, limit: int
    ) -> list[MemoryHit]:
        payload = {
            "query": question,
            "search_type": self.search_type,
            "datasets": [dataset],
        }
        resp = self._client.post(
            f"{self.base_url}/api/v1/search",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=payload,
        )
        if resp.status_code >= 400:
            # A cold/absent dataset is a normal "no memory yet" case, not an error.
            log.info("cognee_memory.search_non_200", status=resp.status_code)
            return []
        return _parse_search_response(resp.json(), limit=limit)

    # ---- helpers ----

    def _dataset_for(self, account_id: str | None) -> str:
        if not account_id:
            return f"{self.dataset_prefix}_signals"
        safe = _DATASET_SAFE_RE.sub("_", account_id)
        return f"{self.dataset_prefix}_acct_{safe}"

    def _emit_write(self, packet: MemoryPacket, dataset: str, *, degraded: bool) -> None:
        if self._event_logger is None:
            return
        event_type = (
            ScanEventType.memory_write_replayed
            if self._replayed
            else ScanEventType.memory_write
        )
        self._event_logger.emit(
            event_type,
            f"memory_write: {packet.title}",
            metadata={
                "backend": "cognee_cloud" if not degraded else "jsonl_fallback",
                "dataset": dataset,
                "evidence_host": _host(packet.evidence_url),
                "signal_id": packet.signal_id,
                "degraded": degraded,
                "replayed": self._replayed,
            },
        )


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
    return "\n".join(fields)


def _parse_search_response(payload: Any, *, limit: int) -> list[MemoryHit]:
    """Coerce a Cognee Cloud /search or /recall response into MemoryHits.

    /search returns: [{dataset_id, dataset_name, search_result: [str, ...]}]
    /recall returns: [{kind, search_type, text, score, dataset_name, ...}]
    We handle both so the adapter is robust to either endpoint.
    """
    if not payload:
        return []
    items = payload if isinstance(payload, list) else [payload]

    hits: list[MemoryHit] = []
    for item in items:
        if not isinstance(item, dict):
            if isinstance(item, str) and item.strip():
                hits.append(MemoryHit(score=1.0, text=item.strip(), metadata={"backend": "cognee_cloud"}))
            continue

        dataset_name = item.get("dataset_name")

        # /search shape: search_result is a list of answer strings.
        results = item.get("search_result")
        if isinstance(results, list):
            for r in results:
                text = _coerce_text(r)
                if text:
                    hits.append(
                        MemoryHit(
                            score=1.0,
                            text=text,
                            metadata={"backend": "cognee_cloud", "dataset_name": dataset_name},
                        )
                    )
            continue

        # /recall shape: a single `text` per item.
        text = _coerce_text(item.get("text") or item.get("raw"))
        if text:
            score = item.get("score")
            hits.append(
                MemoryHit(
                    score=float(score) if isinstance(score, (int, float)) else 1.0,
                    text=text,
                    metadata={
                        "backend": "cognee_cloud",
                        "dataset_name": dataset_name,
                        "search_type": item.get("search_type"),
                    },
                )
            )

    return hits[:limit]


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("value", "text", "content", "answer"):
            v = value.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return json.dumps(value, sort_keys=True)[:400]
    return str(value).strip()
