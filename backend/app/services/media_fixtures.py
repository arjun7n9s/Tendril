"""Loads mock media fixtures, templated per account.

Mirrors `mock_fixtures.py` for the media pipeline so the durable runner can
execute end to end without spending any provider credits. Templates use
`{account_name}`, `{account_domain}`, and `{account_handle}`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures"


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-") or "company"


def _account_context(account_name: str, account_domain: str | None) -> dict[str, str]:
    handle = _slugify(account_name)
    return {
        "account_name": account_name,
        "account_domain": account_domain or f"{handle}.example.com",
        "account_handle": handle,
    }


def _format(value: str, ctx: dict[str, str]) -> str:
    return value.format(**ctx)


@dataclass
class MockMediaSource:
    source_url: str
    source_type: str
    title: str
    description: str
    publisher: str
    speaker_names: list[str]
    published_offset_days: int
    duration_seconds: int
    transcript_available: bool
    discovery_query: str
    fixture_key: str


@dataclass
class MockTranscript:
    provider: str
    language: str
    confidence: float
    segments: list[dict[str, Any]] = field(default_factory=list)


# Maps a source URL fragment to the transcript/signal fixture key.
_FIXTURE_KEY_FRAGMENTS = (
    "eng-podcast",
    "earnings-q3",
    "webinar-reliability",
    "keynote-2024",
)


def fixture_key_for_url(url: str) -> str | None:
    for fragment in _FIXTURE_KEY_FRAGMENTS:
        if fragment in url:
            return fragment
    return None


def load_media_sources(account_name: str, account_domain: str | None) -> list[MockMediaSource]:
    raw = json.loads((FIXTURES_ROOT / "mock_media_sources.json").read_text(encoding="utf-8"))
    ctx = _account_context(account_name, account_domain)
    out: list[MockMediaSource] = []
    for item in raw.get("_default", []):
        url = _format(item["source_url"], ctx)
        out.append(
            MockMediaSource(
                source_url=url,
                source_type=item.get("source_type", "other"),
                title=_format(item.get("title", ""), ctx),
                description=_format(item.get("description", ""), ctx),
                publisher=item.get("publisher", ""),
                speaker_names=list(item.get("speaker_names", [])),
                published_offset_days=int(item.get("published_offset_days", 0)),
                duration_seconds=int(item.get("duration_seconds", 0)),
                transcript_available=bool(item.get("transcript_available", False)),
                discovery_query=_format(item.get("discovery_query", ""), ctx),
                fixture_key=fixture_key_for_url(url) or "",
            )
        )
    return out


def load_transcript(fixture_key: str) -> MockTranscript | None:
    raw = json.loads((FIXTURES_ROOT / "mock_transcripts.json").read_text(encoding="utf-8"))
    item = raw.get(fixture_key)
    if not item:
        return None
    return MockTranscript(
        provider=item.get("provider", "mock"),
        language=item.get("language", "en"),
        confidence=float(item.get("confidence", 0.9)),
        segments=list(item.get("segments", [])),
    )


def load_conversation_signals(fixture_key: str) -> list[dict[str, Any]]:
    raw = json.loads(
        (FIXTURES_ROOT / "mock_conversation_signals.json").read_text(encoding="utf-8")
    )
    return list(raw.get("_default", {}).get(fixture_key, []))
