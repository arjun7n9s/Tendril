"""URL canonicalization, classification, and dedup."""

from __future__ import annotations

from app.models.enums import SourceType
from app.services.url_utils import (
    canonicalize,
    classify,
    classify_url,
    dedupe,
    extract_target_from_google_redirect,
    is_blocked,
    registered_domain_of,
)


def test_canonicalize_strips_default_port_fragment_and_tracking() -> None:
    raw = "HTTPS://Acme.COM:443/Blog/?utm_source=google&utm_medium=cpc&keep=1#frag"
    out = canonicalize(raw)
    assert out == "https://acme.com/Blog?keep=1"


def test_canonicalize_handles_trailing_slash() -> None:
    assert canonicalize("https://acme.com/blog/") == "https://acme.com/blog"
    assert canonicalize("https://acme.com/") == "https://acme.com/"


def test_extract_target_from_google_redirect() -> None:
    href = "/url?q=https%3A%2F%2Facme.com%2Fpath&sa=U&ved=xxx"
    assert extract_target_from_google_redirect(href) == "https://acme.com/path"
    assert extract_target_from_google_redirect("https://acme.com") is None


def test_is_blocked_filters_google_and_linkedin() -> None:
    assert is_blocked("https://www.google.com/search?q=foo")
    assert is_blocked("https://linkedin.com/in/someone")
    assert not is_blocked("https://acme.com/careers")


def test_classify_by_path_and_host() -> None:
    assert classify("https://acme.com/careers/engineer") == SourceType.careers
    assert classify("https://acme.com/engineering/scaling") == SourceType.blog
    assert classify("https://acme.com/docs/intro") == SourceType.docs
    assert classify("https://github.com/acme/repo") == SourceType.github
    assert classify("https://techcrunch.com/2026/05/27/acme") == SourceType.news
    assert (
        classify("https://acme.com/about", account_domain="acme.com")
        == SourceType.company_site
    )


def test_classify_url_returns_none_for_blocked() -> None:
    assert classify_url("https://www.google.com/search?q=x") is None
    out = classify_url("https://acme.com/careers/se", account_domain="acme.com")
    assert out is not None
    assert out.source_type == SourceType.careers
    assert out.canonical == "https://acme.com/careers/se"


def test_dedupe_preserves_first_occurrence() -> None:
    a = classify_url("https://acme.com/x")
    b = classify_url("https://acme.com/x?utm_source=foo")
    assert a and b
    out = dedupe([a, b])
    assert len(out) == 1


def test_registered_domain_of() -> None:
    assert registered_domain_of("https://blog.acme.co.uk/x") == "acme.co.uk"
    assert registered_domain_of("https://acme.com") == "acme.com"
