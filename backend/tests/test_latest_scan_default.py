"""Phase 7: account-level views default to the latest scan.

When the same account is scanned multiple times in a single dev DB,
signals and outreach drafts accumulate. The frontend demo would render
all of them and look noisy. The default response now scopes to the
latest scan; `?all_history=true` opts back in to the full history.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import get_sessionmaker
from app.models.account import Account
from app.models.brief import Brief
from app.models.enums import (
    AccountStatus,
    OutreachStatus,
    OutreachTone,
    ScanMode,
    ScanStatus,
    SignalType,
)
from app.models.outreach import OutreachDraft
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal


def _seed_two_scans_for_one_account(account_name: str = "Acme") -> tuple[str, str, str]:
    """Returns (account_id, older_scan_id, latest_scan_id)."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        account = Account(
            name=account_name,
            domain=f"{account_name.lower()}.com",
            industry="fintech",
            status=AccountStatus.target,
        )
        db.add(account)
        db.commit()

        older = Scan(
            account_id=account.id,
            scan_type="account_watchtower",
            status=ScanStatus.completed,
            mode=ScanMode.live,
            progress_percent=100,
            started_at=datetime.now(UTC) - timedelta(hours=2),
            completed_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db.add(older)
        db.commit()
        # Ensure a created_at gap so 'latest' is unambiguous.
        latest = Scan(
            account_id=account.id,
            scan_type="account_watchtower",
            status=ScanStatus.completed,
            mode=ScanMode.live,
            progress_percent=100,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        db.add(latest)
        db.commit()

        # 1 stale signal on older, 2 fresh signals on latest.
        for scan, prefix, conf in (
            (older, "stale", 0.7),
        ):
            db.add(
                Signal(
                    scan_id=scan.id,
                    account_id=account.id,
                    signal_type=SignalType.tech_stack,
                    title=f"{prefix} signal",
                    evidence_url=f"https://acme.com/{prefix}",
                    confidence=conf,
                    observed_at=date.today(),
                    recency_days=120,
                )
            )
        for i in range(2):
            db.add(
                Signal(
                    scan_id=latest.id,
                    account_id=account.id,
                    signal_type=SignalType.funding,
                    title=f"fresh signal {i}",
                    evidence_url=f"https://acme.com/fresh{i}",
                    confidence=0.85,
                    observed_at=date.today(),
                    recency_days=2,
                )
            )

        # Score and brief on the latest scan only.
        db.add(
            Score(
                scan_id=latest.id,
                account_id=account.id,
                fit_score=24,
                timing_score=22,
                relationship_score=12,
                evidence_score=14,
                total_score=72,
                sales_ready=True,
                score_reasoning_json={"x": 1},
            )
        )
        db.add(
            Brief(
                scan_id=latest.id,
                account_id=account.id,
                title=f"{account_name}: GTM brief",
                executive_summary="latest brief",
                why_now="recent",
                key_evidence_json=[],
                risks_json=[],
                recommended_next_steps_json=[],
            )
        )

        # Pending outreach drafts on both scans. Default response should
        # only return the one tied to the latest scan.
        db.add(
            OutreachDraft(
                scan_id=older.id,
                account_id=account.id,
                subject="Stale subject",
                body="stale body",
                tone=OutreachTone.warm,
                status=OutreachStatus.pending_review,
                guardrail_notes_json=[],
            )
        )
        db.add(
            OutreachDraft(
                scan_id=latest.id,
                account_id=account.id,
                subject="Fresh subject",
                body="fresh body",
                tone=OutreachTone.warm,
                status=OutreachStatus.pending_review,
                guardrail_notes_json=[],
            )
        )
        db.commit()
        return account.id, older.id, latest.id


def test_account_detail_shows_only_latest_scan_signals(client: TestClient) -> None:
    account_id, older_id, latest_id = _seed_two_scans_for_one_account()
    detail = client.get(f"/api/v1/accounts/{account_id}").json()
    assert detail["latest_scan"]["id"] == latest_id
    titles = {s["title"] for s in detail["recent_signals"]}
    assert all("stale" not in t for t in titles)
    assert any("fresh" in t for t in titles)


def test_account_signals_default_to_latest_scan(client: TestClient) -> None:
    account_id, older_id, latest_id = _seed_two_scans_for_one_account()
    body = client.get(f"/api/v1/accounts/{account_id}/signals").json()
    assert body["total"] == 2
    assert all(s["scan_id"] == latest_id for s in body["items"])


def test_account_signals_all_history_returns_full_set(client: TestClient) -> None:
    account_id, older_id, latest_id = _seed_two_scans_for_one_account()
    body = client.get(
        f"/api/v1/accounts/{account_id}/signals", params={"all_history": "true"}
    ).json()
    assert body["total"] == 3


def test_outreach_pending_defaults_to_latest_scan_per_account(
    client: TestClient,
) -> None:
    account_id, older_id, latest_id = _seed_two_scans_for_one_account()
    body = client.get("/api/v1/outreach/pending").json()
    subjects = {d["subject"] for d in body["items"]}
    assert "Fresh subject" in subjects
    assert "Stale subject" not in subjects


def test_outreach_pending_all_history_includes_older_drafts(
    client: TestClient,
) -> None:
    _seed_two_scans_for_one_account()
    body = client.get(
        "/api/v1/outreach/pending", params={"all_history": "true"}
    ).json()
    subjects = {d["subject"] for d in body["items"]}
    assert {"Fresh subject", "Stale subject"}.issubset(subjects)
