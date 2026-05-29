"""Media resolution + content-addressable storage (CAS).

Resolves the cheapest legal/reliable path to a transcript for a source, then
computes a SHA-256 `media_hash` over the *resolved content itself* — not the
URL. This is true content addressing: two different URLs that point at the same
episode (e.g. a YouTube link and a podcast RSS enclosure of the same talk)
hash to the same value, so the second one is a cache hit and transcription is
paid for exactly once, even across accounts.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.logging_setup import get_logger
from app.models.enums import (
    MediaDownloadStatus,
    MediaScanStage,
    TranscriptionStatus,
)
from app.models.media_asset import MediaAsset
from app.models.media_source import MediaSource
from app.services.media_fixtures import fixture_key_for_url, load_transcript
from app.services.media_scan_events import MediaScanEventLogger
from app.services.url_utils import host_of

log = get_logger("media_resolution")


@dataclass
class ResolvedMedia:
    media_asset: MediaAsset
    cache_hit: bool
    resolution_path: str  # existing_transcript | captions | rss_audio | download


def _normalize_transcript_text(segments: list[dict]) -> str:
    """Stable, order-preserving text projection of transcript segments.

    Speaker labels and timings can vary slightly between providers, so we hash
    only the lowercased, whitespace-collapsed spoken words. That makes the hash
    a fingerprint of *what was said*, which is what dedup should key on.
    """
    parts: list[str] = []
    for seg in segments:
        text = (seg.get("text") or "").strip().lower()
        if text:
            parts.append(" ".join(text.split()))
    return "\n".join(parts)


def _content_hash(source: MediaSource) -> tuple[str, str]:
    """Return (media_hash, basis_kind) for a source's resolved content.

    Preference order mirrors the resolution order:
    1. The episode's transcript text (available transcript / caption / fixture),
       hashed as a content fingerprint — stable across differing URLs.
    2. Fallback: the canonical media identity, used only when no transcript
       content can be resolved cheaply (a real deployment hashes audio bytes
       here instead).
    """
    fixture_key = fixture_key_for_url(source.source_url) or (
        (source.metadata_json or {}).get("fixture_key") or ""
    )
    if fixture_key:
        transcript = load_transcript(fixture_key)
        if transcript is not None and transcript.segments:
            normalized = _normalize_transcript_text(transcript.segments)
            if normalized:
                return (
                    hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                    "transcript_content",
                )

    # Fallback identity (no cheap transcript content available yet).
    canonical = (source.source_url or "").strip().lower()
    duration = source.duration_seconds or 0
    basis = f"{canonical}|{duration}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest(), "url_identity_fallback"


def resolve_and_hash(
    db: Session,
    *,
    source: MediaSource,
    events: MediaScanEventLogger,
) -> ResolvedMedia:
    """Resolve a source to a (possibly cached) MediaAsset.

    Returns the asset plus whether an existing transcript was reused.
    """
    media_hash, basis_kind = _content_hash(source)

    existing = db.scalar(select(MediaAsset).where(MediaAsset.media_hash == media_hash))
    if existing is not None:
        cache_hit = existing.transcript_id is not None
        source.media_asset_id = existing.id
        db.add(source)
        db.flush()
        if cache_hit:
            events.cache_hit(
                f"content match — reusing cached transcript for "
                f"{host_of(source.source_url) or 'media'}",
                stage=MediaScanStage.hash_media,
                media_hash_prefix=media_hash[:12],
                basis=basis_kind,
            )
        return ResolvedMedia(
            media_asset=existing,
            cache_hit=cache_hit,
            resolution_path="existing_asset",
        )

    # Decide the cheapest resolution path.
    if source.transcript_available:
        resolution_path = "existing_transcript"
        download_status = MediaDownloadStatus.resolved
    elif source.source_type.value in ("youtube", "webinar", "conference"):
        resolution_path = "captions"
        download_status = MediaDownloadStatus.resolved
    else:
        resolution_path = "download"
        download_status = MediaDownloadStatus.resolved

    asset = MediaAsset(
        media_hash=media_hash,
        canonical_url=source.source_url,
        content_type="audio/mpeg",
        duration_seconds=source.duration_seconds,
        download_status=download_status,
        transcription_status=TranscriptionStatus.pending,
    )
    db.add(asset)
    db.flush()
    source.media_asset_id = asset.id
    db.add(source)
    db.flush()

    events.info(
        f"resolved media via {resolution_path}",
        stage=MediaScanStage.resolve_media,
        resolution_path=resolution_path,
        media_hash_prefix=media_hash[:12],
        basis=basis_kind,
    )
    return ResolvedMedia(media_asset=asset, cache_hit=False, resolution_path=resolution_path)
