"""Tests for app.services.sanitization."""

from __future__ import annotations

from app.services.sanitization import host_of, sanitize_metadata, sanitize_url


def test_sanitize_url_strips_userinfo_and_query() -> None:
    url = "wss://brd-customer-hl_xxx-zone-y:supersecret@brd.superproxy.io:9222/path?token=abc"
    out = sanitize_url(url)
    assert "supersecret" not in out
    assert "token=abc" not in out
    assert "brd.superproxy.io" in out


def test_host_of() -> None:
    assert host_of("https://ramp.com/careers") == "ramp.com"
    assert host_of("") is None


def test_sanitize_metadata_drops_forbidden_keys() -> None:
    meta = {
        "host": "ramp.com",
        "authorization": "Bearer abcdef",
        "browser_ws": "wss://user:pass@brd.superproxy.io",
        "nested": {"api_key": "abcdef"},
    }
    out = sanitize_metadata(meta)
    assert out["host"] == "ramp.com"
    assert "Bearer" not in out["authorization"]
    assert "abcdef" not in out["authorization"]
    assert "pass" not in out["browser_ws"]
    assert out["nested"]["api_key"] != "abcdef"


def test_sanitize_metadata_scrubs_bearer_in_strings() -> None:
    meta = {"trace": "calling api with Bearer abcdefgh and zone foo"}
    out = sanitize_metadata(meta)
    assert "abcdefgh" not in out["trace"]
    assert "REDACTED" in out["trace"]
