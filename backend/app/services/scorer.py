"""Scoring service.

Implements the 100-point scoring rubric and sales-ready rule:
    sales_ready = total >= 70
        AND signals with confidence >= 0.65 count >= 2
        AND unique evidence URLs >= 2

Returns reasoning JSON so the brief can quote the rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
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


def score_fit(account: Account, icp: ICPProfile | None) -> tuple[int, dict[str, Any]]:
    if icp is None:
        return 5, {"reason": "no ICP profile"}

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
        score += 5
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
    if not signals:
        return 0, {"reason": "no signals"}
    score = 0
    detail: dict[str, Any] = {"hot": [], "warm": [], "recent": 0}
    for s in signals:
        stype = as_str(s.signal_type)
        if stype in _HOT_TIMING_TYPES:
            score += 8
            detail["hot"].append(stype)
        elif stype in _WARM_TIMING_TYPES:
            score += 4
            detail["warm"].append(stype)
        else:
            score += 1
        if s.recency_days is not None and s.recency_days <= 14:
            score += 2
            detail["recent"] += 1
    return min(score, 30), detail


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
    if not signals:
        return 0, {"reason": "no signals"}
    unique_urls = {s.evidence_url for s in signals if s.evidence_url}
    avg_conf = sum(s.confidence for s in signals) / max(len(signals), 1)
    unique_hosts = {url.split("/")[2] for url in unique_urls if "://" in url}
    score = 0
    detail: dict[str, Any] = {
        "unique_url_count": len(unique_urls),
        "unique_host_count": len(unique_hosts),
        "avg_confidence": round(avg_conf, 3),
    }
    score += min(len(unique_urls) * 3, 9)
    score += min(len(unique_hosts) * 2, 6)
    if avg_conf >= 0.75:
        score += 5
    elif avg_conf >= 0.6:
        score += 3
    elif avg_conf >= 0.5:
        score += 1
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
        },
    )


def load_default_icp(db: Session) -> ICPProfile | None:
    return db.scalar(select(ICPProfile).where(ICPProfile.name == "default"))
