"""Phase 7: POST /scans/{id}/brief/regenerate"""

from __future__ import annotations

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
    ScanMode,
    ScanStatus,
    SignalType,
)
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal


def _seed_completed_mock_scan(client: TestClient, seed_csv_path: Path) -> tuple[str, str]:
    with seed_csv_path.open("rb") as f:
        client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    accounts = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    account_id = accounts["items"][0]["id"]
    create = client.post(
        f"/api/v1/accounts/{account_id}/scans",
        json={"mode": "mock"},
    )
    scan_id = create.json()["scan_id"]
    run_scan(scan_id)
    return account_id, scan_id


def test_regenerate_creates_a_new_brief_row(
    client: TestClient, seed_csv_path: Path
) -> None:
    account_id, scan_id = _seed_completed_mock_scan(client, seed_csv_path)

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        before = list(db.scalars(select(Brief).where(Brief.scan_id == scan_id)))
    assert before, "expected an initial brief from the scan run"

    resp = client.post(f"/api/v1/scans/{scan_id}/brief/regenerate")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["scan_id"] == scan_id
    assert body["title"]

    with SessionLocal() as db:
        after = list(db.scalars(select(Brief).where(Brief.scan_id == scan_id)))
    assert len(after) == len(before) + 1


def test_regenerate_rejects_incomplete_scan(client: TestClient) -> None:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = Account(
            name="Acme",
            domain="acme.com",
            industry="fintech",
            status=AccountStatus.target,
        )
        db.add(account)
        db.commit()
        scan = Scan(
            account_id=account.id,
            scan_type="account_watchtower",
            status=ScanStatus.scraping,
            mode=ScanMode.mock,
            progress_percent=35,
        )
        db.add(scan)
        db.commit()
        scan_id = scan.id
    resp = client.post(f"/api/v1/scans/{scan_id}/brief/regenerate")
    assert resp.status_code == 409
    assert "scan_not_completed" in resp.json()["detail"]


def test_regenerate_404_for_unknown_scan(client: TestClient) -> None:
    resp = client.post("/api/v1/scans/scan_does_not_exist/brief/regenerate")
    assert resp.status_code == 404


def test_regenerate_does_not_rescrape(
    client: TestClient, seed_csv_path: Path
) -> None:
    """Regeneration should not add new evidence or signals; only a brief."""
    account_id, scan_id = _seed_completed_mock_scan(client, seed_csv_path)

    pre_signals = client.get(
        "/api/v1/signals", params={"scan_id": scan_id}
    ).json()["total"]
    pre_evidence = client.get(f"/api/v1/scans/{scan_id}/evidence").json()

    client.post(f"/api/v1/scans/{scan_id}/brief/regenerate")

    post_signals = client.get(
        "/api/v1/signals", params={"scan_id": scan_id}
    ).json()["total"]
    post_evidence = client.get(f"/api/v1/scans/{scan_id}/evidence").json()
    assert pre_signals == post_signals
    assert len(pre_evidence) == len(post_evidence)
