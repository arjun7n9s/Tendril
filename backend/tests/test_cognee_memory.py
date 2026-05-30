"""CogneeMemoryService (Cognee Cloud REST adapter) tests.

These mock the hosted tenant's HTTP API with respx so we exercise the real
adapter code paths (multipart remember, JSON search, response parsing,
account-scoped datasets, and JSONL fallback) without touching the network.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.config import get_settings
from app.services.cognee_memory import CogneeMemoryService, _parse_search_response
from app.services.memory_service import MemoryPacket

BASE = "https://tenant-test.aws.cognee.ai"


@pytest.fixture(autouse=True)
def _cognee_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COGNEE_API_KEY", "test-cognee-key")
    monkeypatch.setenv("COGNEE_API_URL", BASE)
    monkeypatch.setenv("COGNEE_TENANT_ID", "tenant-123")
    monkeypatch.setenv("COGNEE_USER_ID", "user-123")
    monkeypatch.setenv("COGNEE_DATASET_PREFIX", "signalgraph")
    # Make writes synchronous in tests for determinism.
    monkeypatch.setenv("COGNEE_RUN_IN_BACKGROUND", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _packet(account_id: str = "acc_a") -> MemoryPacket:
    return MemoryPacket(
        scan_id="scan_a",
        account_id=account_id,
        dataset="signalgraph_signals",
        title="Expansion signal",
        body="Acme is hiring platform engineers",
        fact="Acme opened three platform roles",
        inference="Good moment for engineering productivity outreach",
        evidence_url="https://example.com/jobs",
        signal_id="sig_a",
        metadata={"signal_type": "hiring", "modality": "web"},
    )


@respx.mock
def test_remember_posts_multipart_to_account_dataset(tmp_path: Path) -> None:
    route = respx.post(f"{BASE}/api/v1/remember").mock(
        return_value=httpx.Response(
            200, json={"status": "completed", "dataset_id": "d1", "items_processed": 1}
        )
    )
    svc = CogneeMemoryService(dataset_prefix="signalgraph", fallback_dir=tmp_path)
    title = svc.remember(_packet())

    assert title == "Expansion signal"
    assert route.called
    request = route.calls.last.request
    # Auth header present, no bearer.
    assert request.headers.get("X-Api-Key") == "test-cognee-key"
    body = request.content.decode("utf-8", errors="ignore")
    # Account-scoped dataset name travels in the multipart form.
    assert "signalgraph_acct_acc_a" in body
    # Local mirror also written.
    assert (tmp_path / "fallback" / "account_acc_a.jsonl").exists()


@respx.mock
def test_query_parses_search_result_shape(tmp_path: Path) -> None:
    respx.post(f"{BASE}/api/v1/search").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "dataset_id": "d1",
                    "dataset_name": "signalgraph_acct_acc_a",
                    "search_result": [
                        "Acme is hiring senior data platform engineers (Kafka, Snowflake)."
                    ],
                }
            ],
        )
    )
    svc = CogneeMemoryService(dataset_prefix="signalgraph", fallback_dir=tmp_path)
    hits = svc.query("what changed?", limit=3, account_id="acc_a")

    assert len(hits) == 1
    assert "Kafka" in hits[0].text
    assert hits[0].metadata["backend"] == "cognee_cloud"


@respx.mock
def test_query_falls_back_to_jsonl_when_cloud_empty(tmp_path: Path) -> None:
    # Seed the local mirror via a successful remember (remember mocked 200).
    respx.post(f"{BASE}/api/v1/remember").mock(
        return_value=httpx.Response(200, json={"status": "completed"})
    )
    # Cloud search returns nothing usable.
    respx.post(f"{BASE}/api/v1/search").mock(return_value=httpx.Response(200, json=[]))

    svc = CogneeMemoryService(dataset_prefix="signalgraph", fallback_dir=tmp_path)
    svc.remember(_packet())
    hits = svc.query("hiring platform engineers", limit=3, account_id="acc_a")

    assert hits, "expected JSONL fallback to return the mirrored packet"
    assert hits[0].metadata["backend"] == "jsonl"


@respx.mock
def test_remember_degrades_to_fallback_on_cloud_error(tmp_path: Path) -> None:
    respx.post(f"{BASE}/api/v1/remember").mock(return_value=httpx.Response(500, text="boom"))
    svc = CogneeMemoryService(dataset_prefix="signalgraph", fallback_dir=tmp_path)

    # Must not raise even though the cloud write failed.
    title = svc.remember(_packet())
    assert title == "Expansion signal"
    # Local mirror still has it.
    assert (tmp_path / "fallback" / "account_acc_a.jsonl").exists()


def test_parse_search_response_handles_recall_shape() -> None:
    payload = [
        {
            "kind": "graph_completion",
            "search_type": "GRAPH_COMPLETION",
            "text": "Acme is hiring three data platform roles.",
            "score": None,
            "dataset_name": "signalgraph_acct_acc_a",
            "raw": {"value": "Acme is hiring three data platform roles."},
        }
    ]
    hits = _parse_search_response(payload, limit=5)
    assert len(hits) == 1
    assert "data platform" in hits[0].text


def test_dataset_name_is_account_scoped_and_safe(tmp_path: Path) -> None:
    svc = CogneeMemoryService(dataset_prefix="signalgraph", fallback_dir=tmp_path)
    assert svc._dataset_for("acc_123") == "signalgraph_acct_acc_123"
    # Unsafe characters collapse to underscores.
    assert svc._dataset_for("acc/../x") == "signalgraph_acct_acc_x"
    # No account -> shared signals dataset.
    assert svc._dataset_for(None) == "signalgraph_signals"
