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


def _memory_grounding_line(graph_context: str) -> str:
    """Pick the most useful single line from a graph_context block.

    Works for both memory backends:
    - JSONL recall emits a "Recurring themes over time: ..." line first.
    - Cognee GRAPH_COMPLETION emits a synthesized answer as the first bullet
      under "Prior account memory:".

    Returns an empty string when there's nothing to surface.
    """
    if not graph_context or graph_context in ("", "(empty)"):
        return ""
    lines = [ln.strip() for ln in graph_context.splitlines() if ln.strip()]
    # Prefer an explicit recurring-themes summary if present.
    for ln in lines:
        if ln.lower().startswith("recurring themes"):
            return ln
    # Otherwise take the first recalled memory bullet.
    for ln in lines:
        if ln.startswith("- "):
            return ln[2:].strip()
    return ""


def generate_brief(
    account: Account,
    signals: list[Signal],
    score: Score,
    graph_context: str = "",
) -> BriefDraft:
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
    # Ground "why now" in accumulated account memory when the graph recall
    # surfaced prior context. This is the read side of the memory loop made
    # visible in the deterministic brief too, so mock demos show Cognee's value.
    memory_line = _memory_grounding_line(graph_context)
    if memory_line:
        why_now = f"{why_now} Account memory: {memory_line}"

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
    account: Account,
    brief: BriefDraft,
    top_signal: Signal | None,
    tone: str = "warm",
) -> OutreachDraftPayload:
    tone = (tone or "warm").lower()
    spec = _TONE_SPECS.get(tone, _TONE_SPECS["warm"])

    subject = spec["subject"](account)
    lines: list[str] = []
    lines.append(spec["greeting"])
    lines.append("")
    lines.append(spec["opener"](account))
    if top_signal is not None:
        lines.append("")
        lines.append(
            f"{spec['signal_lead']} {top_signal.title}. "
            f"Reference: {top_signal.evidence_url}"
        )
    lines.append("")
    lines.append(spec["offer"])
    lines.append("")
    lines.append(spec["closer"])
    body = "\n".join(lines)
    return OutreachDraftPayload(subject=subject, body=body, tone=tone)


# Deterministic tone presets so the tone toggle changes the draft even
# without a live model (mock mode / AIML down). Each preset shifts the
# subject line, greeting, framing, offer, and sign-off register while
# staying inside the same ethical guardrails (no false familiarity,
# account-level only, low-pressure offer).
_TONE_SPECS: dict[str, dict] = {
    "warm": {
        "subject": lambda a: f"Quick note on {a.name}'s data platform work",
        "greeting": "Hi there,",
        "opener": lambda a: (
            f"Reading {a.name}'s recent public engineering content, it looks like the team "
            "is investing in data platform reliability and modernization."
        ),
        "signal_lead": "One thread that stood out:",
        "offer": (
            "If it would be useful, I'm happy to share a short reliability migration "
            "checklist we put together with comparable fintech data teams."
        ),
        "closer": "No pressure - happy to send it over and stay out of your way otherwise.",
    },
    "technical": {
        "subject": lambda a: f"{a.name}'s data platform reliability + migration patterns",
        "greeting": "Hi team,",
        "opener": lambda a: (
            f"Your recent public engineering work suggests {a.name} is hardening its data "
            "platform - reliability, pipeline observability, and migration tradeoffs."
        ),
        "signal_lead": "The detail that caught my eye:",
        "offer": (
            "If helpful, I can share a technical teardown of how similar teams handled "
            "schema migration, backfills, and SLA monitoring without downtime."
        ),
        "closer": "Happy to go deep on the architecture or stay async - your call.",
    },
    "executive": {
        "subject": lambda a: f"Accelerating {a.name}'s data platform initiative",
        "greeting": "Hello,",
        "opener": lambda a: (
            f"It looks like {a.name} is making a strategic investment in its data platform, "
            "which usually maps to faster product velocity and lower operational risk."
        ),
        "signal_lead": "What signaled this to us:",
        "offer": (
            "If it's useful, I can share how comparable teams measured ROI and de-risked "
            "the rollout at the leadership level."
        ),
        "closer": "Happy to find 15 minutes whenever the timing works.",
    },
    "concise": {
        "subject": lambda a: f"{a.name} data platform - quick idea",
        "greeting": "Hi,",
        "opener": lambda a: (
            f"Noticed {a.name} is investing in data platform reliability."
        ),
        "signal_lead": "Specifically:",
        "offer": "Want a short migration checklist from similar fintech teams?",
        "closer": "No pressure either way.",
    },
}


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
    tone: str = "warm",
) -> tuple[OutreachDraftPayload, dict]:
    """Call AIML to draft outreach, falling back on bad output.

    Final guardrails (`guardrails.check_outreach`) run on the result by the
    caller, never inside this function.
    """
    tone = (tone or "warm").lower()
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
    fallback_outreach = generate_outreach(account, fallback_brief, top_signal, tone)

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
        tone=tone,
        tone_guidance=_TONE_GUIDANCE.get(tone, _TONE_GUIDANCE["warm"]),
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
        OutreachDraftPayload(subject=subject[:512], body=body[:2000], tone=tone),
        {"model": meta.model, "duration_ms": meta.duration_ms, "fallback": False},
    )


# Per-tone guidance injected into the live outreach prompt. Mirrors the
# deterministic presets so live and mock drafts shift register consistently.
_TONE_GUIDANCE: dict[str, str] = {
    "warm": (
        "Tone: WARM. Friendly and human, lightly enthusiastic but never pushy. "
        "Conversational greeting, a genuine low-pressure offer to help."
    ),
    "technical": (
        "Tone: TECHNICAL. Speak engineer-to-engineer. Reference concrete systems "
        "and tradeoffs (pipelines, schema migration, observability, SLAs). Precise, "
        "no fluff, credible. Offer a technical resource, not a sales call."
    ),
    "executive": (
        "Tone: EXECUTIVE. Concise and outcome-oriented. Frame around business impact "
        "(velocity, risk, ROI), not implementation detail. Respect their time; offer a "
        "brief, senior-level conversation."
    ),
    "concise": (
        "Tone: CONCISE. Maximum brevity. 3-4 short sentences total. One observation, "
        "one offer, one low-pressure close. No preamble."
    ),
}


@dataclass
class _MinimalScore:
    """Drop-in for the deterministic generator when we only have signals."""

    total_score: int
    fit_score: int
    timing_score: int
    relationship_score: int
    evidence_score: int
    sales_ready: bool
