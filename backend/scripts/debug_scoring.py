"""Sanity-check the scoring rubric against representative scenarios.

Usage:
    uv run python -m scripts.debug_scoring
    uv run python scripts/debug_scoring.py
"""

from __future__ import annotations

# Ensure `import app.*` works whether invoked as a module or as a file.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date

from app.models.account import Account
from app.models.enums import AccountStatus, SignalType
from app.models.icp import ICPProfile
from app.models.signal import Signal
from app.services.scorer import ScoringInput, compute_scores


def _signal(signal_type: SignalType, confidence: float, url: str, recency_days: int = 5) -> Signal:
    return Signal(
        scan_id="scan_x",
        account_id="acc_x",
        signal_type=signal_type,
        title=signal_type.value,
        evidence_url=url,
        confidence=confidence,
        observed_at=date.today(),
        recency_days=recency_days,
    )


def _print_score(label: str, out) -> None:
    print(f"\n=== {label} ===")
    print(
        f"  fit={out.fit_score} timing={out.timing_score} "
        f"rel={out.relationship_score} ev={out.evidence_score} "
        f"total={out.total_score} sales_ready={out.sales_ready}"
    )
    if not out.sales_ready:
        print(f"  needs_one_more: {out.reasoning.get('needs_one_more')}")


def main() -> None:
    fintech_account = Account(
        id="acc_ramp",
        name="Ramp",
        domain="ramp.com",
        industry="fintech",
        company_size="1001-5000",
        status=AccountStatus.target,
        metadata_json={
            "tech_keywords": ["kafka", "snowflake", "dbt", "observability"]
        },
    )
    fintech_icp = ICPProfile(
        name="default",
        industries_json=["fintech"],
        company_sizes_json=["1001-5000"],
        regions_json=[],
        target_roles_json=[],
        tech_keywords_json=["kafka", "snowflake", "dbt", "observability"],
        pain_keywords_json=[],
        competitor_keywords_json=[],
    )

    # Phase 4 live Ramp scenario: 2 hot signals from one host, conf 0.85.
    ramp_signals = [
        _signal(SignalType.funding, 0.85, "https://ramp.com/blog/valuation", 2),
        _signal(SignalType.leadership_change, 0.85, "https://ramp.com/blog/news", 5),
    ]
    _print_score(
        "Ramp live (2 hot signals, 1 host, champion present)",
        compute_scores(
            ScoringInput(
                account=fintech_account,
                signals=ramp_signals,
                icp=fintech_icp,
                has_champion=True,
            )
        ),
    )

    # Sparse but multi-host.
    multi_host = [
        _signal(SignalType.funding, 0.85, "https://ramp.com/blog/valuation", 2),
        _signal(SignalType.product_launch, 0.78, "https://techcrunch.com/x", 4),
    ]
    _print_score(
        "Ramp + tech-press (2 hot, 2 hosts, no champion)",
        compute_scores(
            ScoringInput(
                account=fintech_account,
                signals=multi_host,
                icp=fintech_icp,
                has_champion=False,
            )
        ),
    )

    # Noisy: many low-confidence signals.
    noisy = [
        _signal(SignalType.other, 0.5, f"https://ramp.com/n{i}", 30)
        for i in range(8)
    ]
    _print_score(
        "Noisy (8 conf 0.5 signals, 1 host)",
        compute_scores(
            ScoringInput(
                account=fintech_account,
                signals=noisy,
                icp=fintech_icp,
                has_champion=False,
            )
        ),
    )

    # Stale: 2 hot signals but observed 200 days ago.
    stale = [
        _signal(SignalType.funding, 0.85, "https://ramp.com/old1", 200),
        _signal(SignalType.migration, 0.85, "https://ramp.com/old2", 200),
    ]
    _print_score(
        "Stale (2 hot but 200 days old, no champion)",
        compute_scores(
            ScoringInput(
                account=fintech_account,
                signals=stale,
                icp=fintech_icp,
                has_champion=False,
            )
        ),
    )

    # Out of ICP: same signals but wrong industry.
    off_icp_account = Account(
        id="acc_off",
        name="OffTopic",
        domain="off.com",
        industry="retail",
        company_size="11-50",
        status=AccountStatus.target,
        metadata_json={"tech_keywords": []},
    )
    _print_score(
        "Out of ICP (same hot signals, wrong industry)",
        compute_scores(
            ScoringInput(
                account=off_icp_account,
                signals=ramp_signals,
                icp=fintech_icp,
                has_champion=False,
            )
        ),
    )


if __name__ == "__main__":
    main()
