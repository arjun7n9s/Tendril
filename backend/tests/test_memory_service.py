"""JsonlMemoryService tests."""

from __future__ import annotations

from pathlib import Path

from app.services.memory_service import JsonlMemoryService, MemoryPacket


def test_memory_service_writes_one_jsonl_per_scan(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    p1 = MemoryPacket(
        scan_id="scan_a",
        account_id="acc_a",
        dataset="signalgraph_signals",
        title="Hiring signal",
        body="Acme hiring data engineers",
    )
    p2 = MemoryPacket(
        scan_id="scan_a",
        account_id="acc_a",
        dataset="signalgraph_signals",
        title="Migration signal",
        body="Migrating to Snowflake",
    )
    svc.remember(p1)
    svc.remember(p2)

    path = tmp_path / "scan_scan_a.jsonl"
    assert path.exists()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert "Hiring" in lines[0]
    assert "Migration" in lines[1]


def test_memory_service_query_returns_empty_in_stub(tmp_path: Path) -> None:
    svc = JsonlMemoryService(tmp_path)
    assert svc.query("any question") == []
    assert svc.healthy()
