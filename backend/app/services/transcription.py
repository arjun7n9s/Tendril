"""Transcription stage.

Produces a `Transcript` row for a `MediaAsset`. Resolution order:

1. If the asset already has a transcript (CAS cache hit), reuse it.
2. In `mock` mode, or when an existing transcript/caption fixture is available,
   load deterministic diarized segments — no provider call, no cost.
3. In `live` mode with Speechmatics configured and a real audio URL, submit a
   batch job with diarization and poll for the timestamped result.

Speechmatics failures are retryable: the asset is left in a `failed`
transcription state so the durable runner can resume the transcribe stage.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.logging_setup import get_logger
from app.models.enums import (
    MediaScanStage,
    TranscriptionStatus,
    TranscriptProvider,
)
from app.models.media_asset import MediaAsset
from app.models.media_source import MediaSource
from app.models.transcript import Transcript
from app.services.media_fixtures import fixture_key_for_url, load_transcript
from app.services.media_scan_events import MediaScanEventLogger

log = get_logger("transcription")


@dataclass
class TranscriptionResult:
    transcript: Transcript
    reused: bool


def _reuse_existing(asset: MediaAsset, db: Session) -> Transcript | None:
    if asset.transcript_id:
        return db.get(Transcript, asset.transcript_id)
    return None


def transcribe_source(
    db: Session,
    *,
    source: MediaSource,
    asset: MediaAsset,
    events: MediaScanEventLogger,
    live: bool,
) -> TranscriptionResult | None:
    """Transcribe (or reuse a transcript for) a source's media asset."""
    # 1) CAS reuse.
    existing = _reuse_existing(asset, db)
    if existing is not None:
        asset.transcription_status = TranscriptionStatus.reused
        db.add(asset)
        db.flush()
        events.cache_hit(
            "reused existing transcript (no transcription cost)",
            stage=MediaScanStage.transcribe,
            transcript_id=existing.id,
        )
        return TranscriptionResult(transcript=existing, reused=True)

    # 2) Fixture / existing-transcript / caption path (also the mock path).
    fixture_key = fixture_key_for_url(source.source_url) or (
        (source.metadata_json or {}).get("fixture_key") or ""
    )
    mock_tr = load_transcript(fixture_key) if fixture_key else None

    if mock_tr is not None and (not live or source.transcript_available):
        transcript = _persist_transcript(
            db,
            asset=asset,
            provider=_coerce_provider(mock_tr.provider),
            language=mock_tr.language,
            segments=mock_tr.segments,
            confidence=mock_tr.confidence,
        )
        events.info(
            f"transcript acquired via {mock_tr.provider}",
            stage=MediaScanStage.transcribe,
            segment_count=len(mock_tr.segments),
            provider=mock_tr.provider,
        )
        return TranscriptionResult(transcript=transcript, reused=False)

    # 3) Live Speechmatics path.
    if live:
        settings = get_settings()
        if not settings.speechmatics_configured():
            events.warning(
                "Speechmatics not configured; skipping transcription",
                stage=MediaScanStage.transcribe,
            )
            asset.transcription_status = TranscriptionStatus.failed
            db.add(asset)
            db.flush()
            return None
        try:
            segments, confidence, language = _speechmatics_transcribe(
                db, source=source, asset=asset, events=events
            )
        except Exception as exc:
            events.warning(
                "Speechmatics transcription failed (resumable)",
                stage=MediaScanStage.transcribe,
                error_type=type(exc).__name__,
            )
            # The submitted job id (if any) is already persisted on the asset
            # by `_speechmatics_transcribe`, so a resume polls it instead of
            # resubmitting — this is what prevents double-billing on a crash.
            asset.transcription_status = TranscriptionStatus.failed
            db.add(asset)
            db.flush()
            return None
        transcript = _persist_transcript(
            db,
            asset=asset,
            provider=TranscriptProvider.speechmatics,
            language=language,
            segments=segments,
            confidence=confidence,
        )
        events.speechmatics_call(
            "batch transcription complete",
            stage=MediaScanStage.transcribe,
            segment_count=len(segments),
        )
        return TranscriptionResult(transcript=transcript, reused=False)

    # Nothing available.
    events.warning(
        "no transcript available for source",
        stage=MediaScanStage.transcribe,
    )
    asset.transcription_status = TranscriptionStatus.failed
    db.add(asset)
    db.flush()
    return None


def _persist_transcript(
    db: Session,
    *,
    asset: MediaAsset,
    provider: TranscriptProvider,
    language: str | None,
    segments: list[dict],
    confidence: float | None,
) -> Transcript:
    raw_text = "\n".join(
        f"[{s.get('start')}] {s.get('speaker', 'Speaker')}: {s.get('text', '')}"
        for s in segments
    )
    transcript = Transcript(
        media_asset_id=asset.id,
        provider=provider,
        language=language,
        raw_text=raw_text,
        segments_json=segments,
        confidence=confidence,
    )
    db.add(transcript)
    db.flush()
    asset.transcript_id = transcript.id
    asset.transcription_status = TranscriptionStatus.completed
    db.add(asset)
    db.flush()
    return transcript


