"""Bright Data smoke test.

Hits Bright Data's canonical test URL via Web Unlocker to verify
authentication and zone health. Use before running real-target scans
so we don't burn credits chasing a config bug.

Usage:
    uv run python -m scripts.smoke_brightdata
"""

from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.services.brightdata_client import (
    BRIGHT_DATA_SMOKE_URL,
    BrightDataNotConfiguredError,
    BrightDataRestClient,
)


async def main() -> int:
    settings = get_settings()
    print("Smoke target:", BRIGHT_DATA_SMOKE_URL)
    if not settings.bright_data_rest_configured():
        print("Bright Data REST is not configured. Check .env for:")
        print("  BRIGHT_DATA_API_KEY, BRIGHT_DATA_SERP_ZONE, BRIGHT_DATA_UNLOCKER_ZONE")
        return 2

    print("API endpoint:", settings.bright_data_api_endpoint)
    print("SERP zone:", settings.bright_data_serp_zone)
    print("Unlocker zone:", settings.bright_data_unlocker_zone)

    try:
        async with BrightDataRestClient() as client:
            result = await client.smoke_test()
    except BrightDataNotConfiguredError as exc:
        print("not configured:", exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1

    snippet = (result.body or "").strip().splitlines()[0:3]
    print("status:", result.http_status)
    print("duration_ms:", result.duration_ms)
    print("content_length:", result.content_length)
    print("first_lines:", snippet)
    if "Bright Data" in (result.body or ""):
        print("OK: smoke succeeded")
        return 0
    print("WARNING: smoke returned 2xx but body did not contain 'Bright Data'")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
