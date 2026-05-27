"""Tests for AIML-backed brief and outreach generation."""

from __future__ import annotations

from datetime import date

import pytest

from app.config import get_settings
from app.models.account import Account
from app.models.enums import AccountStatus, SignalType
from app.models.score import Score
from app.models.signal import Signal
from app.services.briefing import (
    BriefDraft,
    OutreachDraftPayload,
    generate_brief,
    generate_brief_live,
    generate_outreach,
    generate_outreach_live,
)
from tests.test_extractor import StubAimlClient, StubAimlResponse


@pytest.fixture(autouse=True)
def _aiml_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIML_API_KEY", "test-aiml-key")
    monkeypatch.setenv("AIML_EXTRACTION_MODEL", "stub-extractor")
    monkeypatch.setenv("AIML_BRIEFING_MODEL", "stub-briefer")
    monkeypatch.setenv("AIML_DRAFT_MODEL", "stub-drafter")
    get_settings.cache_clear()


def _make_account() -> Account:
    return Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        industry="fintech",
        status=AccountStatus.target,
    )


def _make_signal(*, evidence_url: str, signal_type: SignalType = SignalType.hiring, confidence: float = 0.8) -> Signal:
    return Signal(
        scan_id="scan_x",
        account_id="acc_x",
        signal_type=signal_type,
        title=f"{signal_type.value}: signal",
        evidence_url=evidence_url,
        fact_text="Page mentions Kafka and Snowflake.",
        inference_text="Investing in data platform.",
        confidence=confidence,
        observed_at=date.today(),
        recency_days=2,
    )


def _make_score(total: int = 78, sales_ready: bool = True) -> Score:
    return Score(
        scan_id="scan_x",
        account_id="acc_x",
        fit_score=22,
        timing_score=24,
        relationship_score=14,
        evidence_score=18,
        total_score=total,
        sales_ready=sales_ready,
        score_reasoning_json={"why": "test"},
    )


async def test_generate_brief_live_returns_model_payload() -> None:
    account = _make_account()
    signals = [
        _make_signal(evidence_url="https://acme.com/careers", confidence=0.9),
        _make_signal(evidence_url="https://acme.com/blog", signal_type=SignalType.migration, confidence=0.7),
    ]
    stub = StubAimlClient(
        [
            StubAimlResponse(
                payload={
                    "title": "Acme: GTM brief",
                    "executive_summary": "Acme is investing in data platform reliability.",
                    "why_now": "Hiring + migration evidence in the last 14 days.",
                    "key_evidence": [
                        {
                            "title": "Hiring data platform",
                            "evidence_url": "https://acme.com/careers",
                            "confidence": 0.9,
                        }
                    ],
                    "risks": ["Limited corroboration"],
                    "recommended_next_steps": ["Send a reliability checklist"],
                }
            )
        ]
    )

    brief, telemetry = await generate_brief_live(
        aiml=stub,
        account=account,
        signals=signals,
        score=_make_score(),
    )
    assert telemetry["fallback"] is False
    assert brief.title.startswith("Acme")
    assert "data platform" in brief.executive_summary.lower()
    assert brief.key_evidence and brief.key_evidence[0]["evidence_url"] == "https://acme.com/careers"


async def test_generate_brief_live_falls_back_on_bad_payload() -> None:
    account = _make_account()
    signals = [_make_signal(evidence_url="https://acme.com/careers")]
    # Model returns garbage that has none of the required fields.
    stub = StubAimlClient([StubAimlResponse(payload={"unrelated": "junk"})])

    brief, telemetry = await generate_brief_live(
        aiml=stub,
        account=account,
        signals=signals,
        score=_make_score(),
    )
    deterministic = generate_brief(account, signals, _make_score())
    # Title falls back to the deterministic version (or a normalized prefix).
    assert account.name in brief.title
    assert brief.executive_summary == deterministic.executive_summary


async def test_generate_outreach_live_returns_subject_and_body() -> None:
    account = _make_account()
    top = _make_signal(evidence_url="https://acme.com/careers")
    stub = StubAimlClient(
        [
            StubAimlResponse(
                payload={
                    "subject": "Quick note on Acme's data platform work",
                    "body": "Hello, the recent engineering content suggests reliability investment...",
                }
            )
        ]
    )
    out, telemetry = await generate_outreach_live(
        aiml=stub, account=account, signals=[top], top_signal=top
    )
    assert telemetry["fallback"] is False
    assert "Acme" in out.subject
    assert out.body
    assert isinstance(out, OutreachDraftPayload)


async def test_generate_outreach_live_falls_back_on_empty_payload() -> None:
    account = _make_account()
    top = _make_signal(evidence_url="https://acme.com/careers")
    stub = StubAimlClient([StubAimlResponse(payload={"subject": "", "body": ""})])
    out, telemetry = await generate_outreach_live(
        aiml=stub, account=account, signals=[top], top_signal=top
    )
    deterministic = generate_outreach(
        account,
        BriefDraft(
            title="x",
            executive_summary="x",
            why_now="x",
            key_evidence=[],
            risks=[],
            recommended_next_steps=[],
        ),
        top,
    )
    assert telemetry["fallback"] is True
    assert out.subject == deterministic.subject
