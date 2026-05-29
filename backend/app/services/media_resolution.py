"""Media resolution + content-addressable storage (CAS).

Resolves the cheapest legal/reliable path to a transcript for a source, then
computes a SHA-256 `media_hash` that becomes the durable identity of the audio.
If a `media_asset` already exists for that hash, its transcript is reused and
transcription is skipped entirely — the same episode is never transcribed
twice, even across different accounts.
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
from app.services.media_scan_events import MediaScanEventLogger
from app.services.url_utils import host_of

log = get_logger("media_resolution")


@dataclass
class ResolvedMedia:
    media_asset: MediaAsset
    cache_hit: bool
    resolution_path: str  # existing_transcript | captions | rss_audio | download


def _compute_media_hash(source: MediaSource) -> str:
    """Compute a stable content hash for the source's media.

    In a live deployment this hashes the normalized downloaded audio bytes.
    Here we derive a deterministic hash from the canonical media identity
    (url + duration), which is stable across accounts referencing the same
    episode — exactly the dedup property CAS needs. A real byte-hash slots in
    behind this same function without changing callers.
    """
    canonical = (source.source_url or "").strip().lower()
    duration = source.duration_seconds or 0
    basis = f"{canonical}|{duration}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def resolve_and_hash(
    db: Session,
    *,
    source: MediaSource,
    events: MediaScanEventLogger,
) -> ResolvedMedia:
    """Resolve a source to a (possibly cached) MediaAsset.

    Returns the asset plus whether an existing transcript was reused.
    """
    media_hash = _compute_media_hash(source)

    existing = db.scalar(select(MediaAsset).where(MediaAsset.media_hash == media_hash))
    if existing is not None:
        cache_hit = existing.transcript_id is not None
        source.media_asset_id = existing.id
        db.add(source)
        db.flush()
        if cache_hit:
            events.cache_hit(
                f"reusing cached transcript for {host_of(source.source_url) or 'media'}",
                stage=MediaScanStage.hash_media,
                media_hash_prefix=media_hash[:12],
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
    )
    return ResolvedMedia(media_asset=asset, cache_hit=False, resolution_path=resolution_path)
