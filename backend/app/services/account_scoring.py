"""Unified account score snapshots.

Both pipelines write here so the account's headline number reflects every
modality:

- the web scan pipeline writes a snapshot from its full rubric `Score`;
- the media pipeline writes a snapshot that applies the conversation
  score-delta on top of the latest snapshot.

Reading the latest snapshot gives the UI one number that genuinely moves when
spoken evidence lands.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account_score_snapshot import AccountScoreSnapshot


def latest_snapshot(db: Session, account_id: str) -> AccountScoreSnapshot | None:
    return db.scalar(
        select(AccountScoreSnapshot)
        .where(AccountScoreSnapshot.account_id == account_id)
        .order_by(AccountScoreSnapshot.created_at.desc())
    )


def record_web_snapshot(
    db: Session,
    *,
    account_id: str,
    fit: int,
    timing: int,
    relationship: int,
    evidence: int,
    total: int,
    sales_ready: bool,
    origin_id: str | None,
    reasoning: dict | None = None,
) -> AccountScoreSnapshot:
    snap = AccountScoreSnapshot(
        account_id=account_id,
        fit_score=fit,
        timing_score=timing,
        relationship_score=relationship,
        evidence_score=evidence,
        total_score=total,
        sales_ready=sales_ready,
        source="web_scan",
        origin_id=origin_id,
        conversation_delta=None,
        reasoning_json=reasoning or {},
    )
    db.add(snap)
    db.flush()
    return snap


def record_media_snapshot(
    db: Session,
    *,
    account_id: str,
    delta: int,
    new_total: int,
    sales_ready: bool,
    origin_id: str | None,
    explanation: list[str] | None = None,
) -> AccountScoreSnapshot:
    """Write a snapshot that layers the conversation delta on the prior one.

    Component sub-scores are inherited from the previous snapshot (the spoken
    delta is applied to timing, which is where conversation intent lives), so
    the breakdown stays coherent.
    """
    prev = latest_snapshot(db, account_id)
    fit = prev.fit_score if prev else 0
    rel = prev.relationship_score if prev else 0
    evidence = prev.evidence_score if prev else 0
    prev_timing = prev.timing_score if prev else 0
    new_timing = min(30, prev_timing + max(0, delta))

    snap = AccountScoreSnapshot(
        account_id=account_id,
        fit_score=fit,
        timing_score=new_timing,
        relationship_score=rel,
        evidence_score=evidence,
        total_score=new_total,
        sales_ready=sales_ready,
        source="media_scan",
        origin_id=origin_id,
        conversation_delta=delta,
        reasoning_json={"source": "media_scan", "explanation": explanation or []},
    )
    db.add(snap)
    db.flush()
    return snap
