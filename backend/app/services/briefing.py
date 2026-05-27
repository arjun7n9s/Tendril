"""Mock briefing + outreach generation.

Phase 2: deterministic generation from stored signals + score. Phase 4
swaps the implementation to call AI/ML API behind the same surface.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.account import Account
from app.models.helpers import as_str
from app.models.score import Score
from app.models.signal import Signal


@dataclass
class BriefDraft:
    title: str
    executive_summary: str
    why_now: str
    key_evidence: list[dict]
    risks: list[str]
    recommended_next_steps: list[str]


@dataclass
class OutreachDraftPayload:
    subject: str
    body: str
    tone: str = "warm"


def _format_evidence(signals: list[Signal]) -> list[dict]:
    return [
        {
            "title": s.title,
            "summary": s.summary or "",
            "evidence_url": s.evidence_url,
            "confidence": round(s.confidence, 2),
            "signal_type": as_str(s.signal_type),
        }
        for s in signals
    ]


def generate_brief(account: Account, signals: list[Signal], score: Score) -> BriefDraft:
    top_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)[:5]
    evidence = _format_evidence(top_signals)

    facts = "; ".join(
        f"{s.title} (conf {s.confidence:.2f})" for s in top_signals[:3]
    ) or "No high-confidence signals yet."

    summary = (
        f"{account.name} shows a {score.total_score}/100 actionability score. "
        f"Fit {score.fit_score}, timing {score.timing_score}, "
        f"relationship {score.relationship_score}, evidence {score.evidence_score}. "
        f"Top facts: {facts}"
    )
    why_now = (
        "Multiple recent public signals point to data platform reliability "
        "investment, including hiring and migration evidence."
        if any(
            as_str(s.signal_type) in {"hiring", "migration", "product_launch"}
            for s in top_signals
        )
        else "No urgent timing trigger; treat as a warm research thread."
    )

    risks: list[str] = []
    if score.evidence_score < 10:
        risks.append("Limited corroborating evidence; expand source coverage before outreach.")
    if score.relationship_score < 8:
        risks.append("No strong relationship signal; lead with account-level context, not familiarity.")
    if not score.sales_ready:
        risks.append(
            "Account does not meet sales-ready threshold; treat as monitor or near-miss."
        )

    next_steps: list[str] = []
    if score.sales_ready:
        next_steps.append("Send a warm, account-level outreach draft for review.")
    next_steps.append("Re-scan in 7 days for new public signals.")
    if score.evidence_score < 10:
        next_steps.append("Expand discovery queries to include docs and review sites.")

    return BriefDraft(
        title=f"{account.name}: live GTM brief",
        executive_summary=summary,
        why_now=why_now,
        key_evidence=evidence,
        risks=risks,
        recommended_next_steps=next_steps,
    )


def generate_outreach(
    account: Account, brief: BriefDraft, top_signal: Signal | None
) -> OutreachDraftPayload:
    subject = f"Quick note on {account.name}'s data platform work"
    lines: list[str] = []
    lines.append(f"Hi there,")
    lines.append("")
    lines.append(
        f"Reading {account.name}'s recent public engineering content, it looks like the team "
        "is investing in data platform reliability and modernization."
    )
    if top_signal is not None:
        lines.append("")
        lines.append(
            f"One thread that stood out: {top_signal.title}. "
            f"Reference: {top_signal.evidence_url}"
        )
    lines.append("")
    lines.append(
        "If it would be useful, I am happy to share a short reliability migration checklist "
        "we put together with comparable fintech data teams."
    )
    lines.append("")
    lines.append("No pressure - happy to send it over and stay out of your way otherwise.")
    body = "\n".join(lines)
    return OutreachDraftPayload(subject=subject, body=body, tone="warm")
