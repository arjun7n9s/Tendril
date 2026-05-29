"""Local Cognee memory smoke.

Usage:
    $env:TENDRIL_MEMORY_BACKEND="cognee"
    uv run python -m scripts.smoke_cognee_memory

This writes one synthetic memory packet through the configured memory
backend. Keep it manual because the first real Cognee run may download a
FastEmbed model and may call the configured LLM.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.memory_service import MemoryPacket, build_memory_service


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    memory = build_memory_service(backend_root / "var" / "memory")
    packet = MemoryPacket(
        scan_id="cognee_smoke",
        account_id="demo_account",
        dataset="signalgraph_signals",
        title="Cognee smoke signal",
        body="A synthetic Tendril memory write for local Cognee setup.",
        fact="The local memory adapter accepted a packet.",
        inference="Cognee can be used as Tendril's graph memory backend.",
        relationship="Account: demo_account",
        evidence_url="https://example.com/cognee-smoke",
        signal_id="smoke_signal",
        metadata={"smoke": True},
    )

    print(f"[memory] backend={memory.__class__.__name__} healthy={memory.healthy()}")
    written = memory.remember(packet)
    print(f"[memory] wrote={written}")
    hits = memory.query("What did the Cognee smoke signal prove?", limit=3)
    print(f"[memory] query_hits={len(hits)}")
    for hit in hits:
        print(f"- score={hit.score:.2f} text={hit.text[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
