"""Structured logging with secret redaction.

Every log line goes through `redact_secrets`, which scrubs anything that
looks like a credential value loaded from settings. Keys and zone names
are still safe to log.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import structlog

from app.config import get_settings

_REDACTED = "***REDACTED***"

# Patterns that should never appear in logs even by accident.
_URL_AUTH_PATTERN = re.compile(r"(https?|wss?)://[^/\s]*:[^@\s]+@", re.IGNORECASE)


def _collect_secret_values() -> list[str]:
    s = get_settings()
    candidates = [
        s.bright_data_api_key,
        s.bright_data_browser_ws,
        s.bright_data_browser_selenium_url,
        s.aiml_api_key,
        s.cognee_api_key,
        s.triggerware_api_key,
        s.speechmatics_api_key,
    ]
    return [c for c in candidates if c and len(c) >= 6]


def _redact_string(value: str, secrets: list[str]) -> str:
    redacted = value
    for secret in secrets:
        if secret and secret in redacted:
            redacted = redacted.replace(secret, _REDACTED)
    redacted = _URL_AUTH_PATTERN.sub(r"\1://" + _REDACTED + "@", redacted)
    return redacted


def redact_secrets(_logger: Any, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    secrets = _collect_secret_values()
    if not secrets:
        # Still apply URL-auth pattern even if no secrets cached.
        pass

    def _walk(obj: Any) -> Any:
        if isinstance(obj, str):
            return _redact_string(obj, secrets)
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_walk(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(_walk(v) for v in obj)
        return obj

    return _walk(event_dict)


def configure_logging() -> None:
    """Configure structlog + stdlib logging for the app.

    Safe to call multiple times.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            redact_secrets,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        force=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()
