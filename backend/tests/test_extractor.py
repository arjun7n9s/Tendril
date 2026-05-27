"""Phase 4 extractor: validation, sanitization, fallback behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import pytest

from app.config import get_settings
from app.db import get_sessionmaker
from app.models.account import Account
from app.models.enums import (
    AccountStatus,
    FetchMethod,
    FetchStatus,
    ScanMode,
    ScanStatus,
    SourceType,
)
from app.models.evidence import EvidenceDocument
from app.models.icp import ICPProfile
from app.models.scan import Scan
from app.models.source import Source
from app.services.aiml_client import AimlClient
from app.services.extractor import (
    _validate_signal,
    extract_signals_for_evidence,
    extract_signals_live,
)
from app.services.scan_events import ScanEventLogger


@pytest.fixture(autouse=True)
def _aiml_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIML_API_KEY", "test-aiml-key")
    monkeypatch.setenv("AIML_EXTRACTION_MODEL", "test-extractor-model")
    monkeypatch.setenv("AIML_BRIEFING_MODEL", "test-briefing-model")
    monkeypatch.setenv("AIML_DRAFT_MODEL", "test-draft-model")
    get_settings.cache_clear()


# ---- Pure validation tests ----


def test_validate_signal_accepts_clean_payload() -> None:
    raw = {
        "signal_type": "hiring",
        "title": "Hiring senior data engineer",
        "summary": "ok",
        "fact_text": "Open role mentions Kafka and Snowflake.",
        "inference_text": "Investing in data platform.",
        "recommended_action": "Send a reliability checklist.",
        "evidence_url": "https://acme.com/careers",
        "observed_at": "2026-05-20",
        "confidence": 0.82,
    }
    sig, reason = _validate_signal(raw, evidence_url="https://acme.com/careers")
    assert reason is None
    assert sig is not None
    assert sig["signal_type"].value == "hiring"
    assert sig["confidence"] == 0.82
    assert sig["observed_at"] == date(2026, 5, 20)


def test_validate_signal_rejects_missing_evidence_url() -> None:
    raw = {"title": "x", "evidence_url": "", "confidence": 0.9}
    sig, reason = _validate_signal(raw, evidence_url="https://acme.com/x")
    assert sig is None
    assert reason == "missing_evidence_url"


def test_validate_signal_rejects_evidence_url_mismatch() -> None:
    raw = {
        "title": "x",
        "evidence_url": "https://other.com/x",
        "confidence": 0.9,
    }
    sig, reason = _validate_signal(raw, evidence_url="https://acme.com/x")
    assert sig is None
    assert reason == "evidence_url_mismatch"


def test_validate_signal_rejects_low_confidence() -> None:
    raw = {
        "title": "x",
        "evidence_url": "https://acme.com/x",
        "confidence": 0.3,
    }
    sig, reason = _validate_signal(raw, evidence_url="https://acme.com/x")
    assert sig is None
    assert reason == "confidence_below_threshold"


def test_validate_signal_rejects_sensitive_content() -> None:
    raw = {
        "title": "Hiring trends",
        "summary": "Their political stance influences the team direction.",
        "evidence_url": "https://acme.com/x",
        "confidence": 0.9,
    }
    sig, reason = _validate_signal(raw, evidence_url="https://acme.com/x")
    assert sig is None
    assert reason == "sensitive_personal_content"


def test_validate_signal_rejects_forbidden_phrase() -> None:
    raw = {
        "title": "Note",
        "summary": "I noticed you switched companies.",
        "evidence_url": "https://acme.com/x",
        "confidence": 0.9,
    }
    sig, reason = _validate_signal(raw, evidence_url="https://acme.com/x")
    assert sig is None
    assert reason == "forbidden_phrase"


def test_validate_signal_coerces_unknown_signal_type() -> None:
    raw = {
        "title": "weird",
        "signal_type": "what_even_is_this",
        "evidence_url": "https://acme.com/x",
        "confidence": 0.6,
    }
    sig, reason = _validate_signal(raw, evidence_url="https://acme.com/x")
    assert reason is None
    assert sig is not None
    assert sig["signal_type"].value == "other"


# ---- Stubbed AIML client tests ----


@dataclass
class StubAimlResponse:
    payload: dict[str, Any]
    duration_ms: int = 100


class StubAimlClient:
    """In-process stub matching the AimlClient surface."""

    def __init__(self, responses: list[StubAimlResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def __aenter__(self) -> "StubAimlClient":
        return self

    async def __aexit__(self, *_exc) -> None:
        return None

    async def aclose(self) -> None:
        return None

    async def resolve_model(self, slot: str) -> str:
        return f"stub/{slot}"

    async def complete_json(self, *, slot: str, system_prompt: str, user_prompt: str, **_kwargs):
        self.calls.append({"slot": slot, "system_prompt": system_prompt, "user_prompt": user_prompt})
        if not self._responses:
            return {"signals": []}, _meta(slot, 0)
        r = self._responses.pop(0)
        return r.payload, _meta(slot, r.duration_ms)

    async def complete_text(self, *, slot: str, system_prompt: str, user_prompt: str, **_kwargs):
        self.calls.append({"slot": slot, "system_prompt": system_prompt, "user_prompt": user_prompt})
        if not self._responses:
            return _text_meta(slot, "", 0)
        r = self._responses.pop(0)
        return _text_meta(slot, r.payload.get("text", ""), r.duration_ms)


def _meta(slot: str, ms: int):
    from app.services.aiml_client import CompletionResult

    return CompletionResult(text="", model=f"stub/{slot}", prompt_tokens=10, completion_tokens=10, duration_ms=ms)


def _text_meta(slot: str, text: str, ms: int):
    from app.services.aiml_client import CompletionResult

    return CompletionResult(text=text, model=f"stub/{slot}", prompt_tokens=10, completion_tokens=10, duration_ms=ms)


def _seed_account_with_evidence(*, content: str, url: str = "https://acme.com/careers"):
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = Account(
            name="Acme",
            domain="acme.com",
            industry="fintech",
            status=AccountStatus.target,
        )
        db.add(account)
        db.commit()
        scan = Scan(
            account_id=account.id,
            scan_type="account_watchtower",
            status=ScanStatus.extracting,
            mode=ScanMode.live,
            progress_percent=60,
        )
        db.add(scan)
        db.commit()
        src = Source(
            scan_id=scan.id,
            account_id=account.id,
            url=url,
            source_type=SourceType.careers,
            rank=1,
            selected_for_scrape=True,
        )
        db.add(src)
        db.commit()
        ev = EvidenceDocument(
            scan_id=scan.id,
            source_id=src.id,
            account_id=account.id,
            url=url,
            title="Senior Data Engineer at Acme",
            content_markdown=content,
            content_hash="abc",
            fetched_at=datetime.now() - timedelta(seconds=10),
            fetch_status=FetchStatus.success,
            fetch_method=FetchMethod.unlocker,
            http_status=200,
            metadata_json={"length": len(content)},
        )
        db.add(ev)
        db.commit()
        return account.id, scan.id, ev.id


async def test_extract_signals_for_evidence_filters_invalid() -> None:
    account_id, _scan_id, ev_id = _seed_account_with_evidence(
        content="# Senior Data Engineer\nWe use Kafka and Snowflake.\n"
    )
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = db.get(Account, account_id)
        ev = db.get(EvidenceDocument, ev_id)

        client = StubAimlClient(
            [
                StubAimlResponse(
                    payload={
                        "signals": [
                            # valid
                            {
                                "signal_type": "hiring",
                                "title": "Hiring data platform",
                                "summary": "ok",
                                "fact_text": "Mentions Kafka and Snowflake",
                                "inference_text": "modernizing platform",
                                "recommended_action": "send checklist",
                                "evidence_url": ev.url,
                                "observed_at": "2026-05-20",
                                "confidence": 0.84,
                            },
                            # rejected: low confidence
                            {
                                "signal_type": "tech_stack",
                                "title": "weak guess",
                                "evidence_url": ev.url,
                                "confidence": 0.3,
                            },
                            # rejected: wrong url
                            {
                                "signal_type": "hiring",
                                "title": "x",
                                "evidence_url": "https://other.com/x",
                                "confidence": 0.9,
                            },
                            # rejected: sensitive
                            {
                                "signal_type": "other",
                                "title": "x",
                                "summary": "Their political views matter.",
                                "evidence_url": ev.url,
                                "confidence": 0.9,
                            },
                        ]
                    }
                )
            ]
        )

        validated, rejections, _ms = await extract_signals_for_evidence(
            aiml=client, account=account, icp=None, evidence=ev
        )
        assert len(validated) == 1
        assert len(rejections) == 3
        reasons = sorted(r.reason for r in rejections)
        assert "confidence_below_threshold" in reasons
        assert "evidence_url_mismatch" in reasons
        assert "sensitive_personal_content" in reasons


async def test_extract_signals_live_persists_signals() -> None:
    account_id, scan_id, ev_id = _seed_account_with_evidence(
        content="# Senior Data Engineer\nWe use Kafka and Snowflake at scale.\n"
    )
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = db.get(Account, account_id)
        scan = db.get(Scan, scan_id)
        ev = db.get(EvidenceDocument, ev_id)
        events = ScanEventLogger(db, scan.id)
        client = StubAimlClient(
            [
                StubAimlResponse(
                    payload={
                        "signals": [
                            {
                                "signal_type": "hiring",
                                "title": "Hiring data platform reliability",
                                "summary": "Open roles emphasize reliability.",
                                "fact_text": "Posting requires Kafka and Snowflake.",
                                "inference_text": "Reliability investment underway.",
                                "recommended_action": "Send a reliability checklist.",
                                "evidence_url": ev.url,
                                "observed_at": date.today().isoformat(),
                                "confidence": 0.78,
                            }
                        ]
                    }
                )
            ]
        )
        signals = await extract_signals_live(
            db,
            scan=scan,
            account=account,
            icp=None,
            evidence_rows=[ev],
            aiml=client,
            events=events,
        )
        db.commit()

        assert len(signals) == 1
        assert signals[0].evidence_url == ev.url
        assert signals[0].confidence == 0.78
        assert signals[0].evidence_document_id == ev.id
        # Event trace recorded one aiml_call.
        kinds = [getattr(e.event_type, "value", str(e.event_type)) for e in scan.events]
        assert "aiml_call" in kinds
