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
    # Phase 4: live extraction would otherwise call AIML. Disable it so the
    # runner falls back to the placeholder extractor and the test stays offline.
    monkeypatch.setenv("AIML_API_KEY", "")
    monkeypatch.setenv("AIML_EXTRACTION_MODEL", "")
    monkeypatch.setenv("AIML_BRIEFING_MODEL", "")
    monkeypatch.setenv("AIML_DRAFT_MODEL", "")
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



@respx.mock
def test_live_scan_with_stubbed_aiml_extracts_real_signals(
    client: TestClient, seed_csv_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase 4: live mode end-to-end with Bright Data + AI/ML both stubbed."""
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "false")
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-bd-key")
    monkeypatch.setenv("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    monkeypatch.setenv("BRIGHT_DATA_SERP_ZONE", "test-serp")
    monkeypatch.setenv("BRIGHT_DATA_UNLOCKER_ZONE", "test-unlocker")
    monkeypatch.setenv("BRIGHT_DATA_BROWSER_WS", "")
    monkeypatch.setenv("AIML_API_KEY", "test-aiml-key")
    monkeypatch.setenv("AIML_EXTRACTION_MODEL", "stub-extractor")
    monkeypatch.setenv("AIML_BRIEFING_MODEL", "stub-briefer")
    monkeypatch.setenv("AIML_DRAFT_MODEL", "stub-drafter")
    get_settings.cache_clear()

    with seed_csv_path.open("rb") as f:
        client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    accounts = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    account_id = accounts["items"][0]["id"]

    serp_html = (
        "<html><body>"
        "<div class='g'><a href='https://ramp.com/careers/data-engineer'>"
        "<h3>Data Engineer at Ramp</h3></a></div>"
        "<div class='g'><a href='https://ramp.com/engineering/scaling'>"
        "<h3>Scaling our data platform</h3></a></div>"
        "</body></html>"
    )
    rich_page = (
        "<html><body><h1>Senior Data Engineer at Ramp</h1>"
        + "<p>" + "We use Kafka and Snowflake at scale. " * 50 + "</p>"
        + "</body></html>"
    )

    def _bd_responder(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        if '"zone":"test-serp"' in body:
            return httpx.Response(200, text=serp_html)
        return httpx.Response(200, text=rich_page)

    respx.post("https://api.brightdata.com/request").mock(side_effect=_bd_responder)

    # Stub the AimlClient class itself so we don't hit the network.
    from tests.test_extractor import StubAimlClient, StubAimlResponse
    import app.jobs.scan_runner as scan_runner

    extraction_response = {
        "signals": [
            {
                "signal_type": "hiring",
                "title": "Hiring data platform reliability",
                "summary": "Open roles target Kafka + Snowflake reliability.",
                "fact_text": "Posting requires Kafka and Snowflake.",
                "inference_text": "Investing in reliability.",
                "recommended_action": "Send reliability checklist.",
                "evidence_url": "<<EVIDENCE_URL>>",
                "observed_at": "2026-05-20",
                "confidence": 0.82,
            }
        ]
    }

    class _StubFactory:
        def __init__(self) -> None:
            # One response per evidence document fetched; the URL gets injected
            # by patching extract_signals_for_evidence.
            self.responses: list[StubAimlResponse] = [
                StubAimlResponse(payload=extraction_response) for _ in range(20)
            ]

        async def __aenter__(self) -> "StubAimlClient":
            self._inner = StubAimlClient(self.responses)
            return self._inner

        async def __aexit__(self, *exc) -> None:
            return None

    monkeypatch.setattr(scan_runner, "AimlClient", lambda: _StubFactory())

    # The stub returns the same evidence_url for every page; patch the
    # extractor's per-evidence helper to splice the actual URL in.
    import app.services.extractor as extractor_module

    real_extract = extractor_module.extract_signals_for_evidence

    async def _patched(*, aiml, account, icp, evidence):
        sig = dict(extraction_response["signals"][0])
        sig["evidence_url"] = evidence.url
        client_payload = {"signals": [sig]}
        # Bypass the AIML call entirely.
        from app.services.extractor import _validate_signal

        validated, rejections = [], []
        for raw in client_payload["signals"]:
            v, reason = _validate_signal(raw, evidence_url=evidence.url)
            if v is None:
                rejections.append(extractor_module.ExtractionRejection(evidence.url, reason or "rejected"))
            else:
                validated.append(v)
        return validated, rejections, 50

    monkeypatch.setattr(extractor_module, "extract_signals_for_evidence", _patched)

    create = client.post(
        f"/api/v1/accounts/{account_id}/scans",
        json={"mode": "live"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["mode"] == "live"
    scan_id = body["scan_id"]

    from app.jobs.scan_runner import run_scan

    run_scan(scan_id)

    status = client.get(f"/api/v1/scans/{scan_id}").json()
    assert status["status"] == "completed", status
    assert status["counts"]["signals"] >= 1
    # Memory writes happen in the graphing phase regardless.
    assert status["counts"]["memory_writes"] >= 1
    # Restore extractor function for any later tests.
    monkeypatch.setattr(extractor_module, "extract_signals_for_evidence", real_extract)

    signals_resp = client.get(f"/api/v1/scans/{scan_id}", params={}).json()
    assert signals_resp["counts"]["signals"] >= 1
