"""Briefing and outreach generation.

Synchronous helpers (used in mock mode) build deterministic briefs from
stored signals + score. Async helpers (used in live mode) call the AIML
gateway through prompt templates with strict guardrails. Outreach drafts
always run through `guardrails.check_outreach` before persistence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from app.logging_setup import get_logger
from app.models.account import Account
from app.models.helpers import as_str
from app.models.score import Score
from app.models.signal import Signal
from app.prompts import load_prompt, render_prompt
from app.services.aiml_client import AimlClient

log = get_logger("briefing")


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


# ---------------- Mock / deterministic helpers ----------------


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


# ---------------- Live (AIML) helpers ----------------


def _signals_block(signals: list[Signal]) -> str:
    if not signals:
        return "(no signals)"
    parts: list[str] = []
    for s in sorted(signals, key=lambda x: x.confidence, reverse=True)[:8]:
        parts.append(
            f"- [{as_str(s.signal_type)} conf {s.confidence:.2f}] {s.title}\n"
            f"  evidence_url: {s.evidence_url}\n"
            f"  fact: {s.fact_text or ''}\n"
            f"  inference: {s.inference_text or ''}"
        )
    return "\n".join(parts)


def _safe_brief_payload(payload: dict, account: Account, fallback: BriefDraft) -> BriefDraft:
    """Coerce model output to BriefDraft, leaning on the deterministic fallback
    for any missing fields. Never trust unbounded model output verbatim.
    """
    title = (payload.get("title") or "").strip() or fallback.title
    if not title.startswith(account.name):
        title = f"{account.name}: GTM brief"

    exec_summary = (payload.get("executive_summary") or "").strip() or fallback.executive_summary
    why_now = (payload.get("why_now") or "").strip() or fallback.why_now

    key_evidence = payload.get("key_evidence")
    if not isinstance(key_evidence, list) or not key_evidence:
        key_evidence = fallback.key_evidence
    else:
        cleaned: list[dict] = []
        for item in key_evidence[:8]:
            if not isinstance(item, dict):
                continue
            ev_url = (item.get("evidence_url") or "").strip()
            if not ev_url:
                continue
            cleaned.append(
                {
                    "title": (item.get("title") or "").strip()[:512],
                    "evidence_url": ev_url,
                    "confidence": _coerce_float(item.get("confidence"), 0.5),
                    "signal_type": (item.get("signal_type") or "").strip() or None,
                    "summary": (item.get("summary") or "").strip() or None,
                }
            )
        key_evidence = cleaned or fallback.key_evidence

    risks = payload.get("risks")
    if not isinstance(risks, list) or not risks:
        risks = fallback.risks
    else:
        risks = [str(r).strip() for r in risks if str(r).strip()][:5]

    steps = payload.get("recommended_next_steps")
    if not isinstance(steps, list) or not steps:
        steps = fallback.recommended_next_steps
    else:
        steps = [str(s).strip() for s in steps if str(s).strip()][:5]

    return BriefDraft(
        title=title,
        executive_summary=exec_summary,
        why_now=why_now,
        key_evidence=key_evidence,
        risks=risks,
        recommended_next_steps=steps,
    )


def _coerce_float(value, default: float) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, f))


async def generate_brief_live(
    *,
    aiml: AimlClient,
    account: Account,
    signals: list[Signal],
    score: Score,
    graph_context: str = "",
) -> tuple[BriefDraft, dict]:
    """Call AIML to draft a brief, falling back on bad output.

    Returns (brief, telemetry) where telemetry includes model id and ms.
    """
    fallback = generate_brief(account, signals, score)
    system_prompt = load_prompt("generate_brief.system.md")
    user_prompt = render_prompt(
        "generate_brief.user.md",
        account_name=account.name,
        account_industry=account.industry or "",
        account_domain=account.domain or "",
        total_score=score.total_score,
        fit_score=score.fit_score,
        timing_score=score.timing_score,
        relationship_score=score.relationship_score,
        evidence_score=score.evidence_score,
        sales_ready=str(score.sales_ready).lower(),
        signals_block=_signals_block(signals),
        graph_context=graph_context or "(empty)",
    )
    try:
        payload, meta = await aiml.complete_json(
            slot="briefing",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=900,
            temperature=0.2,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("briefing.live_failed", error=str(exc))
        return fallback, {"model": None, "duration_ms": 0, "fallback": True}

    brief = _safe_brief_payload(payload, account, fallback)
    return brief, {"model": meta.model, "duration_ms": meta.duration_ms, "fallback": False}


async def generate_outreach_live(
    *,
    aiml: AimlClient,
    account: Account,
    signals: list[Signal],
    top_signal: Signal | None,
) -> tuple[OutreachDraftPayload, dict]:
    """Call AIML to draft outreach, falling back on bad output.

    Final guardrails (`guardrails.check_outreach`) run on the result by the
    caller, never inside this function.
    """
    fallback_brief = generate_brief(
        account,
        signals,
        _MinimalScore(
            total_score=70,
            fit_score=15,
            timing_score=15,
            relationship_score=10,
            evidence_score=10,
            sales_ready=True,
        ),
    )
    fallback_outreach = generate_outreach(account, fallback_brief, top_signal)

    system_prompt = load_prompt("generate_outreach.system.md")
    other_signals_block = "\n".join(
        f"- {s.title} (conf {s.confidence:.2f}, {as_str(s.signal_type)})"
        for s in signals[:5]
        if s is not top_signal
    ) or "(none)"
    user_prompt = render_prompt(
        "generate_outreach.user.md",
        account_name=account.name,
        account_industry=account.industry or "",
        top_signal_type=as_str(top_signal.signal_type) if top_signal else "other",
        top_signal_title=(top_signal.title if top_signal else "Public web evidence"),
        top_signal_fact=(top_signal.fact_text or "" if top_signal else ""),
        top_signal_url=(top_signal.evidence_url if top_signal else ""),
        other_signals=other_signals_block,
    )
    try:
        payload, meta = await aiml.complete_json(
            slot="draft",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=400,
            temperature=0.4,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("outreach.live_failed", error=str(exc))
        return fallback_outreach, {"model": None, "duration_ms": 0, "fallback": True}

    subject = (payload.get("subject") or "").strip() if isinstance(payload, dict) else ""
    body = (payload.get("body") or "").strip() if isinstance(payload, dict) else ""
    if not subject or not body:
        return fallback_outreach, {"model": meta.model, "duration_ms": meta.duration_ms, "fallback": True}

    return (
        OutreachDraftPayload(subject=subject[:512], body=body[:2000], tone="warm"),
        {"model": meta.model, "duration_ms": meta.duration_ms, "fallback": False},
    )


@dataclass
class _MinimalScore:
    """Drop-in for the deterministic generator when we only have signals."""

    total_score: int
    fit_score: int
    timing_score: int
    relationship_score: int
    evidence_score: int
    sales_ready: bool
