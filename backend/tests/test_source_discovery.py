"""Live source discovery tests with respx-mocked Bright Data endpoint."""

from __future__ import annotations

import httpx
import pytest
import respx
from sqlalchemy import select

from app.config import get_settings
from app.db import get_sessionmaker
from app.models.account import Account
from app.models.enums import AccountStatus, ScanMode, ScanStatus, SourceType
from app.models.icp import ICPProfile
from app.models.scan import Scan
from app.services.brightdata_client import BrightDataRestClient
from app.services.scan_events import ScanEventLogger
from app.services.source_discovery import build_queries, discover_sources_live


@pytest.fixture(autouse=True)
def _live_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-bd-key")
    monkeypatch.setenv("BRIGHT_DATA_API_ENDPOINT", "https://api.brightdata.com/request")
    monkeypatch.setenv("BRIGHT_DATA_SERP_ZONE", "test-serp")
    monkeypatch.setenv("BRIGHT_DATA_UNLOCKER_ZONE", "test-unlocker")
    get_settings.cache_clear()


def test_build_queries_uses_account_and_icp() -> None:
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        status=AccountStatus.target,
    )
    icp = ICPProfile(
        name="default",
        industries_json=["fintech"],
        company_sizes_json=[],
        regions_json=[],
        target_roles_json=[],
        tech_keywords_json=["Kafka", "Snowflake", "dbt"],
        pain_keywords_json=["reliability"],
        competitor_keywords_json=["fivetran"],
    )
    qs = build_queries(account, icp)
    texts = [q.text for q in qs]
    assert any("Acme careers" in t and "Kafka" in t for t in texts)
    assert any("site:acme.com" in t for t in texts)
    assert any("site:github.com" in t and "Acme" in t for t in texts)
    assert any("reliability" in t for t in texts)
    assert any("fivetran" in t for t in texts)
    assert len(qs) <= 8


def _serp_html_for(*urls_with_titles: tuple[str, str]) -> str:
    parts = []
    for url, title in urls_with_titles:
        parts.append(
            f"<div class='g'><a href='{url}'><h3>{title}</h3></a></div>"
        )
    return "<html><body>" + "".join(parts) + "</body></html>"


@respx.mock
async def test_discover_sources_live_persists_ranked_dedup(seed_csv_path) -> None:
    SessionLocal = get_sessionmaker()

    # Seed a single account directly for isolation.
    with SessionLocal() as db:
        account = Account(
            name="Acme",
            domain="acme.com",
            industry="fintech",
            company_size="201-500",
            status=AccountStatus.target,
        )
        db.add(account)
        icp = ICPProfile(
            name="default",
            industries_json=["fintech"],
            tech_keywords_json=["kafka", "snowflake"],
        )
        db.add(icp)
        db.commit()
        scan = Scan(
            account_id=account.id,
            scan_type="account_watchtower",
            status=ScanStatus.discovering,
            mode=ScanMode.live,
            progress_percent=15,
        )
        db.add(scan)
        db.commit()
        account_id = account.id
        scan_id = scan.id

    # Every SERP query returns the same 4 results, including duplicates and
    # a Google-redirect form so we exercise dedup + redirect parsing.
    serp_html = _serp_html_for(
        ("https://acme.com/careers/engineer", "Engineer at Acme"),
        ("/url?q=https%3A%2F%2Facme.com%2Fblog%2Fscaling", "Scaling our data platform"),
        ("https://github.com/acme/data-tools", "acme/data-tools"),
        # duplicate of the first via a tracking param; should dedup.
        ("https://acme.com/careers/engineer?utm_source=google", "dup"),
        # blocked: should be filtered.
        ("https://www.google.com/search?q=acme", "Google"),
        # blocked: linkedin.
        ("https://linkedin.com/company/acme", "LinkedIn"),
    )

    respx.post("https://api.brightdata.com/request").mock(
        return_value=httpx.Response(200, text=serp_html)
    )

    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        account = db.get(Account, account_id)
        icp = db.scalars(select(ICPProfile).where(ICPProfile.name == "default")).first()
        events = ScanEventLogger(db, scan.id)
        async with BrightDataRestClient() as client:
            sources = await discover_sources_live(
                db,
                scan=scan,
                account=account,
                icp=icp,
                client=client,
                events=events,
                max_sources=4,
            )
        db.commit()

        urls = [s.url for s in sources]
        # Dedup: the utm version should not appear separately.
        assert "https://acme.com/careers/engineer" in urls
        assert all("utm_source" not in u for u in urls)
        # Blocked hosts removed.
        assert all("google.com/search" not in u for u in urls)
        assert all("linkedin.com" not in u for u in urls)
        # Ranking: company-domain pages first.
        first = sources[0]
        assert first.url.startswith("https://acme.com")
        # Source type classification.
        types = {s.source_type for s in sources}
        # SQLAlchemy may return enum values or strings; normalize.
        type_values = {
            t.value if hasattr(t, "value") else t for t in types
        }
        assert SourceType.careers.value in type_values or SourceType.company_site.value in type_values
        # Selection cap.
        selected = [s for s in sources if s.selected_for_scrape]
        assert len(selected) <= 4

        # Event trace recorded SERP calls and a summary.
        events_rows = list(scan.events)
        assert any(
            getattr(e.event_type, "value", str(e.event_type)) == "bright_data_call"
            for e in events_rows
        )
