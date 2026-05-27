"""Parse Bright Data SERP responses into candidate URLs.

The Bright Data SERP zone may return either:
- A parsed JSON object containing an `organic` results array (default), or
- Rendered Google HTML (when the zone is configured for raw HTML output).

We try JSON first because it's faster and structurally stable, then fall
back to HTML parsers (selectolax with multiple selectors, then
BeautifulSoup as a last-resort raw href scan).
"""

from __future__ import annotations

import json
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


def _from_json(payload: str) -> list[ParsedSerpHit] | None:
    """Try to parse Bright Data's parsed-SERP JSON shape.

    Returns None when the body isn't JSON or doesn't have a recognizable
    organic-results array.
    """
    stripped = payload.lstrip()
    if not stripped.startswith("{"):
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    out: list[ParsedSerpHit] = []
    seen: set[str] = set()

    def _add(url: str | None, title: str | None) -> None:
        if not url:
            return
        target = _resolve(url)
        if not target or target in seen:
            return
        seen.add(target)
        out.append(ParsedSerpHit(url=target, title=(title or None)))

    # Common Bright Data shape: top-level `organic` list of {link/url, title}.
    organic = data.get("organic")
    if isinstance(organic, list):
        for item in organic:
            if not isinstance(item, dict):
                continue
            _add(item.get("link") or item.get("url"), item.get("title"))

    # Some payloads expose news / videos / knowledge variants.
    for key in ("news", "videos", "shopping", "top_stories"):
        items = data.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    _add(item.get("link") or item.get("url"), item.get("title"))

    if out:
        return out
    return None


def _from_selectolax(html: str) -> list[ParsedSerpHit]:
    tree = HTMLParser(html)
    out: list[ParsedSerpHit] = []
    seen: set[str] = set()

    selectors = [
        "div.g a[href]",
        "div.tF2Cxc a[href]",
        "div.yuRUbf a[href]",
        "h3 a[href]",
        "a[href]",
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
            break
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


def parse_serp_html(body: str) -> list[ParsedSerpHit]:
    """Parse a SERP response body in whichever shape Bright Data returns."""
    if not body:
        return []
    json_hits = _from_json(body)
    if json_hits is not None:
        return json_hits
    primary = _from_selectolax(body)
    if primary:
        return primary
    return _from_beautifulsoup(body)
