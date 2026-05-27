"""Guardrail tests for outreach drafts."""

from __future__ import annotations

from app.services.guardrails import check_outreach


def test_passes_clean_draft() -> None:
    res = check_outreach(
        subject="Quick note on Acme's data platform",
        body="Reading Acme's recent engineering content, it looks like the team is investing in reliability.",
    )
    assert res.ok
    assert res.notes == []


def test_rejects_creepy_phrasing() -> None:
    res = check_outreach(
        subject="hi",
        body="I saw you changed jobs and your new company is using competitor Y.",
    )
    assert not res.ok
    assert any("banned_phrase" in n for n in res.notes)


def test_rejects_competitor_mention_without_evidence() -> None:
    res = check_outreach(
        subject="hi",
        body="Heard you switched from competitor Snowflake recently.",
        competitor_keywords=["Snowflake"],
        evidence_urls=[],
    )
    assert not res.ok
    assert any("competitor_mentioned_without_evidence" in n for n in res.notes)


def test_allows_competitor_mention_with_evidence() -> None:
    res = check_outreach(
        subject="hi",
        body="Your engineering blog mentioned Snowflake in the migration write-up.",
        competitor_keywords=["Snowflake"],
        evidence_urls=["https://acme.com/blog"],
    )
    assert res.ok


def test_rejects_too_long_body() -> None:
    res = check_outreach(subject="hi", body="x" * 1600)
    assert not res.ok
    assert "too_long" in res.notes
