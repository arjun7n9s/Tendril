"""Bright Data Browser API fallback (Playwright over CDP).

Only used when Web Unlocker returns thin or blocked content. The
Playwright import is deferred so unit tests don't pay its startup cost.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from app.config import Settings, get_settings
from app.logging_setup import get_logger

log = get_logger("browser_client")


@dataclass
class BrowserFetchResult:
    body: str
    http_status: int
    duration_ms: int
    target_host: str | None
    content_length: int


class BrowserClientNotConfiguredError(RuntimeError):
    pass


async def fetch_via_browser(
    url: str, *, settings: Settings | None = None, timeout_ms: int = 90_000
) -> BrowserFetchResult:
    """Connect to Bright Data Scraping Browser via WebSocket and fetch URL."""
    settings = settings or get_settings()
    if not settings.bright_data_browser_ws:
        raise BrowserClientNotConfiguredError("BRIGHT_DATA_BROWSER_WS not set")

    # Imported lazily so test runs don't pay the import cost.
    from playwright.async_api import async_playwright  # type: ignore

    from app.services.url_utils import host_of

    start = time.monotonic()
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(settings.bright_data_browser_ws)
        try:
            page = await browser.new_page()
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            except Exception as exc:  # noqa: BLE001
                # Some pages never reach networkidle; fall back to domcontentloaded.
                log.info("browser_client.networkidle_failed", error=str(exc))
                response = await page.goto(
                    url, wait_until="domcontentloaded", timeout=timeout_ms
                )
            content = await page.content()
            status = response.status if response is not None else 200
        finally:
            await browser.close()

    duration_ms = int((time.monotonic() - start) * 1000)
    return BrowserFetchResult(
        body=content,
        http_status=status,
        duration_ms=duration_ms,
        target_host=host_of(url),
        content_length=len(content),
    )


async def fetch_via_browser_with_timeout(
    url: str, *, settings: Settings | None = None, hard_timeout_seconds: float = 120.0
) -> BrowserFetchResult:
    return await asyncio.wait_for(
        fetch_via_browser(url, settings=settings),
        timeout=hard_timeout_seconds,
    )
