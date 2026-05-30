"""End-to-end Phase 2 mock scan: API drives the runner synchronously."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import get_sessionmaker
from app.jobs.scan_runner import run_scan
from app.models.account import Account
from app.models.brief import Brief
from app.models.enums import OutreachStatus, ScanMode, ScanStatus
from app.models.outreach import OutreachDraft
from app.models.scan_event import ScanEvent
from app.models.score import Score


@pytest.fixture
def seeded_account(client: TestClient, seed_csv_path: Path) -> str:
    """Seed the demo CSV via the API and return the Ramp account_id."""
    with seed_csv_path.open("rb") as f:
        r = client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    assert r.status_code == 200, r.text
    list_body = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    return list_body["items"][0]["id"]


def test_full_mock_scan_pipeline(client: TestClient, seeded_account: str) -> None:
    # Trigger a scan synchronously by calling the runner directly.
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"scan_type": "account_watchtower", "mode": "mock", "max_sources": 8},
    )
    assert create.status_code == 201, create.text
    scan_id = create.json()["scan_id"]

    # Drive the runner manually so the assertions don't race the BackgroundTask.
    run_scan(scan_id)

    status = client.get(f"/api/v1/scans/{scan_id}").json()
    assert status["status"] == "completed"
    assert status["progress_percent"] == 100
    counts = status["counts"]
    assert counts["fetched"] >= 3
    assert counts["signals"] >= 3
    assert counts["bright_data_calls"] >= 1
    assert counts["aiml_calls"] >= 1
    assert counts["memory_writes"] >= 3

    # Sources discovered + selected
    sources = client.get(f"/api/v1/scans/{scan_id}/sources").json()
    assert any(s["selected_for_scrape"] for s in sources)

    # Evidence persisted
    evidence = client.get(f"/api/v1/scans/{scan_id}/evidence").json()
    assert len(evidence) >= 3
    assert all(e["fetch_method"] == "mock" for e in evidence)

    # Signals accessible by account and scan
    signals_by_scan = client.get("/api/v1/signals", params={"scan_id": scan_id}).json()
    assert signals_by_scan["total"] >= 3
    assert all(s["evidence_url"] for s in signals_by_scan["items"])

    signals_by_account = client.get(
        f"/api/v1/accounts/{seeded_account}/signals"
    ).json()
    assert signals_by_account["total"] >= 3

    # Score persisted with rubric
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        score = db.query(Score).filter(Score.scan_id == scan_id).first()
        assert score is not None
        assert score.fit_score <= 30
        assert score.timing_score <= 30
        assert score.relationship_score <= 20
        assert score.evidence_score <= 20
        assert score.total_score <= 100
        assert score.score_reasoning_json is not None

        brief = db.query(Brief).filter(Brief.scan_id == scan_id).first()
        assert brief is not None
        assert brief.executive_summary
        assert brief.key_evidence_json

    # Brief endpoint
    brief_body = client.get(f"/api/v1/accounts/{seeded_account}/brief").json()
    assert "executive_summary" in brief_body
    assert brief_body["account_id"] == seeded_account


def test_scan_events_chronological_and_sanitized(
    client: TestClient, seeded_account: str
) -> None:
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["scan_id"]
    run_scan(scan_id)

    events = client.get(f"/api/v1/scans/{scan_id}/events").json()
    items = events["items"]
    assert items, "expected at least one scan event"
    # Sequence is monotonically increasing
    seqs = [e["sequence"] for e in items]
    assert seqs == sorted(seqs)
    assert seqs[0] == 1

    # Phases observed in correct order at minimum: discovering -> scraping -> ... -> briefing
    phases_in_order = [
        e["phase"] for e in items if e["event_type"] == "phase_started"
    ]
    expected = ["discovering", "scraping", "extracting", "graphing", "scoring", "briefing"]
    indexes = [phases_in_order.index(p) for p in expected if p in phases_in_order]
    assert indexes == sorted(indexes)

    # Sanitization: no metadata value should contain a bearer token shape or wss auth.
    flat = repr(events)
    assert "Bearer " not in flat
    assert "superproxy.io" not in flat


def test_scan_creates_outreach_when_sales_ready(
    client: TestClient, seeded_account: str
) -> None:
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["scan_id"]
    run_scan(scan_id)

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        drafts = db.query(OutreachDraft).filter(OutreachDraft.scan_id == scan_id).all()
        # Ramp has fintech + champion + 4 strong signals; should hit sales_ready.
        score = db.query(Score).filter(Score.scan_id == scan_id).first()
        if score and score.sales_ready:
            assert drafts, "expected outreach draft when sales_ready"
            assert drafts[0].status == OutreachStatus.pending_review

    pending = client.get("/api/v1/outreach/pending").json()
    if pending["total"] > 0:
        first = pending["items"][0]
        # Approve the draft.
        approved = client.post(f"/api/v1/outreach/{first['id']}/approve").json()
        assert approved["status"] == "approved"


def test_account_detail_shows_latest_scan_and_brief(
    client: TestClient, seeded_account: str
) -> None:
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["scan_id"]
    run_scan(scan_id)

    detail = client.get(f"/api/v1/accounts/{seeded_account}").json()
    assert detail["latest_scan"] is not None
    assert detail["latest_scan"]["status"] == "completed"
    assert detail["latest_score"] is not None
    assert detail["latest_brief"] is not None
    assert len(detail["recent_signals"]) >= 3


def test_live_mode_falls_back_to_mock_when_unconfigured(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Force unconfigured Bright Data REST.
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "")
    from app.config import get_settings
    from app.db import get_engine, get_sessionmaker as gs

    get_settings.cache_clear()

    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "live"},
    )
    body = create.json()
    # The endpoint coerces unconfigured live to mock at create time.
    assert body["mode"] == "mock"


def test_live_mode_requires_mock_mode_false(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Safety gate: even with Bright Data configured, live needs SIGNALGRAPH_MOCK_MODE=false."""
    # Bright Data REST stays configured (from .env) but mock mode is on.
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "live"},
    )
    assert create.status_code == 201
    assert create.json()["mode"] == "mock"


