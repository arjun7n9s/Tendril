"""SERP HTML parser tests."""

from __future__ import annotations

from app.services.serp_parser import parse_serp_html


def test_parses_traditional_div_g_results() -> None:
    html = """
    <html><body>
      <div class="g">
        <a href="https://acme.com/careers/engineer">
          <h3>Senior Data Engineer at Acme</h3>
        </a>
      </div>
      <div class="g">
        <a href="https://acme.com/engineering/scaling">
          <h3>Scaling our data platform</h3>
        </a>
      </div>
    </body></html>
    """
    hits = parse_serp_html(html)
    urls = [h.url for h in hits]
    assert "https://acme.com/careers/engineer" in urls
    assert "https://acme.com/engineering/scaling" in urls
    titles = [h.title for h in hits]
    assert any("Senior Data Engineer" in (t or "") for t in titles)


def test_parses_google_redirect_form() -> None:
    html = """
    <html><body>
      <a href="/url?q=https%3A%2F%2Facme.com%2Fblog&amp;sa=U">
        <h3>Acme Engineering Blog</h3>
      </a>
    </body></html>
    """
    hits = parse_serp_html(html)
    assert any(h.url == "https://acme.com/blog" for h in hits)


def test_falls_back_to_beautifulsoup_when_no_match() -> None:
    # Deliberately weird structure that the selectolax selectors won't match well.
    html = "<weird><a href='https://acme.com/x'>x</a></weird>"
    hits = parse_serp_html(html)
    assert any(h.url == "https://acme.com/x" for h in hits)


def test_handles_empty_html() -> None:
    assert parse_serp_html("") == []
