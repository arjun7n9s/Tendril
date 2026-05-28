"""Scoring service.

Implements the 100-point scoring rubric and sales-ready rule:
    sales_ready = total >= 70
        AND signals with confidence >= 0.65 count >= 2
        AND unique evidence URLs >= 2

Resilient to sparse live signals: a couple of strong, recent signals
should be enough to score well. Signal quality is weighted alongside
signal count so an account with 2 high-confidence "hot" signals does
not score worse than one with 6 noisy low-confidence ones.

Returns reasoning JSON so the brief can quote the rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.helpers import as_str
from app.models.icp import ICPProfile
from app.models.signal import Signal


# Signal types that strongly indicate buying timing.
_HOT_TIMING_TYPES = {"funding", "migration", "product_launch", "leadership_change"}
_WARM_TIMING_TYPES = {"hiring", "tech_stack", "competitor_mention", "champion_move"}

# Phase 5: confidence-weighted scoring thresholds.
_HOT_BASE = 9
_HOT_MAX = 12
_WARM_BASE = 5
_WARM_MAX = 7
_OTHER_BASE = 1
_OTHER_MAX = 2

# Recency curve in days. Anything <=14d is full credit; >=120d is no credit.
_RECENCY_FULL_DAYS = 14
_RECENCY_NONE_DAYS = 120


@dataclass
class ScoringInput:
    account: Account
    signals: list[Signal]
    icp: ICPProfile | None
    has_champion: bool


@dataclass
class ScoringOutput:
    fit_score: int
    timing_score: int
    relationship_score: int
    evidence_score: int
    total_score: int
    sales_ready: bool
    reasoning: dict[str, Any]


def _norm(values: list[str] | None) -> set[str]:
    return {v.lower() for v in (values or []) if isinstance(v, str)}


def _recency_weight(recency_days: int | None, observed_at: date | None) -> float:
    """Linear decay: 1.0 within the full-credit window, 0.0 past the floor."""
    days: int | None = recency_days
    if days is None and observed_at is not None:
        days = max(0, (date.today() - observed_at).days)
    if days is None:
        return 0.6  # unknown but not useless
    if days <= _RECENCY_FULL_DAYS:
        return 1.0
    if days >= _RECENCY_NONE_DAYS:
        return 0.0
    span = _RECENCY_NONE_DAYS - _RECENCY_FULL_DAYS
    return max(0.0, 1.0 - (days - _RECENCY_FULL_DAYS) / span)


def score_fit(account: Account, icp: ICPProfile | None) -> tuple[int, dict[str, Any]]:
    if icp is None:
        return 8, {"reason": "no ICP profile; awarding partial fit"}

    industries = _norm(icp.industries_json)
    sizes = _norm(icp.company_sizes_json)
    regions = _norm(icp.regions_json)
    tech_keywords = _norm(icp.tech_keywords_json)

    score = 0
    detail: dict[str, Any] = {}

    if account.industry and account.industry.lower() in industries:
        score += 10
        detail["industry_match"] = True
    if account.company_size and account.company_size.lower() in sizes:
        score += 6
        detail["company_size_match"] = True
    if account.region and account.region.lower() in regions:
        score += 3
        detail["region_match"] = True

    account_tech = _norm((account.metadata_json or {}).get("tech_keywords"))
    overlap = account_tech & tech_keywords
    detail["tech_overlap"] = sorted(overlap)
    score += min(len(overlap) * 3, 12)

    return min(score, 30), detail


def score_timing(signals: list[Signal]) -> tuple[int, dict[str, Any]]:
    """Confidence-weighted timing score with recency decay.

    For each signal:
        contribution = base + (max - base) * confidence  -- but base is the
                       worst-case value at conf=0.45 and max at conf=1.0,
                       so effectively contribution scales linearly between
                       them. Recency weight then multiplies the result.
    Score is capped at 30 and floored at 0.
    """
    if not signals:
        return 0, {"reason": "no signals"}

    detail: dict[str, Any] = {
        "hot": [],
        "warm": [],
        "other": 0,
        "recent_count": 0,
        "per_signal": [],
    }
    raw = 0.0

    for s in signals:
        stype = as_str(s.signal_type)
        if stype in _HOT_TIMING_TYPES:
            base, ceiling = _HOT_BASE, _HOT_MAX
            detail["hot"].append(stype)
        elif stype in _WARM_TIMING_TYPES:
            base, ceiling = _WARM_BASE, _WARM_MAX
            detail["warm"].append(stype)
        else:
            base, ceiling = _OTHER_BASE, _OTHER_MAX
            detail["other"] += 1

        # Confidence in [0.45, 1.0] is mapped to [0, 1] for this scaling.
        conf_norm = max(0.0, min(1.0, (s.confidence - 0.45) / 0.55))
        contribution = base + (ceiling - base) * conf_norm

        recency = _recency_weight(s.recency_days, s.observed_at)
        if recency >= 0.95:
            detail["recent_count"] += 1
        contribution *= 0.65 + 0.35 * recency

        raw += contribution
        detail["per_signal"].append(
            {
                "signal_type": stype,
                "confidence": round(s.confidence, 2),
                "recency_weight": round(recency, 2),
                "contribution": round(contribution, 2),
            }
        )

    score = min(int(round(raw)), 30)
    detail["raw_score"] = round(raw, 2)
    return score, detail


def score_relationship(has_champion: bool, signals: list[Signal]) -> tuple[int, dict[str, Any]]:
    score = 0
    detail: dict[str, Any] = {"has_champion": has_champion}
    if has_champion:
        score += 12
    if any(getattr(s, "person_id", None) for s in signals):
        score += 4
        detail["person_linked_signals"] = True
    if any(as_str(s.signal_type) == "champion_move" for s in signals):
        score += 4
        detail["champion_move_signal"] = True
    return min(score, 20), detail


def score_evidence(signals: list[Signal]) -> tuple[int, dict[str, Any]]:
    """Evidence score rewards quality first, breadth second.

    Ramp's Phase 4 run had 2 signals from 1 host with avg conf 0.85.
    Old rubric gave 13/20. The new rubric weights average confidence
    much more heavily so 2 high-confidence sources count as solid
    evidence even before we have multi-host corroboration.
    """
    if not signals:
        return 0, {"reason": "no signals"}
    unique_urls = {s.evidence_url for s in signals if s.evidence_url}
    avg_conf = sum(s.confidence for s in signals) / max(len(signals), 1)
    unique_hosts = {url.split("/")[2] for url in unique_urls if "://" in url}

    detail: dict[str, Any] = {
        "unique_url_count": len(unique_urls),
        "unique_host_count": len(unique_hosts),
        "avg_confidence": round(avg_conf, 3),
    }

    # Confidence-driven core (0-12).
    core = max(0.0, min(1.0, (avg_conf - 0.45) / 0.55)) * 12
    detail["confidence_core"] = round(core, 2)

    # URL breadth (0-5): 1 URL = 2, 2 = 4, 3+ = 5.
    if len(unique_urls) >= 3:
        breadth = 5
    elif len(unique_urls) == 2:
        breadth = 4
    elif len(unique_urls) == 1:
        breadth = 2
    else:
        breadth = 0
    detail["url_breadth"] = breadth

    # Multi-host corroboration bonus (0-3): +1 per extra host past the first.
    multi_host_bonus = min(3, max(0, len(unique_hosts) - 1))
    detail["multi_host_bonus"] = multi_host_bonus

    score = int(round(core + breadth + multi_host_bonus))
    return min(score, 20), detail


def compute_scores(payload: ScoringInput) -> ScoringOutput:
    fit, fit_detail = score_fit(payload.account, payload.icp)
    timing, timing_detail = score_timing(payload.signals)
    rel, rel_detail = score_relationship(payload.has_champion, payload.signals)
    ev, ev_detail = score_evidence(payload.signals)
    total = fit + timing + rel + ev

    high_conf = [s for s in payload.signals if s.confidence >= 0.65]
    unique_urls = {s.evidence_url for s in payload.signals if s.evidence_url}
    sales_ready = total >= 70 and len(high_conf) >= 2 and len(unique_urls) >= 2

    near_miss = (not sales_ready) and 55 <= total <= 69
    needs_one_more = []
    if not sales_ready:
        if total < 70:
            needs_one_more.append(f"total_score below 70 (currently {total})")
        if len(high_conf) < 2:
            needs_one_more.append(
                f"need {2 - len(high_conf)} more signal(s) with confidence >= 0.65"
            )
        if len(unique_urls) < 2:
            needs_one_more.append(
                f"need {2 - len(unique_urls)} more unique evidence URL(s)"
            )

    return ScoringOutput(
        fit_score=fit,
        timing_score=timing,
        relationship_score=rel,
        evidence_score=ev,
        total_score=total,
        sales_ready=sales_ready,
        reasoning={
            "fit": fit_detail,
            "timing": timing_detail,
            "relationship": rel_detail,
            "evidence": ev_detail,
            "high_confidence_signal_count": len(high_conf),
            "unique_evidence_url_count": len(unique_urls),
            "sales_ready_rule": "total>=70 AND >=2 signals at conf>=0.65 AND >=2 unique URLs",
            "near_miss": near_miss,
            "needs_one_more": needs_one_more,
        },
    )


def load_default_icp(db: Session) -> ICPProfile | None:
    return db.scalar(select(ICPProfile).where(ICPProfile.name == "default"))
