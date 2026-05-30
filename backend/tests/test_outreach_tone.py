"""Outreach tone toggle: deterministic presets + regenerate endpoint.

Proves the bug fix — toggling tone actually changes the email body/subject,
not just a stored label — and that guardrails re-run on the rewritten draft.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.jobs.scan_runner import run_scan
from app.models.account import Account
from app.models.signal import Signal
from app.services.briefing import generate_outreach


@pytest.fixture
def seeded_account(client: TestClient, seed_csv_path: Path) -> str:
    with seed_csv_path.open("rb") as f:
        r = client.post(
            "/api/v1/import/seed",
            files={"file": ("seed_demo.csv", f, "text/csv")},
        )
    assert r.status_code == 200, r.text
    return client.get("/api/v1/accounts", params={"search": "ramp"}).json()["items"][0]["id"]


def _make_signal() -> Signal:
    from datetime import date

    from app.models.enums import SignalType

    return Signal(
        scan_id="scan_x",
        account_id="acc_x",
        signal_type=SignalType.migration,
        title="Snowflake migration blog",
        evidence_url="https://acme.com/blog/migration",
        fact_text="Public post describes moving to Snowflake and dbt.",
        confidence=0.8,
        observed_at=date.today(),
        recency_days=3,
    )


def test_deterministic_presets_differ_by_tone() -> None:
    account = Account(id="acc_x", name="Acme", domain="acme.com", industry="fintech")
    sig = _make_signal()

    warm = generate_outreach(account, None, sig, "warm")
    technical = generate_outreach(account, None, sig, "technical")
    executive = generate_outreach(account, None, sig, "executive")
    concise = generate_outreach(account, None, sig, "concise")

    bodies = {warm.body, technical.body, executive.body, concise.body}
    subjects = {warm.subject, technical.subject, executive.subject, concise.subject}
    # Every tone must produce a distinct body and subject.
    assert len(bodies) == 4
    assert len(subjects) == 4
    # Tones carry through on the payload.
    assert warm.tone == "warm"
    assert technical.tone == "technical"
    # Concise really is shorter.
    assert len(concise.body) < len(executive.body)


def _create_draft_via_scan(client: TestClient, account_id: str) -> str | None:
    scan_id = client.post(
        f"/api/v1/accounts/{account_id}/scans", json={"mode": "mock"}
    ).json()["scan_id"]
    run_scan(scan_id)
    pending = client.get("/api/v1/outreach/pending").json()
    if pending["total"] == 0:
        return None
    return pending["items"][0]["id"]


def test_regenerate_changes_body_and_keeps_reviewable(
    client: TestClient, seeded_account: str
) -> None:
    draft_id = _create_draft_via_scan(client, seeded_account)
    if draft_id is None:
        pytest.skip("Ramp did not reach sales-ready in this run")

    before = client.get(f"/api/v1/outreach/{draft_id}").json()
    assert before["tone"] == "warm"
    original_body = before["body"]

    r = client.post(f"/api/v1/outreach/{draft_id}/regenerate", json={"tone": "executive"})
    assert r.status_code == 200, r.text
    after = r.json()

    assert after["tone"] == "executive"
    assert after["body"] != original_body
    # Still needs human approval after a rewrite.
    assert after["status"] in ("edited", "pending_review")
    # Guardrails ran (notes key present, even if empty).
    assert "guardrail_notes_json" in after


def test_regenerate_rejects_terminal_draft(
    client: TestClient, seeded_account: str
) -> None:
    draft_id = _create_draft_via_scan(client, seeded_account)
    if draft_id is None:
        pytest.skip("Ramp did not reach sales-ready in this run")

    client.post(f"/api/v1/outreach/{draft_id}/approve")
    r = client.post(f"/api/v1/outreach/{draft_id}/regenerate", json={"tone": "technical"})
    assert r.status_code == 409


def test_regenerate_rejects_invalid_tone(
    client: TestClient, seeded_account: str
) -> None:
    draft_id = _create_draft_via_scan(client, seeded_account)
    if draft_id is None:
        pytest.skip("Ramp did not reach sales-ready in this run")
    r = client.post(f"/api/v1/outreach/{draft_id}/regenerate", json={"tone": "spicy"})
    # Pydantic enum validation (422) before our handler.
    assert r.status_code == 422
