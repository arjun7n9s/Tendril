"""CogneeMemoryService adapter tests."""

from __future__ import annotations

import sys
from pathlib import Path

from app.services.cognee_memory import CogneeMemoryService
from app.services.memory_service import MemoryPacket


class FakeCognee:
    def __init__(self, *, fail_remember: bool = False) -> None:
        self.fail_remember = fail_remember
        self.remember_calls = []
        self.recall_calls = []

    async def remember(self, data, **kwargs):
        if self.fail_remember:
            raise RuntimeError("cognee down")
        self.remember_calls.append((data, kwargs))
        return {"ok": True}

    async def recall(self, query_text, **kwargs):
        self.recall_calls.append((query_text, kwargs))
        return [{"text": "remembered signal", "score": 0.91}]


def _packet() -> MemoryPacket:
    return MemoryPacket(
        scan_id="scan_a",
        account_id="acc_a",
        dataset="signalgraph_signals",
        title="Expansion signal",
        body="Acme is hiring platform engineers",
        fact="Acme opened three platform roles",
        inference="Good moment for engineering productivity outreach",
        evidence_url="https://example.com/jobs",
        signal_id="sig_a",
    )


def test_cognee_memory_remember_writes_to_cognee(tmp_path: Path, monkeypatch) -> None:
    fake = FakeCognee()
    monkeypatch.setitem(sys.modules, "cognee", fake)

    svc = CogneeMemoryService(
        dataset_prefix="signalgraph",
        fallback_dir=tmp_path,
    )
    title = svc.remember(_packet())

    assert title == "Expansion signal"
    assert len(fake.remember_calls) == 1
    data, kwargs = fake.remember_calls[0]
    assert "Acme is hiring platform engineers" in data
    assert kwargs["dataset_name"] == "signalgraph_signals"
    assert kwargs["self_improvement"] is False


def test_cognee_memory_query_coerces_recall_results(tmp_path: Path, monkeypatch) -> None:
    fake = FakeCognee()
    monkeypatch.setitem(sys.modules, "cognee", fake)
    svc = CogneeMemoryService(dataset_prefix="signalgraph", fallback_dir=tmp_path)

    hits = svc.query("what changed?", limit=1)

    assert len(hits) == 1
    assert hits[0].text == "remembered signal"
    assert hits[0].score == 0.91
    assert fake.recall_calls[0][1]["datasets"] == ["signalgraph_signals"]


def test_cognee_memory_falls_back_to_jsonl_on_write_failure(tmp_path: Path, monkeypatch) -> None:
    fake = FakeCognee(fail_remember=True)
    monkeypatch.setitem(sys.modules, "cognee", fake)
    svc = CogneeMemoryService(dataset_prefix="signalgraph", fallback_dir=tmp_path)

    svc.remember(_packet())

    fallback_path = tmp_path / "fallback" / "scan_scan_a.jsonl"
    assert fallback_path.exists()
    assert "Expansion signal" in fallback_path.read_text(encoding="utf-8")
