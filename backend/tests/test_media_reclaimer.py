"""Crash-recovery reclaimer tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import get_sessionmaker
from app.models.enums import MediaScanMode, MediaScanStage
from app.models.media_scan_job import MediaScanJob
from app.services.media_reclaimer import find_stalled_jobs, reclaim_stalled_jobs


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


def _make_job(db, account_id: str, *, heartbeat_age_seconds: int, status: MediaScanStage):
    now = datetime.now(UTC)
    job = MediaScanJob(
        account_id=account_id,
        mode=MediaScanMode.mock,
        status=status,
        current_stage=status,
        stage_state_json={},
        started_at=now - timedelta(seconds=heartbeat_age_seconds + 10),
        last_heartbeat_at=now - timedelta(seconds=heartbeat_age_seconds),
    )
    db.add(job)
    db.commit()
    return job.id


def test_stalled_job_detected_and_reclaimed(
    client: TestClient, seeded_account: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MEDIA_SCAN_PHASE_TIMEOUT_SECONDS", "60")
    from app.config import get_settings

    get_settings.cache_clear()

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        # A non-terminal job whose heartbeat is well past the stage timeout.
        stalled_id = _make_job(
            db, seeded_account, heartbeat_age_seconds=600, status=MediaScanStage.transcribe
        )
        # A fresh non-terminal job that should NOT be reclaimed.
        fresh_id = _make_job(
            db, seeded_account, heartbeat_age_seconds=1, status=MediaScanStage.transcribe
        )

    with SessionLocal() as db:
        stalled = find_stalled_jobs(db)
        ids = {j.id for j in stalled}
        assert stalled_id in ids
        assert fresh_id not in ids

    enqueued: list[str] = []
    with SessionLocal() as db:
        reclaimed = reclaim_stalled_jobs(db, enqueue=enqueued.append)
    assert stalled_id in reclaimed
    assert fresh_id not in reclaimed
    assert stalled_id in enqueued

    get_settings.cache_clear()


def test_completed_job_never_reclaimed(
    client: TestClient, seeded_account: str
) -> None:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        done_id = _make_job(
            db, seeded_account, heartbeat_age_seconds=99999, status=MediaScanStage.completed
        )
    with SessionLocal() as db:
        stalled = find_stalled_jobs(db)
        assert done_id not in {j.id for j in stalled}
