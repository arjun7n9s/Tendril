"""Media source discovery.

Finds public spoken sources for an account. In `mock` mode it loads templated
fixtures so the pipeline runs offline. In `live` mode it issues targeted SERP
queries through Bright Data (YouTube, podcast, earnings, webinar) and parses
candidate URLs. Live discovery degrades gracefully to whatever it can find.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.logging_setup import get_logger
from app.models.account import Account
from app.models.enums import MediaScanStage, MediaSourceStatus, MediaSourceType
from app.models.icp import ICPProfile
from app.models.media_scan_job import MediaScanJob
from app.models.media_source import MediaSource
from app.services.media_fixtures import fixture_key_for_url, load_media_sources
from app.services.media_scan_events import MediaScanEventLogger

log = get_logger("media_discovery")


@dataclass
class MediaDiscoveryQuery:
    text: str
    purpose: str
    source_type: MediaSourceType


def build_media_queries(account: Account, icp: ICPProfile | None) -> list[MediaDiscoveryQuery]:
    name = account.name
    tech = ", ".join((icp.tech_keywords_json or [])[:3]) if icp else ""
    queries = [
        MediaDiscoveryQuery(
            # site:youtube.com/watch biases SERP toward *individual videos*
            # (reliably audio-extractable) rather than channels or playlists.
            text=f"site:youtube.com/watch {name} engineering {tech}".strip(),
            purpose="youtube_engineering",
            source_type=MediaSourceType.youtube,
        ),
        MediaDiscoveryQuery(
            text=f"site:youtube.com/watch {name} podcast interview data".strip(),
            purpose="youtube_podcast",
            source_type=MediaSourceType.youtube,
        ),
        MediaDiscoveryQuery(
            text=f"site:youtube.com/watch {name} conference talk keynote".strip(),
            purpose="youtube_conference",
            source_type=MediaSourceType.conference,
        ),
        MediaDiscoveryQuery(
            text=f"{name} engineering podcast episode {tech}".strip(),
            purpose="podcast_episode",
            source_type=MediaSourceType.podcast,
        ),
    ]
    return queries


def discover_sources_mock(
    db: Session,
    *,
    job: MediaScanJob,
    account: Account,
    events: MediaScanEventLogger,
) -> list[MediaSource]:
    """Create MediaSource rows from templated fixtures."""
    fixtures = load_media_sources(account.name, account.domain)
    now = datetime.now(UTC)
    created: list[MediaSource] = []
    for f in fixtures:
        try:
            stype = MediaSourceType(f.source_type)
        except ValueError:
            stype = MediaSourceType.other
        src = MediaSource(
            account_id=account.id,
            media_scan_job_id=job.id,
            source_url=f.source_url,
            source_type=stype,
            title=f.title,
            description=f.description,
            publisher=f.publisher,
            speaker_names_json=f.speaker_names,
            published_at=now + timedelta(days=f.published_offset_days),
            duration_seconds=f.duration_seconds,
            transcript_available=f.transcript_available,
            discovery_query=f.discovery_query,
            status=MediaSourceStatus.discovered,
            metadata_json={"fixture_key": f.fixture_key, "source": "mock"},
        )
        db.add(src)
        created.append(src)
    db.flush()
    events.bright_data_call(
        f"discovered {len(created)} candidate conversations",
        stage=MediaScanStage.discover_sources,
        tool="mock_media_serp",
        candidate_count=len(created),
    )
    return created


async def discover_sources_live(
    db: Session,
    *,
    job: MediaScanJob,
    account: Account,
    icp: ICPProfile | None,
    events: MediaScanEventLogger,
) -> list[MediaSource]:
    """Live discovery via Bright Data SERP.

    Issues media-focused queries and parses candidate URLs. If Bright Data is
    unavailable or returns nothing usable, returns an empty list and the runner
    falls back to mock discovery so a demo never dead-ends.
    """
    from app.services.brightdata_client import (
        BrightDataNotConfiguredError,
        BrightDataRestClient,
    )
    from app.services.serp_parser import parse_serp_html

    queries = build_media_queries(account, icp)
    created: list[MediaSource] = []
    seen: set[str] = set()

    try:
        async with BrightDataRestClient() as client:
            for q in queries:
                try:
                    result = await client.serp_search(q.text)
                except BrightDataNotConfiguredError:
                    raise
                except Exception as exc:
                    events.warning(
                        "media SERP query failed",
                        purpose=q.purpose,
                        error_type=type(exc).__name__,
                    )
                    continue

                events.bright_data_call(
                    f"SERP returned {result.content_length} bytes for '{q.purpose}'",
                    stage=MediaScanStage.discover_sources,
                    zone=result.zone,
                    target_host=result.target_host,
                    http_status=result.http_status,
                    duration_ms=result.duration_ms,
                    tool="bright_data_serp",
                )

                for hit in parse_serp_html(result.body)[:5]:
                    if hit.url in seen or not _looks_like_media(hit.url):
                        continue
                    seen.add(hit.url)
                    src = MediaSource(
                        account_id=account.id,
                        media_scan_job_id=job.id,
                        source_url=hit.url,
                        source_type=q.source_type,
                        title=hit.title,
                        discovery_query=q.text,
                        transcript_available=False,
                        status=MediaSourceStatus.discovered,
                        metadata_json={
                            "fixture_key": fixture_key_for_url(hit.url) or "",
                            "source": "live",
                        },
                    )
                    db.add(src)
                    created.append(src)
    except BrightDataNotConfiguredError:
        events.warning("Bright Data not configured for media discovery")
        return []

    db.flush()
    return created


_MEDIA_HOST_MARKERS = (
    "youtube.com/watch",
    "youtu.be/",
    "podcasts.apple.com",
    "soundcloud.com/",
    "vimeo.com/",
    ".mp3",
    ".m4a",
    "buzzsprout.com",
    "libsyn.com",
    "simplecast.com",
    "megaphone.fm",
    "transistor.fm",
    "/episode",
)

# Reject these even if a marker matches: channels, playlists, and text-only
# transcript pages aren't single audio items we can extract + transcribe.
_MEDIA_REJECT_MARKERS = (
    "youtube.com/@",
    "youtube.com/channel",
    "youtube.com/c/",
    "youtube.com/playlist",
    "/earnings/transcripts",
    "earnings-transcript",
    "call-transcripts",
)


def _looks_like_media(url: str) -> bool:
    lower = url.lower()
    if any(bad in lower for bad in _MEDIA_REJECT_MARKERS):
        return False
    return any(marker in lower for marker in _MEDIA_HOST_MARKERS)
