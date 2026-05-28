"""Blessed-run snapshot format.

A blessed run is a JSON document captured from a successful scan that
can be replayed in `mode=cached` to give the demo a deterministic,
high-quality flow when live conditions are flaky. Per refinement #17
the replay path is honest: events emitted from a cached replay use the
`_replayed` event-type variants, and metadata carries `replayed: true`.

Schema (one file per account):

    {
      "version": 1,
      "account": {
        "name": "...", "domain": "...", "industry": "...",
        "company_size": "...", "region": "...", "status": "..."
      },
      "captured_at": "<ISO8601>",
      "captured_from_scan_id": "scan_...",
      "sources": [...],
      "evidence_documents": [...],
      "signals": [...],
      "score": {...},
      "brief": {...},
      "outreach_drafts": [...]
    }

Files live at `fixtures/blessed_runs/<account_id>.json`. Snapshots use
the *current* account_id as filename, but the file does not depend on
that id at replay time; replays bind to the live account row instead.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.brief import Brief
from app.models.evidence import EvidenceDocument
from app.models.helpers import as_str
from app.models.outreach import OutreachDraft
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal
from app.models.source import Source

BLESSED_RUNS_DIR = (
    Path(__file__).resolve().parents[2] / "fixtures" / "blessed_runs"
)
BLESSED_RUN_VERSION = 1


def _isoformat(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def _account_to_dict(account: Account) -> dict[str, Any]:
    return {
        "name": account.name,
        "domain": account.domain,
        "industry": account.industry,
        "company_size": account.company_size,
        "region": account.region,
        "status": as_str(account.status),
        "metadata_json": account.metadata_json,
    }


def _source_to_dict(src: Source) -> dict[str, Any]:
    return {
        "url": src.url,
        "source_type": as_str(src.source_type),
        "discovery_query": src.discovery_query,
        "rank": src.rank,
        "selected_for_scrape": bool(src.selected_for_scrape),
    }


def _evidence_to_dict(ev: EvidenceDocument) -> dict[str, Any]:
    return {
        "url": ev.url,
        "title": ev.title,
        "content_markdown": ev.content_markdown,
        "content_hash": ev.content_hash,
        "fetched_at": _isoformat(ev.fetched_at),
        "fetch_status": as_str(ev.fetch_status),
        "fetch_method": as_str(ev.fetch_method),
        "http_status": ev.http_status,
        "metadata_json": ev.metadata_json,
    }


def _signal_to_dict(sig: Signal) -> dict[str, Any]:
    return {
        "signal_type": as_str(sig.signal_type),
        "title": sig.title,
        "summary": sig.summary,
        "fact_text": sig.fact_text,
        "inference_text": sig.inference_text,
        "recommended_action": sig.recommended_action,
        "evidence_url": sig.evidence_url,
        "observed_at": sig.observed_at.isoformat() if sig.observed_at else None,
        "confidence": sig.confidence,
        "recency_days": sig.recency_days,
        "metadata_json": sig.metadata_json,
    }


def _score_to_dict(score: Score) -> dict[str, Any]:
    return {
        "fit_score": score.fit_score,
        "timing_score": score.timing_score,
        "relationship_score": score.relationship_score,
        "evidence_score": score.evidence_score,
        "total_score": score.total_score,
        "sales_ready": bool(score.sales_ready),
        "score_reasoning_json": score.score_reasoning_json,
    }


def _brief_to_dict(brief: Brief) -> dict[str, Any]:
    return {
        "title": brief.title,
        "executive_summary": brief.executive_summary,
        "why_now": brief.why_now,
        "key_evidence_json": brief.key_evidence_json,
        "risks_json": brief.risks_json,
        "recommended_next_steps_json": brief.recommended_next_steps_json,
    }


def _outreach_to_dict(draft: OutreachDraft) -> dict[str, Any]:
    return {
        "subject": draft.subject,
        "body": draft.body,
        "tone": as_str(draft.tone),
        "status": as_str(draft.status),
        "guardrail_notes_json": draft.guardrail_notes_json,
        "reviewer_feedback": draft.reviewer_feedback,
    }


def snapshot_scan(db: Session, scan: Scan) -> dict[str, Any]:
    """Build a serializable snapshot of a completed scan."""
    account = db.get(Account, scan.account_id)
    if account is None:
        raise ValueError(f"account_not_found:{scan.account_id}")

    sources = list(
        db.scalars(select(Source).where(Source.scan_id == scan.id).order_by(Source.rank))
    )
    evidence = list(
        db.scalars(
            select(EvidenceDocument).where(EvidenceDocument.scan_id == scan.id)
        )
    )
    signals = list(
        db.scalars(
            select(Signal)
            .where(Signal.scan_id == scan.id)
            .order_by(Signal.confidence.desc())
        )
    )
    score = db.scalar(select(Score).where(Score.scan_id == scan.id))
    brief = db.scalar(select(Brief).where(Brief.scan_id == scan.id))
    drafts = list(
        db.scalars(select(OutreachDraft).where(OutreachDraft.scan_id == scan.id))
    )

    return {
        "version": BLESSED_RUN_VERSION,
        "account": _account_to_dict(account),
        "captured_at": _isoformat(datetime.now(UTC)),
        "captured_from_scan_id": scan.id,
        "captured_from_mode": as_str(scan.mode),
        "sources": [_source_to_dict(s) for s in sources],
        "evidence_documents": [_evidence_to_dict(e) for e in evidence],
        "signals": [_signal_to_dict(s) for s in signals],
        "score": _score_to_dict(score) if score else None,
        "brief": _brief_to_dict(brief) if brief else None,
        "outreach_drafts": [_outreach_to_dict(d) for d in drafts],
    }


def write_snapshot(account_id: str, snapshot: dict[str, Any]) -> Path:
    BLESSED_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = BLESSED_RUNS_DIR / f"{account_id}.json"
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_snapshot_for_account(account_id: str) -> dict[str, Any] | None:
    """Load a blessed-run snapshot keyed by account_id, if present."""
    path = BLESSED_RUNS_DIR / f"{account_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def find_snapshot_by_domain(domain: str) -> dict[str, Any] | None:
    """Fall back lookup by account domain when the account_id has changed.

    Useful in fresh local DBs where the demo account got a new id but the
    blessed run was captured against the same company.
    """
    if not domain or not BLESSED_RUNS_DIR.exists():
        return None
    domain_lower = domain.lower()
    for path in BLESSED_RUNS_DIR.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        acc = payload.get("account") or {}
        if (acc.get("domain") or "").lower() == domain_lower:
            return payload
    return None
