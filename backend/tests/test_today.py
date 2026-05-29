"""Today feed endpoint tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.jobs.media_scan_runner import run_media_scan
from app.jobs.scan_runner import run_scan


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


def test_today_empty_before_any_scan(client: TestClient) -> None:
    r = client.get("/api/v1/today")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert "generated_at" in body


def test_today_ranks_scanned_account(client: TestClient, seeded_account: str) -> None:
    web = client.post(
        f"/api/v1/accounts/{seeded_account}/scans", json={"mode": "mock"}
    ).json()
    run_scan(web["scan_id"])

    r = client.get("/api/v1/today")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    item = next(i for i in body["items"] if i["account_id"] == seeded_account)
    assert item["why_now"]
    assert item["total_score"] >= 0
    assert isinstance(item["reason_tags"], list)


def test_today_surfaces_spoken_evidence(client: TestClient, seeded_account: str) -> None:
    web = client.post(
        f"/api/v1/accounts/{seeded_account}/scans", json={"mode": "mock"}
    ).json()
    run_scan(web["scan_id"])
    media = client.post(
        f"/api/v1/accounts/{seeded_account}/media-scans", json={"mode": "mock"}
    ).json()
    run_media_scan(media["media_scan_id"])

    body = client.get("/api/v1/today").json()
    item = next(i for i in body["items"] if i["account_id"] == seeded_account)
    assert item["source"] == "media_scan"
    assert "spoken-evidence" in item["reason_tags"]
