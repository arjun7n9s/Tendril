"""Account score refresh driven by conversation signals.

Conversation signals are strong timing evidence (active migrations, vendor
evaluations, approved budget, executive priorities). Rather than recomputing the
full web rubric — or writing into the web `scores` table, which is keyed to a
web scan — we compute a bounded positive delta on top of the account's latest
score and report it on the media scan job, with a human-readable explanation of
what moved the number. This keeps the web scoring path untouched and avoids any
schema migration on the existing scores table.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.conversation_signal import ConversationSignal
from app.models.helpers import as_str
from app.models.score import Score

# Signal types that meaningfully move buying timing.
_HOT_TYPES = {"migration", "funding", "product_launch", "leadership_change", "competitor_mention"}
_WARM_TYPES = {"hiring", "tech_stack", "champion_move"}

_HOT_POINTS = 6
_WARM_POINTS = 3
_OTHER_POINTS = 1
_MAX_DELTA = 18


@dataclass
class ScoreDelta:
    previous_total: int
    new_total: int
    delta: int
    explanation: list[str]
    sales_ready: bool


def _latest_score(db: Session, account_id: str) -> Score | None:
    return db.scalar(
        select(Score)
        .where(Score.account_id == account_id)
        .order_by(Score.created_at.desc())
    )


def compute_score_delta(
    db: Session,
    *,
    account: Account,
    signals: list[ConversationSignal],
) -> ScoreDelta:
    """Compute (but do not persist) a score delta from conversation signals."""
    prev = _latest_score(db, account.id)
    prev_total = prev.total_score if prev else 0

    raw_delta = 0.0
    explanation: list[str] = []
    for sig in signals:
        stype = as_str(sig.signal_type)
        if stype in _HOT_TYPES:
            pts = _HOT_POINTS
        elif stype in _WARM_TYPES:
            pts = _WARM_POINTS
        else:
            pts = _OTHER_POINTS
        weighted = pts * max(0.0, min(1.0, sig.confidence))
        raw_delta += weighted
        if weighted >= 3:
            explanation.append(
                f"+{round(weighted)} from spoken {stype.replace('_', ' ')} signal "
                f"({int(sig.confidence * 100)}% confidence)"
            )

    delta = min(_MAX_DELTA, round(raw_delta))
    new_total = min(100, prev_total + delta)

    high_conf = [s for s in signals if s.confidence >= 0.65]
    unique_sources = {s.source_url for s in signals}
    sales_ready = new_total >= 70 and len(high_conf) >= 2 and len(unique_sources) >= 1

    if not explanation:
        explanation.append("No material conversation signals affected the score.")

    return ScoreDelta(
        previous_total=prev_total,
        new_total=new_total,
        delta=delta,
        explanation=explanation,
        sales_ready=sales_ready,
    )
