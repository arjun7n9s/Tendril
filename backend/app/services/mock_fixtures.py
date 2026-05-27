"""Loads mock fixtures and adapts them per account.

Fixture files are templated by account name/domain so the same fixtures
work for any seeded account. Templates use `{account_name}`,
`{account_domain}`, and `{account_handle}` (a lowercased dash-safe slug).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures"


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-") or "company"


@dataclass
class MockSerpResult:
    query: str
    url: str
    title: str
    source_type: str
    rank: int


@dataclass
class MockEvidenceContent:
    url: str
    title: str
    markdown: str


@dataclass
class MockSignalSeed:
    signal_type: str
    title: str
    summary: str
    fact_text: str
    inference_text: str
    recommended_action: str
    evidence_url: str
    observed_at_offset_days: int
    confidence: float


def _account_context(account_name: str, account_domain: str | None) -> dict[str, str]:
    handle = _slugify(account_name)
    domain = account_domain or f"{handle}.example.com"
    return {
        "account_name": account_name,
        "account_domain": domain,
        "account_handle": handle,
    }


def _format(value: str, ctx: dict[str, str]) -> str:
    return value.format(**ctx)


def load_serp_results(account_name: str, account_domain: str | None) -> list[MockSerpResult]:
    raw = json.loads((FIXTURES_ROOT / "mock_serp_results.json").read_text(encoding="utf-8"))
    template = raw.get("_default", {})
    ctx = _account_context(account_name, account_domain)
    out: list[MockSerpResult] = []
    for q in template.get("queries", []):
        formatted_query = _format(q["query"], ctx)
        for r in q.get("results", []):
            out.append(
                MockSerpResult(
                    query=formatted_query,
                    url=_format(r["url"], ctx),
                    title=_format(r["title"], ctx),
                    source_type=r.get("source_type", "other"),
                    rank=int(r.get("rank", 0)),
                )
            )
    return out


_PAGE_KEY_BY_SOURCE_TYPE_AND_SLUG = {
    "careers/senior-data-platform-engineer": "careers_senior_data_platform_engineer",
    "careers/staff-engineer-data-reliability": "careers_staff_engineer_data_reliability",
    "engineering/scaling-our-data-platform": "engineering_scaling_our_data_platform",
    "engineering/our-migration-to-snowflake": "engineering_migration_to_snowflake",
    "data-platform-tools": "github_data_platform_tools",
    "launches-data-product": "news_launches_data_product",
}


def _evidence_key_for_url(url: str) -> str | None:
    """Map a templated mock URL to a fixture filename key."""
    for fragment, key in _PAGE_KEY_BY_SOURCE_TYPE_AND_SLUG.items():
        if fragment in url:
            return key
    return None


def load_evidence_for(url: str) -> MockEvidenceContent | None:
    key = _evidence_key_for_url(url)
    if key is None:
        return None
    path = FIXTURES_ROOT / "mock_scraped_pages" / f"{key}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip() if text else ""
    return MockEvidenceContent(url=url, title=title or "Untitled", markdown=text)


def load_signal_seeds(account_name: str, account_domain: str | None) -> list[MockSignalSeed]:
    raw = json.loads(
        (FIXTURES_ROOT / "mock_extracted_signals.json").read_text(encoding="utf-8")
    )
    seeds: list[dict[str, Any]] = raw.get("_default", [])
    serp = load_serp_results(account_name, account_domain)
    url_by_key = {
        "careers_senior_data_platform_engineer": next(
            (r.url for r in serp if "senior-data-platform-engineer" in r.url), ""
        ),
        "engineering_migration_to_snowflake": next(
            (r.url for r in serp if "migration-to-snowflake" in r.url), ""
        ),
        "github_data_platform_tools": next(
            (r.url for r in serp if "data-platform-tools" in r.url), ""
        ),
        "news_launches_data_product": next(
            (r.url for r in serp if "launches-data-product" in r.url), ""
        ),
    }

    out: list[MockSignalSeed] = []
    for s in seeds:
        url = url_by_key.get(s["evidence_url_key"], "")
        if not url:
            continue
        out.append(
            MockSignalSeed(
                signal_type=s["signal_type"],
                title=s["title"],
                summary=s["summary"],
                fact_text=s["fact_text"],
                inference_text=s["inference_text"],
                recommended_action=s["recommended_action"],
                evidence_url=url,
                observed_at_offset_days=int(s["observed_at_offset_days"]),
                confidence=float(s["confidence"]),
            )
        )
    return out
