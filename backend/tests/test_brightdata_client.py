"""Bright Data REST client tests using respx to mock httpx."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.config import get_settings
from app.services.brightdata_client import (
    BRIGHT_DATA_SMOKE_URL,
    BrightDataNotConfiguredError,
    BrightDataResponseError,
    BrightDataRestClient,
)


@pytest.fixture(autouse=True)
def _live_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-bd-key")
    monkeypatch.setenv("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    monkeypatch.setenv("BRIGHT_DATA_SERP_ZONE", "test-serp")
    monkeypatch.setenv("BRIGHT_DATA_UNLOCKER_ZONE", "test-unlocker")
    get_settings.cache_clear()


@respx.mock
async def test_smoke_test_calls_unlocker_zone() -> None:
    route = respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(200, text="Welcome to Bright Data!")
    )
    async with BrightDataRestClient() as client:
        result = await client.smoke_test()
    assert result.http_status == 200
    assert "Bright Data" in result.body
    assert result.target_host == "geo.brdtest.com"
    assert route.called

    # Inspect the last request payload
    body = route.calls.last.request.read().decode()
    assert '"zone":"test-unlocker"' in body
    assert BRIGHT_DATA_SMOKE_URL in body


@respx.mock
async def test_serp_search_uses_serp_zone() -> None:
    route = respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(200, text="<html><body><a href='https://acme.com/x'>x</a></body></html>")
    )
    async with BrightDataRestClient() as client:
        result = await client.serp_search("acme careers data")
    assert route.called
    body = route.calls.last.request.read().decode()
    assert '"zone":"test-serp"' in body
    assert "acme+careers+data" in body or "acme%20careers%20data" in body or "acme careers data" in body
    assert result.http_status == 200


@respx.mock
async def test_unlock_url_uses_unlocker_zone() -> None:
    route = respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(200, text="<html><body>page</body></html>")
    )
    async with BrightDataRestClient() as client:
        result = await client.unlock_url("https://acme.com/careers")
    body = route.calls.last.request.read().decode()
    assert '"zone":"test-unlocker"' in body
    assert "https://acme.com/careers" in body
    assert result.target_host == "acme.com"


@respx.mock
async def test_retries_then_raises_on_persistent_5xx() -> None:
    route = respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(503, text="upstream blew up")
    )
    async with BrightDataRestClient(retry_min_wait=0, retry_max_wait=0) as client:
        with pytest.raises(BrightDataResponseError) as exc_info:
            await client.unlock_url("https://acme.com/x")
    assert exc_info.value.status == 503
    # Tenacity should have retried 3 times total.
    assert route.call_count == 3


async def test_raises_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "")
    get_settings.cache_clear()
    async with BrightDataRestClient() as client:
        with pytest.raises(BrightDataNotConfiguredError):
            await client.unlock_url("https://acme.com/x")
