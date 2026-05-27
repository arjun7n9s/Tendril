"""Phase 3 end-to-end live scan with mocked Bright Data."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.jobs.scan_runner import run_scan


@pytest.fixture
def _live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "false")
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-bd-key")
    monkeypatch.setenv("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    monkeypatch.setenv("BRIGHT_DATA_SERP_ZONE", "test-serp")
    monkeypatch.setenv("BRIGHT_DATA_UNLOCKER_ZONE", "test-unlocker")
    monkeypatch.setenv("BRIGHT_DATA_BROWSER_WS", "")  # disable browser fallback
    get_settings.cache_clear()


@respx.mock
def test_full_live_scan_pipeline(
    client: TestClient, seed_csv_path: Path, _live_env: None
) -> None:
    # Seed accounts.
    with seed_csv_path.open("rb") as f:
        client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    accounts = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    account_id = accounts["items"][0]["id"]

    # All Bright Data calls are intercepted. SERP returns a small list, Unlocker
    # returns a rich HTML page. The same endpoint handles both based on `zone`
    # in the request body, but for the test we don't need to differentiate.
    serp_html = (
        "<html><body>"
        "<div class='g'><a href='https://ramp.com/careers/data-engineer'>"
        "<h3>Data Engineer at Ramp</h3></a></div>"
        "<div class='g'><a href='https://ramp.com/engineering/scaling'>"
        "<h3>Scaling our data platform</h3></a></div>"
        "<div class='g'><a href='https://github.com/ramp/data-tools'>"
        "<h3>ramp/data-tools</h3></a></div>"
        "</body></html>"
    )
    rich_page = (
        "<html><head><title>Page</title></head><body>"
        "<h1>Senior Data Engineer at Ramp</h1>"
        + "<p>" + "We are hiring data engineers with Kafka and Snowflake. " * 50 + "</p>"
        + "</body></html>"
    )

    def _responder(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        if '"zone":"test-serp"' in body:
            return httpx.Response(200, text=serp_html)
        return httpx.Response(200, text=rich_page)

    respx.post("https://api.brightdata.com/request").mock(side_effect=_responder)

    # Trigger live scan.
    create = client.post(
        f"/api/v1/accounts/{account_id}/scans",
        json={"mode": "live"},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["mode"] == "live"
    scan_id = body["scan_id"]

    # Drive runner synchronously so assertions don't race the BackgroundTask.
    run_scan(scan_id)

    status = client.get(f"/api/v1/scans/{scan_id}").json()
    assert status["status"] == "completed", status
    counts = status["counts"]
    assert counts["discovered"] >= 2
    assert counts["selected"] >= 1
    assert counts["fetched"] >= 1
    assert counts["bright_data_calls"] >= 2  # at least one SERP + one Unlocker

    sources = client.get(f"/api/v1/scans/{scan_id}/sources").json()
    assert all("ramp.com" in s["url"] or "github.com" in s["url"] for s in sources)

    evidence = client.get(f"/api/v1/scans/{scan_id}/evidence").json()
    success_evidence = [e for e in evidence if e["fetch_status"] == "success"]
    assert success_evidence
    assert all(e["fetch_method"] == "unlocker" for e in success_evidence)
    # Sanitization: the response must not leak the API key.
    assert all("test-bd-key" not in (e["metadata_json"] or {}).__repr__() for e in evidence)


@respx.mock
def test_live_smoke_endpoint_via_client(_live_env: None) -> None:
    """Ensures the smoke helper works against a mocked Bright Data."""
    import asyncio

    from app.services.brightdata_client import BrightDataRestClient

    respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(200, text="Welcome to Bright Data!")
    )

    async def _go() -> None:
        async with BrightDataRestClient() as c:
            res = await c.smoke_test()
            assert "Bright Data" in res.body
            assert res.target_host == "geo.brdtest.com"

    asyncio.run(_go())
