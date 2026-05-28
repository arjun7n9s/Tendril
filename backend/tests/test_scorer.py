"""Scoring boundary tests."""

from __future__ import annotations

from datetime import date

from app.models.account import Account
from app.models.enums import AccountStatus, SignalType
from app.models.icp import ICPProfile
from app.models.signal import Signal
from app.services.scorer import ScoringInput, compute_scores


def _make_signal(
    *, signal_type: SignalType, confidence: float, evidence_url: str, recency_days: int = 5
) -> Signal:
    return Signal(
        scan_id="scan_x",
        account_id="acc_x",
        signal_type=signal_type,
        title=signal_type.value,
        evidence_url=evidence_url,
        confidence=confidence,
        observed_at=date.today(),
        recency_days=recency_days,
    )


def test_sales_ready_requires_all_three_conditions() -> None:
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        industry="fintech",
        company_size="201-500",
        status=AccountStatus.target,
        metadata_json={"tech_keywords": ["kafka", "snowflake"]},
    )
    icp = ICPProfile(
        name="default",
        industries_json=["fintech"],
        company_sizes_json=["201-500"],
        regions_json=[],
        target_roles_json=[],
        tech_keywords_json=["kafka", "snowflake", "dbt"],
        pain_keywords_json=[],
        competitor_keywords_json=[],
    )
    signals = [
        _make_signal(
            signal_type=SignalType.hiring, confidence=0.85, evidence_url="https://acme.com/c1"
        ),
        _make_signal(
            signal_type=SignalType.migration, confidence=0.75, evidence_url="https://acme.com/blog"
        ),
        _make_signal(
            signal_type=SignalType.product_launch,
            confidence=0.7,
            evidence_url="https://news.example.com/launch",
        ),
    ]
    out = compute_scores(ScoringInput(account=account, signals=signals, icp=icp, has_champion=True))
    assert out.fit_score <= 30
    assert out.timing_score <= 30
    assert out.relationship_score <= 20
    assert out.evidence_score <= 20
    assert out.total_score == out.fit_score + out.timing_score + out.relationship_score + out.evidence_score
    assert out.sales_ready is True
    assert out.reasoning["high_confidence_signal_count"] >= 2
    assert out.reasoning["unique_evidence_url_count"] >= 2


def test_not_sales_ready_when_only_one_high_confidence_signal() -> None:
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        industry="fintech",
        status=AccountStatus.target,
        metadata_json={"tech_keywords": ["kafka"]},
    )
    icp = ICPProfile(
        name="default",
        industries_json=["fintech"],
        company_sizes_json=[],
        tech_keywords_json=["kafka"],
        regions_json=[],
        target_roles_json=[],
        pain_keywords_json=[],
        competitor_keywords_json=[],
    )
    signals = [
        _make_signal(
            signal_type=SignalType.hiring, confidence=0.9, evidence_url="https://acme.com/c1"
        ),
        _make_signal(
            signal_type=SignalType.tech_stack, confidence=0.5, evidence_url="https://acme.com/c2"
        ),
    ]
    out = compute_scores(ScoringInput(account=account, signals=signals, icp=icp, has_champion=False))
    assert out.sales_ready is False


def test_score_caps_are_enforced_with_many_signals() -> None:
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        status=AccountStatus.target,
        metadata_json={},
    )
    signals = [
        _make_signal(
            signal_type=SignalType.funding,
            confidence=0.9,
            evidence_url=f"https://acme.com/{i}",
        )
        for i in range(20)
    ]
    out = compute_scores(ScoringInput(account=account, signals=signals, icp=None, has_champion=True))
    assert out.timing_score <= 30
    assert out.evidence_score <= 20
    assert out.relationship_score <= 20
    assert out.total_score <= 100



