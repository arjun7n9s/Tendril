"""Phase 6: blessed-run snapshot capture + cached replay."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

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
    ScanEventType,
    ScanMode,
    ScanStatus,
    SignalType,
    SourceType,
)
from app.models.evidence import EvidenceDocument
from app.models.outreach import OutreachDraft
from app.models.scan import Scan
from app.models.scan_event import ScanEvent
from app.models.score import Score
from app.models.signal import Signal
from app.models.source import Source
from app.services.blessed_runs import (
    BLESSED_RUNS_DIR,
    snapshot_scan,
    write_snapshot,
)


@pytest.fixture
def _isolated_blessed_runs_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect blessed_runs IO to a temp dir so tests don't touch fixtures."""
    target = tmp_path / "blessed_runs"
    target.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.blessed_runs.BLESSED_RUNS_DIR", target)
    monkeypatch.setattr("app.services.cache_runner.MEMORY_DIR", tmp_path / "memory")
    return target


def _seed_completed_scan() -> tuple[str, str]:
    """Build an account + completed scan with one signal/score/brief/outreach.

    Returns (account_id, scan_id).
    """
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = Account(
            name="Acme",
            domain="acme.com",
            industry="fintech",
            company_size="1001-5000",
            status=AccountStatus.target,
            metadata_json={"tech_keywords": ["kafka", "snowflake"]},
        )
        db.add(account)
        db.commit()

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
            url="https://acme.com/careers/eng",
            source_type=SourceType.careers,
            discovery_query="Acme careers Kafka",
            rank=1,
            selected_for_scrape=True,
        )
        db.add(src)
        db.commit()

        ev = EvidenceDocument(
            scan_id=scan.id,
            source_id=src.id,
            account_id=account.id,
            url="https://acme.com/careers/eng",
            title="Senior Data Engineer",
            content_markdown="# Senior Data Engineer\nWe use Kafka and Snowflake.",
            content_hash="abc123",
            fetched_at=datetime.now(UTC),
            fetch_status=FetchStatus.success,
            fetch_method=FetchMethod.unlocker,
            http_status=200,
            metadata_json={"length": 64},
        )
        db.add(ev)
        db.commit()

        sig = Signal(
            scan_id=scan.id,
            account_id=account.id,
            signal_type=SignalType.hiring,
            title="Hiring data platform reliability",
            summary="Open roles target Kafka + Snowflake reliability.",
            fact_text="Posting requires Kafka and Snowflake.",
            inference_text="Investing in reliability.",
            recommended_action="Send reliability checklist.",
            evidence_url="https://acme.com/careers/eng",
            evidence_document_id=ev.id,
            observed_at=date.today(),
            confidence=0.85,
            recency_days=2,
            metadata_json={"source": "live_extractor"},
        )
        db.add(sig)
        db.commit()

        score = Score(
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
        db.add(score)
        brief = Brief(
            scan_id=scan.id,
            account_id=account.id,
            title="Acme: GTM brief",
            executive_summary="Acme is investing in data platform reliability.",
            why_now="Hiring evidence in the last 14 days.",
            key_evidence_json=[
                {
                    "title": "Hiring data platform",
                    "evidence_url": "https://acme.com/careers/eng",
                    "confidence": 0.85,
                }
            ],
            risks_json=["Limited corroboration"],
            recommended_next_steps_json=["Send a reliability checklist"],
        )
        db.add(brief)
        draft = OutreachDraft(
            scan_id=scan.id,
            account_id=account.id,
            subject="Quick note on Acme's data platform",
            body="Hello, the recent engineering content suggests reliability investment...",
            tone=OutreachTone.warm,
            status=OutreachStatus.pending_review,
            guardrail_notes_json=[],
        )
        db.add(draft)
        db.commit()

        return account.id, scan.id


def test_snapshot_scan_serializes_full_run(
    _isolated_blessed_runs_dir: Path,
) -> None:
    account_id, scan_id = _seed_completed_scan()
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        snapshot = snapshot_scan(db, scan)

    assert snapshot["version"] == 1
    assert snapshot["account"]["domain"] == "acme.com"
    assert len(snapshot["sources"]) == 1
    assert len(snapshot["evidence_documents"]) == 1
    assert len(snapshot["signals"]) == 1
    assert snapshot["signals"][0]["confidence"] == 0.85
    assert snapshot["score"]["total_score"] == 72
    assert snapshot["brief"]["title"] == "Acme: GTM brief"
    assert len(snapshot["outreach_drafts"]) == 1


def test_write_snapshot_persists_to_blessed_runs_dir(
    _isolated_blessed_runs_dir: Path,
) -> None:
    account_id, scan_id = _seed_completed_scan()
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        snapshot = snapshot_scan(db, db.get(Scan, scan_id))

    path = write_snapshot(account_id, snapshot)
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["account"]["domain"] == "acme.com"


def test_cached_replay_creates_full_scan(
    _isolated_blessed_runs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: capture a snapshot, then trigger a cached scan that replays it."""
    account_id, source_scan_id = _seed_completed_scan()
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        snapshot = snapshot_scan(db, db.get(Scan, source_scan_id))
    write_snapshot(account_id, snapshot)

    # Trigger a fresh cached scan against the same account.
    with SessionLocal() as db:
        new_scan = Scan(
            account_id=account_id,
            scan_type="account_watchtower",
            status=ScanStatus.queued,
            mode=ScanMode.cached,
            progress_percent=0,
        )
        db.add(new_scan)
        db.commit()
        new_scan_id = new_scan.id

    # Speed up replay for the test by zeroing the per-phase pause.
    monkeypatch.setattr("app.services.cache_runner._PHASE_PACE_SECONDS", 0.0)
    run_scan(new_scan_id)

    with SessionLocal() as db:
        replayed = db.get(Scan, new_scan_id)
        assert replayed.status == ScanStatus.completed
        assert replayed.progress_percent == 100

        signals = list(
            db.scalars(select(Signal).where(Signal.scan_id == new_scan_id))
        )
        assert len(signals) == 1
        assert signals[0].evidence_url == "https://acme.com/careers/eng"

        brief = db.scalar(select(Brief).where(Brief.scan_id == new_scan_id))
        assert brief is not None
        assert brief.title == "Acme: GTM brief"

        score = db.scalar(select(Score).where(Score.scan_id == new_scan_id))
        assert score is not None
        assert score.total_score == 72
        assert (score.score_reasoning_json or {}).get("replayed") is True

        # Replayed events use the _replayed enum variants.
        events = list(
            db.scalars(
                select(ScanEvent)
                .where(ScanEvent.scan_id == new_scan_id)
                .order_by(ScanEvent.sequence)
            )
        )
        replayed_kinds = [
            e.event_type
            for e in events
            if (
                e.event_type == ScanEventType.bright_data_call_replayed
                or e.event_type == ScanEventType.aiml_call_replayed
                or e.event_type == ScanEventType.memory_write_replayed
            )
        ]
        assert replayed_kinds, "expected at least one *_replayed event"
        # Metadata on replayed events flags replayed=True.
        for e in events:
            if e.event_type == ScanEventType.bright_data_call_replayed:
                assert (e.metadata_json or {}).get("replayed") is True
                break


def test_cached_replay_falls_back_to_mock_when_no_snapshot(
    _isolated_blessed_runs_dir: Path, monkeypatch: pytest.MonkeyPatch, seed_csv_path: Path,
    client: TestClient,
) -> None:
    """If no snapshot exists for the account, cached scans degrade to mock."""
    with seed_csv_path.open("rb") as f:
        client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    accounts = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    account_id = accounts["items"][0]["id"]

    monkeypatch.setattr("app.services.cache_runner._PHASE_PACE_SECONDS", 0.0)
    create = client.post(
        f"/api/v1/accounts/{account_id}/scans",
        json={"mode": "cached"},
    )
    assert create.status_code == 201
    scan_id = create.json()["scan_id"]
    run_scan(scan_id)

    status = client.get(f"/api/v1/scans/{scan_id}").json()
    assert status["status"] == "completed"
    # Mock fallback produced real signals from fixtures.
    assert status["counts"]["signals"] >= 1


def test_domain_fallback_finds_snapshot_with_different_account_id(
    _isolated_blessed_runs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A snapshot captured against a previous account_id should still load
    via the domain-based fallback when the local DB has been recreated.
    """
    # Capture a snapshot against original account
    original_account_id, original_scan_id = _seed_completed_scan()
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        snapshot = snapshot_scan(db, db.get(Scan, original_scan_id))
    write_snapshot(original_account_id, snapshot)

    # Create a new account with the same domain but a different id, to
    # simulate a fresh local DB.
    with SessionLocal() as db:
        new_account = Account(
            name="Acme",
            domain="acme.com",
            industry="fintech",
            status=AccountStatus.target,
        )
        db.add(new_account)
        db.commit()
        new_account_id = new_account.id

        new_scan = Scan(
            account_id=new_account_id,
            scan_type="account_watchtower",
            status=ScanStatus.queued,
            mode=ScanMode.cached,
            progress_percent=0,
        )
        db.add(new_scan)
        db.commit()
        new_scan_id = new_scan.id

    monkeypatch.setattr("app.services.cache_runner._PHASE_PACE_SECONDS", 0.0)
    run_scan(new_scan_id)

    with SessionLocal() as db:
        replayed = db.get(Scan, new_scan_id)
        assert replayed.status == ScanStatus.completed
        # The replay populated the new account from the original snapshot.
        signals = list(
            db.scalars(select(Signal).where(Signal.scan_id == new_scan_id))
        )
        assert signals
        assert signals[0].evidence_url == "https://acme.com/careers/eng"
