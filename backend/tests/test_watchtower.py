"""Watchtower scheduling tests.

Exercises the pure scheduling logic and the API without spinning the daemon
loop. Scans are dispatched via an injected enqueue callable so tests stay fast
and deterministic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import get_sessionmaker
from app.jobs.media_scan_runner import run_media_scan
from app.models.account_watch import AccountWatch
from app.models.enums import MediaScanMode, MediaScanStage
from app.models.media_scan_job import MediaScanJob
from app.services import watchtower
from app.services.watchtower import WatchUpsert


@pytest.fixture
def seeded_account(client: TestClient, seed_csv_path: Path) -> str:
    with seed_csv_path.open("rb") as f:
        r = client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    assert r.status_code == 200, r.text
    body = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    return body["items"][0]["id"]


def test_upsert_and_get_watch(client: TestClient, seeded_account: str) -> None:
    r = client.put(
        f"/api/v1/accounts/{seeded_account}/watch",
        json={"enabled": True, "mode": "mock", "interval_seconds": 3600},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["account_id"] == seeded_account
    assert body["enabled"] is True
    assert body["interval_seconds"] == 3600

    got = client.get(f"/api/v1/accounts/{seeded_account}/watch").json()
    assert got["id"] == body["id"]


def test_tick_disabled_by_default(client: TestClient, seeded_account: str) -> None:
    client.put(
        f"/api/v1/accounts/{seeded_account}/watch",
        json={"enabled": True, "mode": "mock"},
    )
    # Default settings have WATCHTOWER_ENABLED off, so a tick dispatches nothing.
    r = client.post("/api/v1/watchtower/tick")
    assert r.status_code == 200
    body = r.json()
    assert body["enabled"] is False
    assert body["dispatched"] == 0


def test_tick_dispatches_due_watch_when_enabled(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WATCHTOWER_ENABLED", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    client.put(
        f"/api/v1/accounts/{seeded_account}/watch",
        json={"enabled": True, "mode": "mock", "interval_seconds": 3600},
    )

    # Drive tick directly with a synchronous enqueue so the scan runs inline.
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        result = watchtower.tick(db, enqueue=run_media_scan)

    assert result.enabled is True
    assert result.dispatched == 1
    job_id = result.job_ids[0]

    status = client.get(f"/api/v1/media-scans/{job_id}").json()
    assert status["status"] == "completed"

    # The watch advanced its schedule.
    with SessionLocal() as db:
        watch = db.scalar(
            select(AccountWatch).where(AccountWatch.account_id == seeded_account)
        )
        assert watch.last_scanned_at is not None
        assert watch.next_due_at is not None
        assert watch.last_media_scan_job_id == job_id

    get_settings.cache_clear()


def test_find_due_respects_batch_and_skips_active(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WATCHTOWER_ENABLED", "true")
    from app.config import get_settings

    get_settings.cache_clear()

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        watchtower.upsert_watch(
            db,
            account_id=seeded_account,
            payload=WatchUpsert(enabled=True, mode=MediaScanMode.mock),
        )
        db.commit()

        # An in-flight scan for the account should make it ineligible.
        job = MediaScanJob(
            account_id=seeded_account,
            mode=MediaScanMode.mock,
            status=MediaScanStage.transcribe,
            current_stage=MediaScanStage.transcribe,
            stage_state_json={},
            progress_percent=50,
        )
        db.add(job)
        db.commit()

        due = watchtower.find_due_watches(db, limit=5)
        assert all(w.account_id != seeded_account for w in due)

    get_settings.cache_clear()


def test_schedule_next_advances_by_interval() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    watch = AccountWatch(
        account_id="acc_x",
        enabled=True,
        mode=MediaScanMode.mock,
        interval_seconds=3600,
    )
    watchtower.schedule_next(watch, now=now)
    assert watch.last_scanned_at == now
    assert watch.next_due_at == now + timedelta(seconds=3600)


def test_not_due_when_next_due_in_future(
    client: TestClient, seeded_account: str
) -> None:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        watch = watchtower.upsert_watch(
            db,
            account_id=seeded_account,
            payload=WatchUpsert(enabled=True, mode=MediaScanMode.mock),
        )
        watch.next_due_at = datetime.now(UTC) + timedelta(hours=1)
        db.add(watch)
        db.commit()

        due = watchtower.find_due_watches(db, limit=5)
        assert all(w.account_id != seeded_account for w in due)
