"""Verify the structlog redact_secrets processor removes credential values."""

from __future__ import annotations

from app.config import get_settings
from app.logging_setup import redact_secrets


def test_redact_removes_bright_data_api_key() -> None:
    settings = get_settings()
    if not settings.bright_data_api_key:
        return  # nothing to redact in this environment

    sample = {
        "msg": f"Calling Bright Data with key {settings.bright_data_api_key} and zone serp",
    }
    out = redact_secrets(None, "info", sample)
    assert settings.bright_data_api_key not in out["msg"]
    assert "REDACTED" in out["msg"]


def test_redact_strips_url_auth() -> None:
    sample = {
        "url": "wss://brd-customer-hl_xxx-zone-y:supersecret@brd.superproxy.io:9222",
    }
    out = redact_secrets(None, "info", sample)
    assert "supersecret" not in out["url"]
    assert "REDACTED" in out["url"]


def test_redact_handles_nested_structures() -> None:
    settings = get_settings()
    if not settings.aiml_api_key:
        return

    sample = {
        "outer": {
            "inner": [f"key={settings.aiml_api_key}", "harmless"],
        },
    }
    out = redact_secrets(None, "info", sample)
    flat = repr(out)
    assert settings.aiml_api_key not in flat
