"""Cost estimation + budget unit tests."""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.services.cost import (
    estimate_llm_calls_usd,
    estimate_transcription_usd,
    would_exceed_budget,
)


def test_transcription_cost_scales_with_duration() -> None:
    # 60 minutes at the default per-minute rate.
    settings = get_settings()
    one_hour = estimate_transcription_usd(3600, settings=settings)
    assert one_hour == pytest.approx(60 * settings.cost_asr_per_minute_usd, rel=1e-6)
    assert estimate_transcription_usd(0, settings=settings) == 0.0
    assert estimate_transcription_usd(None, settings=settings) == 0.0


def test_llm_call_cost() -> None:
    settings = get_settings()
    assert estimate_llm_calls_usd(0, settings=settings) == 0.0
    assert estimate_llm_calls_usd(3, settings=settings) == pytest.approx(
        3 * settings.cost_llm_per_call_usd, rel=1e-6
    )


def test_budget_ceiling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDIA_SCAN_BUDGET_USD", "1.0")
    get_settings.cache_clear()
    settings = get_settings()
    assert would_exceed_budget(0.5, settings=settings) is False
    assert would_exceed_budget(1.5, settings=settings) is True
    get_settings.cache_clear()


def test_budget_disabled_when_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEDIA_SCAN_BUDGET_USD", "0")
    get_settings.cache_clear()
    settings = get_settings()
    assert would_exceed_budget(9999.0, settings=settings) is False
    get_settings.cache_clear()