def test_two_strong_recent_hot_signals_clear_sales_ready_threshold() -> None:
    """Phase 5: 2 high-confidence hot signals from a fit account should be
    enough to be sales_ready, even from a single host. Mirrors the live
    Ramp run that produced funding + leadership_change at conf 0.85.
    """
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        industry="fintech",
        company_size="1001-5000",
        status=AccountStatus.target,
        metadata_json={
            "tech_keywords": ["kafka", "snowflake", "dbt", "observability"]
        },
    )
    icp = ICPProfile(
        name="default",
        industries_json=["fintech"],
        company_sizes_json=["1001-5000"],
        regions_json=[],
        target_roles_json=[],
        tech_keywords_json=["kafka", "snowflake", "dbt", "observability"],
        pain_keywords_json=[],
        competitor_keywords_json=[],
    )
    signals = [
        _make_signal(
            signal_type=SignalType.funding,
            confidence=0.85,
            evidence_url="https://acme.com/blog/funding",
            recency_days=2,
        ),
        _make_signal(
            signal_type=SignalType.leadership_change,
            confidence=0.85,
            evidence_url="https://acme.com/blog/news",
            recency_days=5,
        ),
    ]
    out = compute_scores(
        ScoringInput(account=account, signals=signals, icp=icp, has_champion=True)
    )
    # Each individual subscore must be capped properly.
    assert 0 <= out.fit_score <= 30
    assert 0 <= out.timing_score <= 30
    assert 0 <= out.relationship_score <= 20
    assert 0 <= out.evidence_score <= 20
    # The whole point: sparse but strong should be sales-ready.
    assert out.sales_ready is True, out.reasoning
    assert out.total_score >= 70


def test_low_confidence_signals_do_not_trigger_sales_ready() -> None:
    """Sanity inverse: many noisy signals should NOT reach sales-ready."""
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        industry="fintech",
        status=AccountStatus.target,
        metadata_json={"tech_keywords": ["kafka"]},
    )
    icp = ICPProfile(
        name="default",
        industries_json=["fintech"],
        company_sizes_json=[],
        regions_json=[],
        target_roles_json=[],
        tech_keywords_json=["kafka"],
        pain_keywords_json=[],
        competitor_keywords_json=[],
    )
    signals = [
        _make_signal(
            signal_type=SignalType.other,
            confidence=0.5,
            evidence_url=f"https://acme.com/x{i}",
        )
        for i in range(6)
    ]
    out = compute_scores(
        ScoringInput(account=account, signals=signals, icp=icp, has_champion=False)
    )
    assert out.sales_ready is False


def test_old_signals_get_recency_decay() -> None:
    """A signal observed 6 months ago contributes far less than one observed
    yesterday, even if both are 'hot'.
    """
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        industry="fintech",
        status=AccountStatus.target,
        metadata_json={"tech_keywords": []},
    )
    fresh = [
        _make_signal(
            signal_type=SignalType.funding,
            confidence=0.85,
            evidence_url="https://acme.com/a",
            recency_days=3,
        ),
        _make_signal(
            signal_type=SignalType.migration,
            confidence=0.85,
            evidence_url="https://acme.com/b",
            recency_days=5,
        ),
    ]
    stale = [
        _make_signal(
            signal_type=SignalType.funding,
            confidence=0.85,
            evidence_url="https://acme.com/a",
            recency_days=200,
        ),
        _make_signal(
            signal_type=SignalType.migration,
            confidence=0.85,
            evidence_url="https://acme.com/b",
            recency_days=200,
        ),
    ]
    fresh_out = compute_scores(
        ScoringInput(account=account, signals=fresh, icp=None, has_champion=False)
    )
    stale_out = compute_scores(
        ScoringInput(account=account, signals=stale, icp=None, has_champion=False)
    )
    assert fresh_out.timing_score > stale_out.timing_score


def test_near_miss_band_is_reported() -> None:
    """Accounts in the 55-69 total band must be flagged as near_miss with
    a list of what they need to clear.
    """
    account = Account(
        id="acc_x",
        name="Acme",
        domain="acme.com",
        industry="fintech",
        status=AccountStatus.target,
        metadata_json={"tech_keywords": ["kafka"]},
    )
    icp = ICPProfile(
        name="default",
        industries_json=["fintech"],
        company_sizes_json=[],
        regions_json=[],
        target_roles_json=[],
        tech_keywords_json=["kafka"],
        pain_keywords_json=[],
        competitor_keywords_json=[],
    )
    # One strong signal: should land in near_miss territory.
    signals = [
        _make_signal(
            signal_type=SignalType.hiring,
            confidence=0.8,
            evidence_url="https://acme.com/c",
            recency_days=7,
        )
    ]
    out = compute_scores(
        ScoringInput(account=account, signals=signals, icp=icp, has_champion=True)
    )
    assert out.sales_ready is False
    assert "needs_one_more" in out.reasoning
    assert out.reasoning["needs_one_more"]
