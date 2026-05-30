"""Hosted Cognee Cloud memory smoke.

Usage:
    $env:TENDRIL_MEMORY_BACKEND="cognee"
    uv run python -m scripts.smoke_cognee_memory

Writes one synthetic packet through the configured memory backend and then
recalls it. Keep it manual because it calls the live Cognee Cloud tenant.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.memory_service import MemoryPacket, build_memory_service


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    memory = build_memory_service(backend_root / "var" / "memory")
    account_id = "demo_account"
    packet = MemoryPacket(
        scan_id="cognee_smoke",
        account_id=account_id,
        dataset="signalgraph_signals",
        title="Cognee smoke signal",
        body="A synthetic Tendril memory write for hosted Cognee setup.",
        fact="The hosted memory adapter accepted a packet.",
        inference="Cognee can be used as Tendril's graph memory backend.",
        relationship="Account: demo_account",
        evidence_url="https://example.com/cognee-smoke",
        signal_id="smoke_signal",
        metadata={"smoke": True, "signal_type": "other", "modality": "web"},
    )

    print(f"[memory] backend={memory.__class__.__name__} healthy={memory.healthy()}")
    written = memory.remember(packet)
    print(f"[memory] wrote={written}")

    # Cloud graph building may run in the background; give it a moment so the
    # account-scoped recall has something to return.
    time.sleep(8)

    hits = memory.query(
        "What did the Cognee smoke signal prove?",
        limit=3,
        account_id=account_id,
    )
    print(f"[memory] query_hits={len(hits)}")
    for hit in hits:
        backend = hit.metadata.get("backend") if isinstance(hit.metadata, dict) else "?"
        print(f"- [{backend}] score={hit.score:.2f} text={hit.text[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
