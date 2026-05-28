"""Tests for the ScanEvent logger and message sanitizer."""

from __future__ import annotations

from app.db import get_sessionmaker
from app.models.account import Account
from app.models.enums import AccountStatus, ScanEventType, ScanMode, ScanStatus
from app.models.scan import Scan
from app.services.scan_events import ScanEventLogger, _sanitize_message


def test_sanitize_message_replaces_full_url_with_host() -> None:
    msg = "fetched https://ramp.com/blog/post-with-secret?token=abc123"
    out = _sanitize_message(msg)
    assert "token=abc123" not in out
    assert "ramp.com" in out
    assert "/blog/" not in out


def test_sanitize_message_strips_websocket_credentials() -> None:
    msg = "Connecting to wss://brd-customer-x-zone-y:secretpass@brd.superproxy.io:9222"
    out = _sanitize_message(msg)
    assert "secretpass" not in out
    assert "brd.superproxy.io" in out


def test_sanitize_message_handles_multiple_urls() -> None:
    msg = "compared https://acme.com/x and https://other.com/y"
    out = _sanitize_message(msg)
    assert "/x" not in out and "/y" not in out
    assert "acme.com" in out and "other.com" in out


def test_sanitize_message_passthrough_for_plain_text() -> None:
    msg = "extracted 3 valid signals"
    assert _sanitize_message(msg) == msg


def _seed_scan() -> str:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = Account(name="Acme", domain="acme.com", status=AccountStatus.target)
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
        return scan.id


def test_logger_writes_sanitized_message() -> None:
    scan_id = _seed_scan()
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        events = ScanEventLogger(db, scan_id)
        events.bright_data_call(
            "Unlocker fetched https://acme.com/careers/sse?token=abc",
            phase=ScanStatus.scraping,
            zone="test-unlocker",
        )
        db.commit()
        scan = db.get(Scan, scan_id)
        latest = scan.events[-1]
        assert "token=abc" not in latest.message
        assert "/careers/sse" not in latest.message
        assert "acme.com" in latest.message
        assert latest.event_type == ScanEventType.bright_data_call


def test_logger_resumes_sequence_across_instances() -> None:
    scan_id = _seed_scan()
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        first = ScanEventLogger(db, scan_id)
        first.info("first")
        first.info("second")
        db.commit()
    with SessionLocal() as db:
        second = ScanEventLogger(db, scan_id)
        second.info("third")
        db.commit()
        scan = db.get(Scan, scan_id)
        seqs = [e.sequence for e in scan.events]
        assert seqs == [1, 2, 3]
