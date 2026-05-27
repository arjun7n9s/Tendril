"""Outreach guardrails.

Rejects drafts that violate the product's safety rules:
- Do not say "I saw you..."
- Do not mention competitor usage unless backed by evidence
- Do not fabricate familiarity
- Do not expose private/sensitive personal attributes
- Keep it short
"""

from __future__ import annotations

from dataclasses import dataclass, field

_BANNED_PHRASES = [
    "i saw you",
    "i noticed you",
    "i saw your",
    "i noticed your",
    "your wife",
    "your husband",
    "your kids",
    "your salary",
    "your address",
    "your home",
]

_SENSITIVE_TERMS = [
    "religion",
    "political",
    "ethnic",
    "race ",
    "racial",
    "gender",
    "sexual orientation",
    "health condition",
    "medical",
]


@dataclass
class GuardrailResult:
    ok: bool
    notes: list[str] = field(default_factory=list)


def check_outreach(
    *,
    subject: str,
    body: str,
    competitor_keywords: list[str] | None = None,
    evidence_urls: list[str] | None = None,
) -> GuardrailResult:
    notes: list[str] = []
    text = f"{subject}\n{body}".lower()

    for phrase in _BANNED_PHRASES:
        if phrase in text:
            notes.append(f"banned_phrase:{phrase!r}")

    for term in _SENSITIVE_TERMS:
        if term in text:
            notes.append(f"sensitive_term:{term!r}")

    # Competitor mentions only allowed if at least one evidence URL is provided.
    if competitor_keywords:
        for kw in competitor_keywords:
            if kw and kw.lower() in text and not evidence_urls:
                notes.append(f"competitor_mentioned_without_evidence:{kw}")

    if len(body) > 1500:
        notes.append("too_long")

    return GuardrailResult(ok=not notes, notes=notes)
