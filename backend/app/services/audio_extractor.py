"""Live audio extraction for the media pipeline.

Turns a *page* URL discovered by Bright Data SERP (a YouTube watch page, a
podcast episode page, a webinar/earnings page) into a real, local audio file
that Speechmatics can transcribe. This is what makes "discover live -> transcribe
live" genuinely work instead of depending on a SERP result happening to be a
direct .mp3.

Strategy:
1. yt-dlp resolves the page, picks the best audio-only stream, and downloads it.
2. ffmpeg (invoked by yt-dlp) transcodes to a compact mono 16 kHz MP3 — small,
   fast to upload, and ideal for ASR.
3. We SHA-256 the resulting audio bytes for content-addressable dedup, so the
   same episode is never transcribed twice even across accounts.

Everything is best-effort: any failure raises AudioExtractionError and the
caller degrades (fixtures / skip) without breaking the scan.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.logging_setup import get_logger

log = get_logger("audio_extractor")

# Where extracted audio lands. Kept under var/ so it's gitignored and easy to
# clear between runs.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIO_CACHE_DIR = PROJECT_ROOT / "var" / "media_audio"

# Hard ceilings so a runaway source can't download a 4-hour stream.
_MAX_DURATION_SECONDS = 5400  # 90 minutes
_TARGET_SAMPLE_RATE = 16_000


class AudioExtractionError(RuntimeError):
    """Raised when a page URL cannot be resolved to a usable audio file."""


@dataclass
class ExtractedAudio:
    file_path: str
    media_hash: str
    duration_seconds: int | None
    byte_size: int
    source_title: str | None
    resolver: str  # "yt_dlp"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_audio(url: str, *, max_duration_seconds: int = _MAX_DURATION_SECONDS) -> ExtractedAudio:
    """Download + transcode the best audio track for `url` to a local mp3.

    Raises AudioExtractionError on any failure (private video, no audio,
    geo-block, ffmpeg missing, over-length, etc.).
    """
    try:
        import yt_dlp  # imported lazily so unit tests don't pay the import
    except ImportError as exc:  # pragma: no cover
        raise AudioExtractionError("yt_dlp_not_installed") from exc

    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Deterministic temp name from the URL; final extension is mp3 after
    # postprocessing. yt-dlp fills in the extension via the template.
    url_key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    out_template = str(AUDIO_CACHE_DIR / f"{url_key}.%(ext)s")
    final_path = AUDIO_CACHE_DIR / f"{url_key}.mp3"

    # Reuse an already-extracted file (cheap idempotency for resumes/reruns).
    if final_path.exists() and final_path.stat().st_size > 0:
        return ExtractedAudio(
            file_path=str(final_path),
            media_hash=_sha256_file(final_path),
            duration_seconds=None,
            byte_size=final_path.stat().st_size,
            source_title=None,
            resolver="yt_dlp",
        )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 2,
        "socket_timeout": 30,
        # Reject absurdly long media before downloading the whole thing.
        "match_filter": _duration_guard(max_duration_seconds),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ],
        # Mono 16 kHz is ideal for ASR and keeps the upload small.
        "postprocessor_args": ["-ac", "1", "-ar", str(_TARGET_SAMPLE_RATE)],
    }

    info_title: str | None = None
    duration: int | None = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if isinstance(info, dict):
                info_title = info.get("title")
                dur = info.get("duration")
                duration = int(dur) if isinstance(dur, (int, float)) else None
    except Exception as exc:
        raise AudioExtractionError(f"extract_failed:{type(exc).__name__}") from exc

    if not final_path.exists() or final_path.stat().st_size == 0:
        # Some extractors emit a different extension; find the produced file.
        produced = _find_produced_audio(url_key)
        if produced is None:
            raise AudioExtractionError("no_audio_file_produced")
        final_path = produced

    return ExtractedAudio(
        file_path=str(final_path),
        media_hash=_sha256_file(final_path),
        duration_seconds=duration,
        byte_size=final_path.stat().st_size,
        source_title=info_title,
        resolver="yt_dlp",
    )


def _duration_guard(max_seconds: int):
    """yt-dlp match_filter that rejects over-length media before download."""

    def _filter(info_dict, *, incomplete=False):
        duration = info_dict.get("duration")
        if isinstance(duration, (int, float)) and duration > max_seconds:
            return f"media too long ({int(duration)}s > {max_seconds}s)"
        return None

    return _filter


def _find_produced_audio(url_key: str) -> Path | None:
    if not AUDIO_CACHE_DIR.exists():
        return None
    candidates = sorted(
        (p for p in AUDIO_CACHE_DIR.glob(f"{url_key}.*") if p.is_file() and p.stat().st_size > 0),
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    return candidates[0] if candidates else None


def looks_extractable(url: str) -> bool:
    """Cheap heuristic: is this URL likely to yield audio via yt-dlp?

    yt-dlp supports 1000+ sites, but for the GTM media pipeline we care about
    the spoken-source hosts. This gates extraction attempts so we don't fire
    yt-dlp at a plain blog post.
    """
    lower = url.lower()
    markers = (
        "youtube.com/watch",
        "youtu.be/",
        "vimeo.com/",
        "soundcloud.com/",
        "podcasts.apple.com",
        ".mp3",
        ".m4a",
        ".wav",
        "/episode",
        "buzzsprout.com",
        "libsyn.com",
        "simplecast.com",
        "megaphone.fm",
        "anchor.fm",
        "transistor.fm",
    )
    return any(m in lower for m in markers)
