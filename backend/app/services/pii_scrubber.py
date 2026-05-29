"""Transcript PII scrubbing.

Raw spoken transcripts routinely contain emails, phone numbers, addresses, and
casual personal references. Per the product's enterprise posture, nothing raw
should reach the memory layer. This module redacts obvious identifiers and
flags transcript sections that mention sensitive personal attributes so they
are never used for outreach.

The scrubber is deterministic and dependency-free (regex based) so it runs in
mock mode and offline without any provider call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.enums import PrivacyStatus

_REDACTED = "[redacted]"

# Conservative detectors. We err toward over-redaction for memory safety.
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)\d{3}[\s.\-]?\d{4}(?!\d)"
)
_URL_RE = re.compile(r"https?://[^\s]+")
_SSN_RE = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_CREDIT_CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,16}(?!\d)")
_STREET_RE = re.compile(
    r"\b\d{1,5}\s+([A-Z][a-zA-Z]+\s){1,3}"
    r"(Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Lane|Ln|Drive|Dr|Court|Ct|"
    r"Way|Parkway|Pkwy|Plaza|Square|Sq|Terrace|Place|Pl|Circle|Cir|Highway|Hwy)\b",
    re.IGNORECASE,
)

# Sensitive personal attributes. A section mentioning these is flagged and
# excluded from outreach use.
_SENSITIVE_TERMS = (
    "religion",
    "religious",
    "ethnic",
    "ethnicity",
    "racial",
    " race ",
    "sexual orientation",
    "gender identity",
    "political affiliation",
    "health condition",
    "medical history",
    "disability",
    "pregnan",
    "immigration status",
)


@dataclass
class ScrubResult:
    scrubbed_text: str
    pii_status: PrivacyStatus
    findings: dict[str, int] = field(default_factory=dict)
    sensitive: bool = False


def _redact(pattern: re.Pattern[str], text: str, label: str, findings: dict[str, int]) -> str:
    count = 0

    def _sub(_m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return _REDACTED

    out = pattern.sub(_sub, text)
    if count:
        findings[label] = findings.get(label, 0) + count
    return out


def scrub_text(text: str | None) -> ScrubResult:
    """Redact identifiers from `text` and flag sensitive content.

    Returns the scrubbed text, a privacy status, and a findings map of how many
    of each identifier type were redacted.
    """
    if not text:
        return ScrubResult(scrubbed_text="", pii_status=PrivacyStatus.clean, findings={})

    findings: dict[str, int] = {}
    out = text
    # Order matters: redact structured identifiers before free phone digits.
    out = _redact(_EMAIL_RE, out, "email", findings)
    out = _redact(_URL_RE, out, "url", findings)
    out = _redact(_SSN_RE, out, "ssn", findings)
    out = _redact(_CREDIT_CARD_RE, out, "card", findings)
    out = _redact(_STREET_RE, out, "address", findings)
    out = _redact(_PHONE_RE, out, "phone", findings)

    lower = out.lower()
    sensitive = any(term in lower for term in _SENSITIVE_TERMS)

    if sensitive:
        status = PrivacyStatus.sensitive_blocked
    elif findings:
        status = PrivacyStatus.scrubbed
    else:
        status = PrivacyStatus.clean

    return ScrubResult(
        scrubbed_text=out,
        pii_status=status,
        findings=findings,
        sensitive=sensitive,
    )


def scrub_segments(segments: list[dict] | None) -> tuple[list[dict], dict[str, int], bool]:
    """Scrub the `text` field of each transcript segment.

    Returns (scrubbed_segments, aggregate_findings, any_sensitive).
    """
    if not segments:
        return [], {}, False
    aggregate: dict[str, int] = {}
    any_sensitive = False
    out: list[dict] = []
    for seg in segments:
        res = scrub_text(seg.get("text"))
        for k, v in res.findings.items():
            aggregate[k] = aggregate.get(k, 0) + v
        any_sensitive = any_sensitive or res.sensitive
        out.append(
            {
                **seg,
                "text": res.scrubbed_text,
                "privacy_status": res.pii_status.value,
            }
        )
    return out, aggregate, any_sensitive