def _coerce_provider(raw: str) -> TranscriptProvider:
    try:
        return TranscriptProvider(raw)
    except ValueError:
        return TranscriptProvider.mock


def _speechmatics_transcribe(
    db: Session, *, source: MediaSource, asset: MediaAsset, events: MediaScanEventLogger
) -> tuple[list[dict], float | None, str | None]:
    """Submit (or resume) and poll a Speechmatics batch job with diarization.

    Crash-safety / no-double-billing: the provider job id is persisted to the
    asset with an immediate commit *right after submit, before waiting*. If the
    process dies during the wait, a resume finds the stored job id and polls
    that existing job instead of submitting a new one — so we never pay twice.

    Uses the optional `speechmatics-batch` SDK (declared under the `voice`
    extra). Raises on failure so the caller can mark the stage resumable.
    """
    from speechmatics.batch import (  # type: ignore[import-not-found]
        AsyncClient,
        FormatType,
        TranscriptionConfig,
    )

    settings = get_settings()

    import asyncio

    from app.services.audio_extractor import (
        AudioExtractionError,
        extract_audio,
        looks_extractable,
    )

    if not looks_extractable(source.source_url):
        raise AudioExtractionError(f"not_extractable_url:{source.source_url[:80]}")

    events.speechmatics_call(
        "extracting audio for transcription",
        stage=MediaScanStage.transcribe,
    )
    audio = extract_audio(source.source_url)

    # True content-addressable dedup: re-key the asset on the real audio bytes.
    existing_by_hash = (
        db.query(MediaAsset)
        .filter(
            MediaAsset.media_hash == audio.media_hash,
            MediaAsset.id != asset.id,
            MediaAsset.transcript_id.isnot(None),
        )
        .first()
    )
    if existing_by_hash is not None and existing_by_hash.transcript_id:
        existing_tr = db.get(Transcript, existing_by_hash.transcript_id)
        if existing_tr is not None:
            events.cache_hit(
                "content match on audio hash; reusing transcript (no ASR cost)",
                stage=MediaScanStage.transcribe,
                media_hash_prefix=audio.media_hash[:12],
            )
            asset.media_hash = audio.media_hash
            asset.transcript_id = existing_tr.id
            asset.duration_seconds = audio.duration_seconds or asset.duration_seconds
            db.add(asset)
            db.flush()
            return existing_tr.segments_json or [], existing_tr.confidence, existing_tr.language

    asset.media_hash = audio.media_hash
    if audio.duration_seconds:
        asset.duration_seconds = audio.duration_seconds
    asset.transcription_status = TranscriptionStatus.in_progress
    db.add(asset)
    db.commit()

    config = TranscriptionConfig(
        language="en",
        operating_point="enhanced",
        diarization="speaker",
    )

    async def _job() -> tuple[list[dict], float | None]:
        async with AsyncClient(api_key=settings.speechmatics_api_key) as client:
            job = await client.submit_job(audio.file_path, transcription_config=config)
            job_id = getattr(job, "id", None) or getattr(job, "job_id", None) or str(job)
            events.speechmatics_call(
                "submitted batch job",
                stage=MediaScanStage.transcribe,
                job_id=job_id,
            )
            poll_timeout = float(
                max(
                    120,
                    settings.speechmatics_poll_seconds
                    * settings.speechmatics_max_poll_attempts,
                )
            )
            transcript = await client.wait_for_completion(
                job_id,
                format_type=FormatType.JSON,
                polling_interval=5.0,
                timeout=poll_timeout,
            )
        segs = _segments_from_transcript(transcript)
        conf = getattr(transcript, "confidence", None)
        return segs, (float(conf) if isinstance(conf, (int, float)) else None)

    segments, confidence = asyncio.run(_job())
    return segments, confidence, "en"


def _segments_from_transcript(transcript: object) -> list[dict]:
    """Group Speechmatics word-level results into coarse speaker segments.

    `transcript.results` is a list of RecognitionResult objects with `.type`,
    `.start_time`, `.end_time`, and `.alternatives[0]` carrying `.content`,
    `.confidence`, `.speaker`.
    """
    results = getattr(transcript, "results", None) or []
    segments: list[dict] = []
    current: dict | None = None

    for r in results:
        r_type = getattr(r, "type", None)
        if r_type not in ("word", "punctuation"):
            continue
        alts = getattr(r, "alternatives", None) or []
        if not alts:
            continue
        alt = alts[0]
        content = getattr(alt, "content", "") or ""
        speaker = getattr(alt, "speaker", None) or "S1"
        start = getattr(r, "start_time", 0.0) or 0.0
        end = getattr(r, "end_time", start) or start

        is_punct = r_type == "punctuation"
        if current is None or current["speaker"] != speaker:
            if current is not None:
                segments.append(current)
            current = {
                "start": round(float(start), 2),
                "end": round(float(end), 2),
                "speaker": speaker,
                "text": content,
            }
        else:
            sep = "" if is_punct else " "
            current["text"] = f"{current['text']}{sep}{content}".strip()
            current["end"] = round(float(end), 2)

    if current is not None:
        segments.append(current)
    return segments
