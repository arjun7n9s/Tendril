"""Parse Bright Data SERP HTML into candidate URLs.

Google's SERP markup changes frequently. We try selectolax first (fast)
and use multiple selectors before falling back to a raw href scan via
BeautifulSoup. Always return absolute http(s) URLs.
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser

from app.services.url_utils import (
    extract_target_from_google_redirect,
    is_absolute_http,
)


@dataclass
class ParsedSerpHit:
    url: str
    title: str | None


def _resolve(href: str) -> str | None:
    if not href:
        return None
    target = extract_target_from_google_redirect(href)
    if target and is_absolute_http(target):
        return target
    if is_absolute_http(href):
        return href
    return None


def _from_selectolax(html: str) -> list[ParsedSerpHit]:
    tree = HTMLParser(html)
    out: list[ParsedSerpHit] = []
    seen: set[str] = set()

    # Common Google SERP result containers - we rely on the anchors inside
    # them, not the container classes themselves, to be tolerant of changes.
    selectors = [
        "div.g a[href]",
        "div.tF2Cxc a[href]",
        "div.yuRUbf a[href]",
        "h3 a[href]",
        "a[href]",  # last-resort fallback handled below
    ]
    for selector in selectors:
        for node in tree.css(selector):
            href = node.attributes.get("href") or ""
            target = _resolve(href)
            if not target or target in seen:
                continue
            title_node = node.css_first("h3")
            title = (title_node.text(strip=True) if title_node else node.text(strip=True)) or None
            out.append(ParsedSerpHit(url=target, title=title))
            seen.add(target)
        if out:
            break  # first selector that produced hits wins
    return out


def _from_beautifulsoup(html: str) -> list[ParsedSerpHit]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[ParsedSerpHit] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        target = _resolve(a["href"])
        if not target or target in seen:
            continue
        title = a.get_text(strip=True) or None
        out.append(ParsedSerpHit(url=target, title=title))
        seen.add(target)
    return out


def parse_serp_html(html: str) -> list[ParsedSerpHit]:
    if not html:
        return []
    primary = _from_selectolax(html)
    if primary:
        return primary
    return _from_beautifulsoup(html)
