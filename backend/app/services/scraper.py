"""Live scraper: Web Unlocker first, Browser API fallback.

Converts fetched HTML to markdown via markdownify so the extractor sees
clean text. One source failing does not fail the scan.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from markdownify import markdownify as md_convert
from sqlalchemy.orm import Session

from app.logging_setup import get_logger
from app.models.account import Account
from app.models.enums import FetchMethod, FetchStatus, ScanStatus
from app.models.evidence import EvidenceDocument
from app.models.scan import Scan
from app.models.source import Source
from app.services.brightdata_client import (
    BrightDataNotConfiguredError,
    BrightDataResponseError,
    BrightDataRestClient,
)
from app.services.browser_client import (
    BrowserClientNotConfiguredError,
    fetch_via_browser_with_timeout,
)
from app.services.scan_events import ScanEventLogger

log = get_logger("scraper")

_THIN_BODY_THRESHOLD = 600
_LIKELY_JS_MARKERS = (
    "Please enable JavaScript",
    "noscript",
    "<script",
    "Loading...",
)


def _looks_thin_or_js_required(body: str) -> bool:
    if not body:
        return True
    if len(body) < _THIN_BODY_THRESHOLD:
        return True
    lower = body.lower()
    return any(marker.lower() in lower for marker in _LIKELY_JS_MARKERS) and len(body) < 4000


def _to_markdown(html_or_text: str) -> str:
    if not html_or_text:
        return ""
    if "<html" not in html_or_text.lower() and "<body" not in html_or_text.lower():
        # Already plain-ish text or markdown.
        return html_or_text
    return md_convert(html_or_text, heading_style="ATX")


def _persist_evidence(
    db: Session,
    *,
    scan: Scan,
    account: Account,
    src: Source,
    body: str,
    fetch_method: FetchMethod,
    http_status: int,
    duration_ms: int,
    error: str | None = None,
) -> EvidenceDocument:
    succeeded = body and not error
    markdown = _to_markdown(body) if succeeded else None
    digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest() if markdown else None

    title: str | None = None
    if markdown:
        first_line = next((ln for ln in markdown.splitlines() if ln.strip()), "")
        title = first_line.lstrip("# ").strip()[:512] or None

    metadata: dict = {"duration_ms": duration_ms}
    if error:
        metadata["error"] = error[:200]

    ev = EvidenceDocument(
        scan_id=scan.id,
        source_id=src.id,
        account_id=account.id,
        url=src.url,
        title=title,
        content_markdown=markdown,
        content_hash=digest,
        fetched_at=datetime.now(UTC),
        fetch_status=FetchStatus.success if succeeded else FetchStatus.failed,
        fetch_method=fetch_method,
        http_status=http_status,
        metadata_json=metadata,
    )
    db.add(ev)
    db.flush()
    return ev


async def scrape_source_live(
    db: Session,
    *,
    scan: Scan,
    account: Account,
    src: Source,
    client: BrightDataRestClient,
    events: ScanEventLogger,
) -> EvidenceDocument | None:
    """Try Web Unlocker, fall back to Browser API on thin/blocked content."""
    # ---- Attempt 1: Web Unlocker ----
    try:
        result = await client.unlock_url(src.url)
    except BrightDataNotConfiguredError:
        raise
    except BrightDataResponseError as exc:
        events.warning(
            "Unlocker call failed",
            target_host=_target_host(src.url),
            http_status=exc.status,
        )
        return _persist_evidence(
            db,
            scan=scan,
            account=account,
            src=src,
            body="",
            fetch_method=FetchMethod.unlocker,
            http_status=exc.status,
            duration_ms=0,
            error=f"unlocker_status_{exc.status}",
        )
    except Exception as exc:  # noqa: BLE001
        events.warning(
            "Unlocker call raised",
            target_host=_target_host(src.url),
            error_type=type(exc).__name__,
        )
        return _persist_evidence(
            db,
            scan=scan,
            account=account,
            src=src,
            body="",
            fetch_method=FetchMethod.unlocker,
            http_status=0,
            duration_ms=0,
            error=type(exc).__name__,
        )

    events.bright_data_call(
        message=f"Unlocker fetched {result.target_host or src.url}",
        phase=ScanStatus.scraping,
        zone=result.zone,
        target_host=result.target_host,
        http_status=result.http_status,
        duration_ms=result.duration_ms,
        content_length=result.content_length,
        tool="bright_data_unlocker",
    )

    if not _looks_thin_or_js_required(result.body):
        return _persist_evidence(
            db,
            scan=scan,
            account=account,
            src=src,
            body=result.body,
            fetch_method=FetchMethod.unlocker,
            http_status=result.http_status,
            duration_ms=result.duration_ms,
        )

    # ---- Attempt 2: Browser API fallback ----
    try:
        bres = await fetch_via_browser_with_timeout(src.url)
    except BrowserClientNotConfiguredError:
        events.warning(
            "browser_api fallback skipped",
            target_host=_target_host(src.url),
            reason="not_configured",
        )
        return _persist_evidence(
            db,
            scan=scan,
            account=account,
            src=src,
            body=result.body,
            fetch_method=FetchMethod.unlocker,
            http_status=result.http_status,
            duration_ms=result.duration_ms,
            error="thin_unlocker_response_browser_unavailable",
        )
    except Exception as exc:  # noqa: BLE001
        events.warning(
            "browser_api fallback failed",
            target_host=_target_host(src.url),
            error_type=type(exc).__name__,
        )
        return _persist_evidence(
            db,
            scan=scan,
            account=account,
            src=src,
            body=result.body,
            fetch_method=FetchMethod.unlocker,
            http_status=result.http_status,
            duration_ms=result.duration_ms,
            error=f"browser_api_{type(exc).__name__}",
        )

    events.bright_data_call(
        message=f"Browser API fetched {bres.target_host or src.url}",
        phase=ScanStatus.scraping,
        target_host=bres.target_host,
        http_status=bres.http_status,
        duration_ms=bres.duration_ms,
        content_length=bres.content_length,
        tool="bright_data_browser",
    )
    return _persist_evidence(
        db,
        scan=scan,
        account=account,
        src=src,
        body=bres.body,
        fetch_method=FetchMethod.browser_api,
        http_status=bres.http_status,
        duration_ms=bres.duration_ms,
    )


def _target_host(url: str) -> str | None:
    from app.services.url_utils import host_of as _h

    return _h(url) or None