def test_live_mode_proceeds_when_gate_open(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When SIGNALGRAPH_MOCK_MODE=false and Bright Data is configured, live is honored."""
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "false")
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-key")
    monkeypatch.setenv("BRIGHT_DATA_SERP_ZONE", "test-serp")
    monkeypatch.setenv("BRIGHT_DATA_UNLOCKER_ZONE", "test-unlocker")
    from app.config import get_settings

    get_settings.cache_clear()

    # Stub run_scan so the BackgroundTask doesn't try to hit real Bright Data.
    import app.api.scans as scans_api

    monkeypatch.setattr(scans_api, "run_scan", lambda scan_id: None)

    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "live"},
    )
    assert create.status_code == 201
    assert create.json()["mode"] == "live"


def test_watchdog_records_stuck_phase(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The phase_timeout error_message should reference the actual stuck phase."""
    from datetime import UTC, datetime, timedelta

    from app.db import get_sessionmaker
    from app.models.enums import ScanStatus
    from app.models.scan import Scan

    # Force a tiny timeout so the watchdog fires immediately on read.
    monkeypatch.setenv("SIGNALGRAPH_SCAN_PHASE_TIMEOUT_SECONDS", "1")
    from app.config import get_settings

    get_settings.cache_clear()

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = Scan(
            account_id=seeded_account,
            scan_type="account_watchtower",
            status=ScanStatus.scraping,
            mode="mock",
            progress_percent=35,
            started_at=datetime.now(UTC) - timedelta(seconds=120),
        )
        db.add(scan)
        db.commit()
        scan_id = scan.id

    body = client.get(f"/api/v1/scans/{scan_id}").json()
    assert body["status"] == "failed"
    assert body["error_message"] == "phase_timeout:scraping"


def test_memory_jsonl_written_for_scan(client: TestClient, seeded_account: str) -> None:
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["scan_id"]
    run_scan(scan_id)

    project_root = Path(__file__).resolve().parents[1]
    jsonl_path = project_root / "var" / "memory" / f"scan_{scan_id}.jsonl"
    assert jsonl_path.exists(), f"expected memory packets at {jsonl_path}"
    lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 3


def test_scan_emits_memory_read_event(client: TestClient, seeded_account: str) -> None:
    """The read loop must emit a memory_read event during the graphing phase."""
    create = client.post(
        f"/api/v1/accounts/{seeded_account}/scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["scan_id"]
    run_scan(scan_id)

    events = client.get(f"/api/v1/scans/{scan_id}/events").json()["items"]
    memory_reads = [e for e in events if e["event_type"] == "memory_read"]
    assert memory_reads, "expected a memory_read event from the read loop"
    # It should report how many packets it recalled.
    assert "recalled" in memory_reads[0]["message"]


def test_second_scan_recalls_prior_account_memory(
    client: TestClient, seeded_account: str
) -> None:
    """A second scan should recall packets written by the first scan.

    This proves memory accumulates across scans (the cross-scan read loop),
    not just within a single run.
    """
    first = client.post(
        f"/api/v1/accounts/{seeded_account}/scans", json={"mode": "mock"}
    ).json()["scan_id"]
    run_scan(first)

    second = client.post(
        f"/api/v1/accounts/{seeded_account}/scans", json={"mode": "mock"}
    ).json()["scan_id"]
    run_scan(second)

    events = client.get(f"/api/v1/scans/{second}/events").json()["items"]
    reads = [e for e in events if e["event_type"] == "memory_read"]
    assert reads, "expected memory_read on the second scan"
    meta = reads[0].get("metadata_json") or {}
    # The second scan must see prior-scan packets in its recall.
    assert meta.get("prior", 0) >= 1
