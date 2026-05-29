"""Cost estimation for media scans.

These are deliberately rough, clearly-labeled estimates — not invoices. The
point is twofold:

1. Budget enforcement: stop a scan before the expensive transcribe/extract
   stages if its projected cost would blow the per-scan ceiling.
2. Telemetry: show reps and operators an approximate dollar cost per scan so
   the "be disciplined about expensive media processing" promise is visible.

Per-unit prices come from settings so they can be tuned without code changes.
"""

from __future__ import annotations

from app.config import Settings, get_settings


def estimate_transcription_usd(
    duration_seconds: int | None, *, settings: Settings | None = None
) -> float:
    """Estimated ASR cost for transcribing `duration_seconds` of audio."""
    settings = settings or get_settings()
    minutes = max(0.0, (duration_seconds or 0) / 60.0)
    return round(minutes * settings.cost_asr_per_minute_usd, 4)


def estimate_llm_calls_usd(num_calls: int, *, settings: Settings | None = None) -> float:
    """Estimated cost for `num_calls` LLM calls (ranking/relevance/extraction)."""
    settings = settings or get_settings()
    return round(max(0, num_calls) * settings.cost_llm_per_call_usd, 4)


def would_exceed_budget(
    projected_usd: float, *, settings: Settings | None = None
) -> bool:
    """True if `projected_usd` exceeds the configured per-scan ceiling.

    A ceiling of 0 disables the hard stop (telemetry still accrues).
    """
    settings = settings or get_settings()
    ceiling = settings.media_scan_budget_usd
    if ceiling <= 0:
        return False
    return projected_usd > ceiling
