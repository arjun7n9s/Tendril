"""Live scraper tests."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.config import get_settings
from app.db import get_sessionmaker
from app.models.account import Account
from app.models.enums import (
    AccountStatus,
    FetchMethod,
    FetchStatus,
    ScanMode,
    ScanStatus,
    SourceType,
)
from app.models.scan import Scan
from app.models.source import Source
from app.services.brightdata_client import BrightDataRestClient
from app.services.scan_events import ScanEventLogger
from app.services.scraper import scrape_source_live


@pytest.fixture(autouse=True)
def _live_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-bd-key")
    monkeypatch.setenv("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    monkeypatch.setenv("BRIGHT_DATA_SERP_ZONE", "test-serp")
    monkeypatch.setenv("BRIGHT_DATA_UNLOCKER_ZONE", "test-unlocker")
    monkeypatch.setenv("BRIGHT_DATA_BROWSER_WS", "")  # disable browser fallback
    get_settings.cache_clear()


def _make_scan_and_source(domain: str, *, path: str = "/careers/engineer"):
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = Account(name="Acme", domain=domain, status=AccountStatus.target)
        db.add(account)
        db.commit()
        scan = Scan(
            account_id=account.id,
            scan_type="account_watchtower",
            status=ScanStatus.scraping,
            mode=ScanMode.live,
            progress_percent=35,
        )
        db.add(scan)
        db.commit()
        src = Source(
            scan_id=scan.id,
            account_id=account.id,
            url=f"https://{domain}{path}",
            source_type=SourceType.careers,
            rank=1,
            selected_for_scrape=True,
        )
        db.add(src)
        db.commit()
        return account.id, scan.id, src.id


@respx.mock
async def test_scrape_source_live_success_via_unlocker() -> None:
    account_id, scan_id, src_id = _make_scan_and_source("acme.com")

    rich_html = (
        "<html><head><title>Senior Data Engineer</title></head><body>"
        "<h1>Senior Data Engineer</h1>"
        + "<p>" + "We are hiring. " * 100 + "</p>"
        + "</body></html>"
    )
    respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(200, text=rich_html)
    )

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        account = db.get(Account, account_id)
        src = db.get(Source, src_id)
        events = ScanEventLogger(db, scan.id)
        async with BrightDataRestClient() as client:
            ev = await scrape_source_live(
                db, scan=scan, account=account, src=src, client=client, events=events
            )
        db.commit()
        assert ev is not None
        assert ev.fetch_status == FetchStatus.success
        assert ev.fetch_method == FetchMethod.unlocker
        assert ev.content_markdown
        assert "Senior Data Engineer" in ev.content_markdown
        assert ev.content_hash


@respx.mock
async def test_scrape_records_failed_evidence_when_browser_unavailable() -> None:
    """Thin Unlocker response + no Browser WS => row marked failed but does not raise."""
    account_id, scan_id, src_id = _make_scan_and_source("acme.com", path="/spa")
    thin_html = "<html><body>Loading...</body></html>"
    respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(200, text=thin_html)
    )

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        account = db.get(Account, account_id)
        src = db.get(Source, src_id)
        events = ScanEventLogger(db, scan.id)
        async with BrightDataRestClient() as client:
            ev = await scrape_source_live(
                db, scan=scan, account=account, src=src, client=client, events=events
            )
        db.commit()
    assert ev is not None
    # Browser fallback unavailable in this test, so we keep the unlocker body
    # but mark it failed via metadata.error.
    assert ev.fetch_method == FetchMethod.unlocker
    assert (ev.metadata_json or {}).get("error") == "thin_unlocker_response_browser_unavailable"


@respx.mock
async def test_scrape_handles_500_gracefully() -> None:
    account_id, scan_id, src_id = _make_scan_and_source("acme.com", path="/down")
    respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(503, text="upstream")
    )
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        account = db.get(Account, account_id)
        src = db.get(Source, src_id)
        events = ScanEventLogger(db, scan.id)
        async with BrightDataRestClient(retry_min_wait=0, retry_max_wait=0) as client:
            ev = await scrape_source_live(
                db, scan=scan, account=account, src=src, client=client, events=events
            )
        db.commit()
    assert ev is not None
    assert ev.fetch_status == FetchStatus.failed
    assert ev.fetch_method == FetchMethod.unlocker
    assert ev.http_status == 503
