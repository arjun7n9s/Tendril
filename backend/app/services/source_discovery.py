"""Live source discovery for a scan.

Generates 4-8 targeted queries per account, calls Bright Data SERP, and
returns a ranked, deduplicated list of candidate sources.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.logging_setup import get_logger
from app.models.account import Account
from app.models.enums import ScanStatus, SourceType
from app.models.icp import ICPProfile
from app.models.scan import Scan
from app.models.source import Source
from app.services.brightdata_client import (
    BrightDataNotConfiguredError,
    BrightDataResponseError,
    BrightDataRestClient,
)
from app.services.scan_events import ScanEventLogger
from app.services.serp_parser import parse_serp_html
from app.services.url_utils import (
    ClassifiedUrl,
    classify_url,
    dedupe,
    registered_domain_of,
)

log = get_logger("source_discovery")

# Lower number = higher priority.
_SOURCE_TYPE_PRIORITY: dict[SourceType, int] = {
    SourceType.careers: 1,
    SourceType.blog: 2,
    SourceType.docs: 3,
    SourceType.company_site: 4,
    SourceType.github: 5,
    SourceType.news: 6,
    SourceType.review: 7,
    SourceType.serp_result: 8,
    SourceType.public_profile: 9,
    SourceType.other: 10,
}


@dataclass
class DiscoveryQuery:
    text: str
    purpose: str  # human-readable label for the scan_events trace


def _take(items: list[str], n: int) -> str:
    """Take up to `n` items and join them with spaces, lowercased."""
    return " ".join((items or [])[:n])


def build_queries(account: Account, icp: ICPProfile | None) -> list[DiscoveryQuery]:
    name = account.name
    domain = account.domain or ""
    tech_keywords = (icp.tech_keywords_json or []) if icp else []
    competitor_keywords = (icp.competitor_keywords_json or []) if icp else []
    pain_keywords = (icp.pain_keywords_json or []) if icp else []

    tech_phrase = _take(tech_keywords, 3) or "data platform"
    pain_phrase = _take(pain_keywords, 2)
    comp_phrase = _take(competitor_keywords, 2)

    queries: list[DiscoveryQuery] = []

    queries.append(
        DiscoveryQuery(
            text=f"{name} careers {tech_phrase}".strip(),
            purpose="careers_with_tech",
        )
    )
    queries.append(
        DiscoveryQuery(
            text=f"{name} engineering blog {tech_phrase}".strip(),
            purpose="engineering_blog",
        )
    )
    queries.append(
        DiscoveryQuery(
            text=f"{name} migration {tech_phrase}".strip(),
            purpose="migration_evidence",
        )
    )
    if pain_phrase:
        queries.append(
            DiscoveryQuery(
                text=f"{name} {pain_phrase}",
                purpose="pain_signal",
            )
        )
    if comp_phrase:
        queries.append(
            DiscoveryQuery(
                text=f"{name} {comp_phrase}",
                purpose="competitor_signal",
            )
        )
    queries.append(
        DiscoveryQuery(
            text=f"{name} press release",
            purpose="press_news",
        )
    )
    if domain:
        queries.append(
            DiscoveryQuery(
                text=f"site:{domain} {tech_phrase}".strip(),
                purpose="site_search",
            )
        )
    queries.append(
        DiscoveryQuery(
            text=f"site:github.com {name} {tech_phrase}".strip(),
            purpose="github_search",
        )
    )
    return queries[:8]


def _rank_key(c: ClassifiedUrl, *, account_rd: str) -> tuple[int, int]:
    """Sort key: company-domain pages first, then careers/blog/docs/etc."""
    same_domain_bonus = 0 if c.registered_domain == account_rd else 1
    type_priority = _SOURCE_TYPE_PRIORITY.get(c.source_type, 99)
    return (same_domain_bonus, type_priority)


async def discover_sources_live(
    db: Session,
    *,
    scan: Scan,
    account: Account,
    icp: ICPProfile | None,
    client: BrightDataRestClient,
    events: ScanEventLogger,
    max_sources: int = 6,
) -> list[Source]:
    """Run real SERP queries and persist candidate Source rows.

    The returned list contains all created sources, with `selected_for_scrape`
    flagged on the top `max_sources` after ranking + dedup.
    """
    queries = build_queries(account, icp)
    account_rd = registered_domain_of(f"https://{account.domain}") if account.domain else ""

    classified: list[tuple[ClassifiedUrl, DiscoveryQuery]] = []
    serp_call_count = 0
    serp_hit_count = 0

    for q in queries:
        try:
            result = await client.serp_search(q.text)
        except BrightDataNotConfiguredError:
            raise
        except BrightDataResponseError as exc:
            events.warning(
                "SERP call failed",
                query_purpose=q.purpose,
                http_status=exc.status,
            )
            continue
        except Exception as exc:  # noqa: BLE001
            events.warning(
                "SERP call raised",
                query_purpose=q.purpose,
                error_type=type(exc).__name__,
            )
            continue

        serp_call_count += 1
        events.bright_data_call(
            message=f"SERP returned {result.content_length} bytes for '{q.purpose}'",
            phase=ScanStatus.discovering,
            zone=result.zone,
            target_host=result.target_host,
            http_status=result.http_status,
            duration_ms=result.duration_ms,
            content_length=result.content_length,
            tool="bright_data_serp",
            query_purpose=q.purpose,
        )

        hits = parse_serp_html(result.body)
        for h in hits[:10]:  # cap per-query SERP hits
            classified_url = classify_url(h.url, account_domain=account.domain)
            if classified_url is None:
                continue
            classified.append((classified_url, q))
            serp_hit_count += 1

    deduped: list[ClassifiedUrl] = dedupe([c for c, _q in classified])
    query_by_canonical: dict[str, DiscoveryQuery] = {}
    for c, q in classified:
        query_by_canonical.setdefault(c.canonical, q)

    deduped.sort(key=lambda c: _rank_key(c, account_rd=account_rd))

    sources: list[Source] = []
    for idx, c in enumerate(deduped):
        q = query_by_canonical.get(c.canonical)
        src = Source(
            scan_id=scan.id,
            account_id=account.id,
            url=c.canonical,
            source_type=c.source_type,
            discovery_query=q.text if q else None,
            rank=idx + 1,
            selected_for_scrape=False,
        )
        db.add(src)
        sources.append(src)
    db.flush()

    selected = 0
    for src in sources:
        if selected >= max_sources:
            break
        src.selected_for_scrape = True
        db.add(src)
        selected += 1
    db.flush()

    events.info(
        "discovery summary",
        queries_run=serp_call_count,
        serp_hits=serp_hit_count,
        candidate_count=len(deduped),
        selected_count=selected,
    )

    return sources
