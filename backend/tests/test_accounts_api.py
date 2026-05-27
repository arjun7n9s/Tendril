"""Phase 1: HTTP smoke tests for /import/seed and /accounts."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_import_endpoint_then_list_accounts(
    client: TestClient, seed_csv_path: Path
) -> None:
    with seed_csv_path.open("rb") as f:
        resp = client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["accounts_created"] >= 5
    assert body["people_created"] >= 3
    assert body["icp_profiles_created"] == 1

    list_resp = client.get("/api/v1/accounts", params={"limit": 100})
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["total"] >= 5
    assert list_body["limit"] == 100
    names = {a["name"].lower() for a in list_body["items"]}
    assert "ramp" in names
    assert "shopify" in names

    target_resp = client.get(
        "/api/v1/accounts", params={"status": "target", "search": "ramp"}
    )
    assert target_resp.status_code == 200
    target_body = target_resp.json()
    assert target_body["total"] == 1
    assert target_body["items"][0]["domain"] == "ramp.com"


def test_get_account_detail(client: TestClient, seed_csv_path: Path) -> None:
    with seed_csv_path.open("rb") as f:
        client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )

    list_body = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    account_id = list_body["items"][0]["id"]
    detail = client.get(f"/api/v1/accounts/{account_id}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["account"]["domain"] == "ramp.com"
    assert detail_body["account"]["industry"] == "fintech"
    assert detail_body["latest_scan"] is None
    assert detail_body["latest_score"] is None
    assert detail_body["latest_brief"] is None
    assert detail_body["recent_signals"] == []


def test_get_account_404(client: TestClient) -> None:
    resp = client.get("/api/v1/accounts/acc_does_not_exist")
    assert resp.status_code == 404


def test_import_rejects_non_csv(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/import/seed",
        files={"file": ("seed.txt", b"not csv", "text/plain")},
    )
    assert resp.status_code == 400
