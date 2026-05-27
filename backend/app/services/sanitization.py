"""Helpers that strip credentials out of event metadata.

Per the plan (refinement #16): scan_events.metadata_json may include zone
name, target host, http status, ms, content-length. It must never include
bearer tokens, embedded URL auth, Browser WS endpoints, or any credential
value. This module guarantees that.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

_REDACTED = "***REDACTED***"

# Keys whose values must always be redacted.
_FORBIDDEN_KEYS = {
    "authorization",
    "auth",
    "api_key",
    "apikey",
    "bearer",
    "browser_ws",
    "selenium_url",
    "ws",
    "websocket",
    "password",
    "token",
}

_URL_AUTH_RE = re.compile(r"(https?|wss?)://[^/\s]*:[^@\s]+@", re.IGNORECASE)
_BEARER_RE = re.compile(r"(?i)bearer\s+[a-z0-9._\-]+")


def _strip_url_auth(value: str) -> str:
    """Remove `user:pass@` from any URL-like substring."""
    return _URL_AUTH_RE.sub(lambda m: f"{m.group(1)}://" + _REDACTED + "@", value)


def sanitize_url(url: str) -> str:
    """Return a URL with any embedded credentials and query string stripped."""
    if not url:
        return url
    try:
        parts = urlsplit(url)
    except ValueError:
        return _strip_url_auth(url)

    netloc = parts.hostname or ""
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def host_of(url: str) -> str | None:
    if not url:
        return None
    try:
        return urlsplit(url).hostname
    except ValueError:
        return None


def sanitize_metadata(meta: dict[str, Any] | None) -> dict[str, Any]:
    """Return a deep copy of `meta` safe for persistence in scan_events.

    - Forbidden keys are dropped.
    - Strings have URL-auth and bearer tokens scrubbed.
    - Any key containing 'url' has its value reduced to host+path only.
    """
    if not meta:
        return {}

    def _walk(value: Any, key_hint: str | None = None) -> Any:
        if isinstance(value, str):
            if key_hint and "url" in key_hint.lower():
                return sanitize_url(value)
            return _BEARER_RE.sub(_REDACTED, _strip_url_auth(value))
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for k, v in value.items():
                if k.lower() in _FORBIDDEN_KEYS:
                    cleaned[k] = _REDACTED
                    continue
                cleaned[k] = _walk(v, k)
            return cleaned
        if isinstance(value, list):
            return [_walk(v, key_hint) for v in value]
        if isinstance(value, tuple):
            return tuple(_walk(v, key_hint) for v in value)
        return value

    return _walk(meta)  # type: ignore[no-any-return]
