"""Unit tests for the transcript PII scrubber."""

from __future__ import annotations

from app.models.enums import PrivacyStatus
from app.services.pii_scrubber import scrub_segments, scrub_text


def test_redacts_email_and_phone() -> None:
    res = scrub_text("Reach me at jane.doe@example.com or call 415-555-0192 today.")
    assert "jane.doe@example.com" not in res.scrubbed_text
    assert "415-555-0192" not in res.scrubbed_text
    assert res.pii_status == PrivacyStatus.scrubbed
    assert res.findings.get("email") == 1
    assert res.findings.get("phone") == 1


def test_redacts_address_and_url() -> None:
    res = scrub_text("Our office is at 1600 Amphitheatre Parkway. See https://secret.example.com/x.")
    assert "1600 Amphitheatre Parkway" not in res.scrubbed_text
    assert "secret.example.com" not in res.scrubbed_text


def test_flags_sensitive_content() -> None:
    res = scrub_text("The candidate mentioned their religion during the talk.")
    assert res.sensitive is True
    assert res.pii_status == PrivacyStatus.sensitive_blocked


def test_clean_text_unchanged() -> None:
    text = "We migrated to Snowflake and cut nightly runtime in half."
    res = scrub_text(text)
    assert res.scrubbed_text == text
    assert res.pii_status == PrivacyStatus.clean
    assert res.findings == {}


def test_scrub_segments_aggregates() -> None:
    segments = [
        {"start": 0.0, "end": 5.0, "speaker": "A", "text": "Email me at a@b.com"},
        {"start": 5.0, "end": 9.0, "speaker": "B", "text": "We use Kafka and Snowflake"},
    ]
    scrubbed, findings, sensitive = scrub_segments(segments)
    assert len(scrubbed) == 2
    assert "a@b.com" not in scrubbed[0]["text"]
    assert findings.get("email") == 1
    assert sensitive is False
    assert scrubbed[0]["privacy_status"] in ("scrubbed", "clean")


def test_empty_input() -> None:
    res = scrub_text(None)
    assert res.scrubbed_text == ""
    assert res.pii_status == PrivacyStatus.clean
    assert scrub_segments(None) == ([], {}, False)
