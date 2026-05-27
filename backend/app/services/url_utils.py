"""URL canonicalization, dedup, and source-type classification.

Used by source_discovery to keep the candidate URL set clean.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import tldextract

from app.models.enums import SourceType

# Hosts we never want to scrape from SERP results.
_GOOGLE_HOSTS = {
    "google.com",
    "www.google.com",
    "webcache.googleusercontent.com",
    "translate.google.com",
    "policies.google.com",
    "support.google.com",
    "accounts.google.com",
}

# Known low-quality aggregators / spammy sources (extend as needed).
_BLOCKED_HOSTS = {
    "scribd.com",
    "youtube.com",  # noisy for our use case
    "facebook.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "linkedin.com",  # explicitly out of scope per plan
}

# Domains we treat as "news/press" by default.
_NEWS_HOSTS = {
    "techcrunch.com",
    "businesswire.com",
    "prnewswire.com",
    "reuters.com",
    "bloomberg.com",
    "venturebeat.com",
    "forbes.com",
    "theverge.com",
}

_DOC_HOSTS = {"readthedocs.io", "readthedocs.org", "gitbook.io"}


@dataclass(frozen=True)
class ClassifiedUrl:
    url: str
    canonical: str
    host: str
    registered_domain: str
    source_type: SourceType


def _safe_split(url: str):
    return urlsplit(url.strip())


def canonicalize(url: str) -> str:
    """Return a normalized URL safe for dedup.

    - Lowercases scheme and host
    - Strips default ports
    - Drops fragments and tracking-style query params
    - Removes trailing slashes on the path
    """
    if not url:
        return ""
    parts = _safe_split(url)
    if not parts.scheme or not parts.netloc:
        return url.strip()

    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if not host:
        return url.strip()

    # Strip default ports.
    port = parts.port
    if port and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Drop common tracking query params.
    query_pairs = []
    if parts.query:
        for pair in parts.query.split("&"):
            if not pair or "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            if k.lower() in {
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_content",
                "utm_term",
                "gclid",
                "fbclid",
                "ref",
                "ref_src",
                "_ga",
            }:
                continue
            query_pairs.append(f"{k}={v}")
    query = "&".join(query_pairs)

    return urlunsplit((scheme, netloc, path, query, ""))


def host_of(url: str) -> str:
    parts = _safe_split(url)
    return (parts.hostname or "").lower()


def registered_domain_of(url: str) -> str:
    host = host_of(url)
    if not host:
        return ""
    extracted = tldextract.extract(host)
    if not extracted.domain:
        return host
    return ".".join(p for p in [extracted.domain, extracted.suffix] if p)


def is_blocked(url: str) -> bool:
    host = host_of(url)
    if not host:
        return True
    if host in _GOOGLE_HOSTS:
        return True
    if host in _BLOCKED_HOSTS:
        return True
    return False


def classify(url: str, *, account_domain: str | None = None) -> SourceType:
    """Best-guess source type from URL shape."""
    parts = _safe_split(url)
    host = (parts.hostname or "").lower()
    path = (parts.path or "").lower()

    if host == "github.com" or host.endswith(".github.com") or host.endswith(".github.io"):
        return SourceType.github
    if host in _NEWS_HOSTS or any(host.endswith("." + n) for n in _NEWS_HOSTS):
        return SourceType.news
    if host in _DOC_HOSTS or any(host.endswith("." + d) for d in _DOC_HOSTS):
        return SourceType.docs

    # Path-based hints
    if any(seg in path for seg in ("/careers", "/jobs", "/work-with-us", "/join-us")):
        return SourceType.careers
    if any(seg in path for seg in ("/blog", "/engineering", "/inside-")):
        return SourceType.blog
    if any(seg in path for seg in ("/docs", "/documentation", "/reference", "/guide")):
        return SourceType.docs
    if any(seg in path for seg in ("/press", "/news", "/newsroom", "/press-release")):
        return SourceType.news
    if "review" in path or "g2.com" in host or "trustradius" in host:
        return SourceType.review

    # Same registered domain as the account → company site.
    if account_domain:
        target_rd = registered_domain_of(f"https://{account_domain}")
        this_rd = registered_domain_of(url)
        if target_rd and this_rd and target_rd == this_rd:
            return SourceType.company_site

    return SourceType.other


def classify_url(url: str, *, account_domain: str | None = None) -> ClassifiedUrl | None:
    canonical = canonicalize(url)
    if not canonical or is_blocked(canonical):
        return None
    return ClassifiedUrl(
        url=url,
        canonical=canonical,
        host=host_of(canonical),
        registered_domain=registered_domain_of(canonical),
        source_type=classify(canonical, account_domain=account_domain),
    )


def dedupe(urls: list[ClassifiedUrl]) -> list[ClassifiedUrl]:
    seen: set[str] = set()
    out: list[ClassifiedUrl] = []
    for u in urls:
        if u.canonical in seen:
            continue
        seen.add(u.canonical)
        out.append(u)
    return out


# ---------- SERP-specific helpers ----------

# Google's redirector form: /url?q=https%3A//target.com/&sa=...
_GOOGLE_REDIRECT_PREFIX = ("/url?q=", "/url?url=")


def extract_target_from_google_redirect(href: str) -> str | None:
    if not href:
        return None
    for prefix in _GOOGLE_REDIRECT_PREFIX:
        if href.startswith(prefix):
            rest = href[len(prefix):]
            target = rest.split("&", 1)[0]
            try:
                return unquote(target)
            except Exception:  # noqa: BLE001
                return target
    return None


_HTTPISH = re.compile(r"^https?://", re.IGNORECASE)


def is_absolute_http(url: str) -> bool:
    return bool(_HTTPISH.match(url or ""))
