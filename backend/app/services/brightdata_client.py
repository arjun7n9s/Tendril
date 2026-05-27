"""Bright Data REST client for SERP and Web Unlocker.

Both use the same endpoint (`https://api.brightdata.com/request`) with a
different `zone`. We use httpx async with tenacity retries so the runner
can fan out concurrent calls when scanning multiple sources.

Refinement #14: async httpx, no sync requests.
Refinement #16: every call's metadata is sanitized before it lands in
scan_events. We never log the bearer token, the embedded URL auth on the
Browser API endpoint, or the full target URL with credentials.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Settings, get_settings
from app.logging_setup import get_logger
from app.services.sanitization import host_of

log = get_logger("brightdata_client")

# A canonical Bright Data test URL that always returns "Welcome to Bright Data!".
BRIGHT_DATA_SMOKE_URL = "https://geo.brdtest.com/welcome.txt"


class BrightDataNotConfiguredError(RuntimeError):
    """Raised when a live call is attempted but credentials are missing."""


class BrightDataResponseError(RuntimeError):
    """Raised when Bright Data returns a non-2xx status."""

    def __init__(self, *, status: int, message: str) -> None:
        super().__init__(f"bright_data_error status={status} message={message}")
        self.status = status
        self.message = message


@dataclass
class BrightDataCallResult:
    body: str
    http_status: int
    duration_ms: int
    zone: str
    target_host: str | None
    content_length: int


class BrightDataRestClient:
    """Async client wrapping Bright Data's `POST /request` endpoint."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
        retry_attempts: int = 3,
        retry_min_wait: float = 1.0,
        retry_max_wait: float = 8.0,
    ) -> None:
        self.settings = settings or get_settings()
        self.timeout = timeout
        self._owned_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._retry_attempts = retry_attempts
        self._retry_min_wait = retry_min_wait
        self._retry_max_wait = retry_max_wait

    async def __aenter__(self) -> "BrightDataRestClient":
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owned_client:
            await self._client.aclose()

    def _require_configured(self) -> None:
        if not self.settings.bright_data_rest_configured():
            raise BrightDataNotConfiguredError(
                "Bright Data REST is not configured (api_key, serp_zone, unlocker_zone)"
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.bright_data_api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

    async def _request_once(self, *, zone: str, url: str) -> BrightDataCallResult:
        payload = {"zone": zone, "url": url, "format": "raw"}
        start = time.monotonic()
        resp = await self._client.post(
            self.settings.bright_data_api_endpoint,
            json=payload,
            headers=self._headers(),
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        body = resp.text or ""
        if resp.status_code >= 400:
            raise BrightDataResponseError(
                status=resp.status_code,
                message=body[:200],
            )
        return BrightDataCallResult(
            body=body,
            http_status=resp.status_code,
            duration_ms=duration_ms,
            zone=zone,
            target_host=host_of(url),
            content_length=len(body),
        )

    async def _request_with_retry(self, *, zone: str, url: str) -> BrightDataCallResult:
        retryer = AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(
                multiplier=1, min=self._retry_min_wait, max=self._retry_max_wait
            ),
            retry=retry_if_exception_type(
                (
                    httpx.TimeoutException,
                    httpx.TransportError,
                    BrightDataResponseError,
                )
            ),
        )
        async for attempt in retryer:
            with attempt:
                return await self._request_once(zone=zone, url=url)
        # tenacity reraises on exhaustion; this line is unreachable
        raise RuntimeError("retry exhausted")  # pragma: no cover

    async def serp_search(self, query: str) -> BrightDataCallResult:
        """Run a Google search via Bright Data SERP zone, return rendered HTML."""
        self._require_configured()
        google_url = f"https://www.google.com/search?{httpx.QueryParams({'q': query})}"
        return await self._request_with_retry(
            zone=self.settings.bright_data_serp_zone, url=google_url
        )

    async def unlock_url(self, url: str) -> BrightDataCallResult:
        """Fetch a public URL via Bright Data Web Unlocker."""
        self._require_configured()
        return await self._request_with_retry(
            zone=self.settings.bright_data_unlocker_zone, url=url
        )

    async def smoke_test(self) -> BrightDataCallResult:
        """Exercise auth + Unlocker against Bright Data's canonical test URL."""
        self._require_configured()
        return await self._request_with_retry(
            zone=self.settings.bright_data_unlocker_zone, url=BRIGHT_DATA_SMOKE_URL
        )
