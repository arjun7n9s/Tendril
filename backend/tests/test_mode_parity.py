"""Mode parity: mock | live | cached must produce identical API shapes.

Per the Phase 5/6 Definition of Done extras: every mode returns the
same shape from the public read endpoints. The values differ, but the
keys, types, and presence/absence patterns must match.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_sessionmaker
from app.jobs.scan_runner import run_scan
from app.models.account import Account
from app.models.brief import Brief
from app.models.enums import (
    AccountStatus,
    FetchMethod,
    FetchStatus,
    OutreachStatus,
    OutreachTone,
    ScanMode,
    ScanStatus,
    SignalType,
    SourceType,
)
from app.models.evidence import EvidenceDocument
from app.models.outreach import OutreachDraft
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal
from app.models.source import Source
from app.services.blessed_runs import snapshot_scan, write_snapshot


def _seed_completed_scan_for_blessed_run(domain: str = "ramp.com") -> str:
    """Build a real completed scan for `domain` so we can capture a
    blessed-run snapshot that the cached test will replay against the
    seeded account.
    """
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = db.scalar(
            __import__("sqlalchemy").select(Account).where(Account.domain == domain)
        )
        assert account is not None
        scan = Scan(
            account_id=account.id,
            scan_type="account_watchtower",
            status=ScanStatus.completed,
            mode=ScanMode.live,
            progress_percent=100,
            started_at=datetime.now(UTC) - timedelta(minutes=2),
            completed_at=datetime.now(UTC),
        )
        db.add(scan)
        db.commit()
        src = Source(
            scan_id=scan.id,
            account_id=account.id,
            url=f"https://{domain}/careers/eng",
            source_type=SourceType.careers,
            rank=1,
            selected_for_scrape=True,
        )
        db.add(src)
        db.commit()
        ev = EvidenceDocument(
            scan_id=scan.id,
            source_id=src.id,
            account_id=account.id,
            url=f"https://{domain}/careers/eng",
            title="Senior Engineer",
            content_markdown="# Senior Engineer\nKafka and Snowflake.",
            content_hash="abc",
            fetched_at=datetime.now(UTC),
            fetch_status=FetchStatus.success,
            fetch_method=FetchMethod.unlocker,
            http_status=200,
        )
        db.add(ev)
        db.commit()
        sig = Signal(
            scan_id=scan.id,
            account_id=account.id,
            signal_type=SignalType.hiring,
            title="Hiring data platform",
            summary="Open data platform roles.",
            fact_text="Posting requires Kafka and Snowflake.",
            inference_text="Investing in reliability.",
            recommended_action="Send a checklist.",
            evidence_url=f"https://{domain}/careers/eng",
            evidence_document_id=ev.id,
            observed_at=date.today(),
            confidence=0.85,
            recency_days=2,
        )
        db.add(sig)
        # Add a second signal so cached replay clears sales_ready.
        sig2 = Signal(
            scan_id=scan.id,
            account_id=account.id,
            signal_type=SignalType.migration,
            title="Migration to Snowflake",
            summary="Public engineering migration post.",
            fact_text="Blog describes Snowflake migration.",
            inference_text="Active modernization.",
            recommended_action="Share comparable case study.",
            evidence_url=f"https://blog.{domain}/migration",
            evidence_document_id=ev.id,
            observed_at=date.today(),
            confidence=0.78,
            recency_days=10,
        )
        db.add(sig2)
        db.add(
            Score(
                scan_id=scan.id,
                account_id=account.id,
                fit_score=24,
                timing_score=22,
                relationship_score=12,
                evidence_score=14,
                total_score=72,
                sales_ready=True,
                score_reasoning_json={"why": "test"},
            )
        )
        db.add(
            Brief(
                scan_id=scan.id,
                account_id=account.id,
                title=f"{account.name}: GTM brief",
                executive_summary="Investing in data platform.",
                why_now="Hiring + migration.",
                key_evidence_json=[
                    {
                        "title": "Hiring",
                        "evidence_url": f"https://{domain}/careers/eng",
                        "confidence": 0.85,
                    }
                ],
                risks_json=[],
                recommended_next_steps_json=["Re-scan in 7 days"],
            )
        )
        db.add(
            OutreachDraft(
                scan_id=scan.id,
                account_id=account.id,
                subject="Quick note",
                body="Hello, the recent engineering content suggests reliability investment.",
                tone=OutreachTone.warm,
                status=OutreachStatus.pending_review,
                guardrail_notes_json=[],
            )
        )
        db.commit()
        return account.id, scan.id


def _scan_response_keys(client: TestClient, scan_id: str) -> set[str]:
    return set(client.get(f"/api/v1/scans/{scan_id}").json().keys())


def _events_response_keys(client: TestClient, scan_id: str) -> set[str]:
    return set(client.get(f"/api/v1/scans/{scan_id}/events").json().keys())


def _account_detail_keys(client: TestClient, account_id: str) -> set[str]:
    return set(client.get(f"/api/v1/accounts/{account_id}").json().keys())


@respx.mock
def test_mock_live_cached_share_response_shapes(
    client: TestClient,
    seed_csv_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "app.services.blessed_runs.BLESSED_RUNS_DIR",
        tmp_path / "blessed_runs",
    )
    monkeypatch.setattr("app.services.cache_runner._PHASE_PACE_SECONDS", 0.0)

    # Seed once.
    with seed_csv_path.open("rb") as f:
        client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )

    accounts = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    account_id = accounts["items"][0]["id"]

    # ---- mock ----
    mock_scan_id = client.post(
        f"/api/v1/accounts/{account_id}/scans",
        json={"mode": "mock"},
    ).json()["scan_id"]
    run_scan(mock_scan_id)
    mock_scan_keys = _scan_response_keys(client, mock_scan_id)
    mock_events_keys = _events_response_keys(client, mock_scan_id)
    mock_detail_keys = _account_detail_keys(client, account_id)

    # ---- live (mocked Bright Data + AIML disabled => placeholder extractor) ----
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "false")
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-bd-key")
    monkeypatch.setenv("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    monkeypatch.setenv("BRIGHT_DATA_SERP_ZONE", "test-serp")
    monkeypatch.setenv("BRIGHT_DATA_UNLOCKER_ZONE", "test-unlocker")
    monkeypatch.setenv("AIML_API_KEY", "")  # drop AIML so extraction uses placeholder
    get_settings.cache_clear()

    serp_html = (
        '<html><body><div class="g">'
        '<a href="https://ramp.com/careers/x"><h3>Careers x</h3></a></div>'
        '<div class="g"><a href="https://ramp.com/blog/y"><h3>Blog y</h3></a></div>'
        "</body></html>"
    )
    rich_page = (
        "<html><body><h1>Ramp page</h1>"
        + "<p>" + "We use Kafka and Snowflake. " * 50 + "</p>"
        + "</body></html>"
    )

    def _bd(req: httpx.Request) -> httpx.Response:
        body = req.read().decode()
        if '"zone":"test-serp"' in body:
            return httpx.Response(200, text=serp_html)
        return httpx.Response(200, text=rich_page)

    respx.post("https://api.brightdata.com/request").mock(side_effect=_bd)

    live_scan_id = client.post(
        f"/api/v1/accounts/{account_id}/scans",
        json={"mode": "live"},
    ).json()["scan_id"]
    run_scan(live_scan_id)
    live_scan_keys = _scan_response_keys(client, live_scan_id)
    live_events_keys = _events_response_keys(client, live_scan_id)
    live_detail_keys = _account_detail_keys(client, account_id)

    # ---- cached: build a snapshot from the live scan first, then replay ----
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        snapshot = snapshot_scan(db, db.get(Scan, live_scan_id))
    write_snapshot(account_id, snapshot)

    cached_scan_id = client.post(
        f"/api/v1/accounts/{account_id}/scans",
        json={"mode": "cached"},
    ).json()["scan_id"]
    run_scan(cached_scan_id)
    cached_scan_keys = _scan_response_keys(client, cached_scan_id)
    cached_events_keys = _events_response_keys(client, cached_scan_id)
    cached_detail_keys = _account_detail_keys(client, account_id)

    # All three modes return the same response shape from each endpoint.
    assert mock_scan_keys == live_scan_keys == cached_scan_keys
    assert mock_events_keys == live_events_keys == cached_events_keys
    assert mock_detail_keys == live_detail_keys == cached_detail_keys
