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
                source=source, events=events
            )
        except Exception as exc:
            events.warning(
                "Speechmatics transcription failed (resumable)",
                stage=MediaScanStage.transcribe,
                error_type=type(exc).__name__,
            )
            asset.transcription_status = TranscriptionStatus.failed
            asset.speechmatics_job_id = getattr(exc, "job_id", None)
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
    *, source: MediaSource, events: MediaScanEventLogger
) -> tuple[list[dict], float | None, str | None]:
    """Submit and poll a Speechmatics batch job with diarization.

    Uses the optional `speechmatics-batch` SDK (declared under the `voice`
    extra). Raises on failure so the caller can mark the stage resumable.
    """
    from speechmatics_batch import BatchClient  # type: ignore[import-not-found]
    from speechmatics_batch.models import (  # type: ignore[import-not-found]
        ConnectionSettings,
        TranscriptionConfig,
    )

    settings = get_settings()
    conn = ConnectionSettings(
        url="https://asr.api.speechmatics.com/v2",
        auth_token=settings.speechmatics_api_key,
    )
    config = TranscriptionConfig(
        language="en",
        diarization="speaker",
        operating_point="enhanced",
    )
    with BatchClient(conn) as client:
        job_id = client.submit_job(audio=source.source_url, transcription_config=config)
        events.speechmatics_call(
            "submitted batch job",
            stage=MediaScanStage.transcribe,
            job_id=job_id,
        )
        transcript = client.wait_for_completion(job_id, transcription_format="json-v2")

    segments: list[dict] = []
    results = transcript.get("results", []) if isinstance(transcript, dict) else []
    # Group word-level results into coarse speaker segments.
    current: dict | None = None
    for r in results:
        if r.get("type") != "word":
            continue
        alt = (r.get("alternatives") or [{}])[0]
        speaker = alt.get("speaker", "Speaker")
        word = alt.get("content", "")
        start = r.get("start_time", 0.0)
        end = r.get("end_time", 0.0)
        if current is None or current["speaker"] != speaker:
            if current is not None:
                segments.append(current)
            current = {"start": start, "end": end, "speaker": speaker, "text": word}
        else:
            current["text"] += f" {word}"
            current["end"] = end
    if current is not None:
        segments.append(current)

    return segments, None, "en"
