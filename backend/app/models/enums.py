"""Shared enum types used across SQLAlchemy models and Pydantic schemas."""

from __future__ import annotations

from enum import Enum


class AccountStatus(str, Enum):
    target = "target"
    customer = "customer"
    former_customer = "former_customer"
    competitor = "competitor"
    ignored = "ignored"


class RoleType(str, Enum):
    champion = "champion"
    buyer = "buyer"
    technical_user = "technical_user"
    unknown = "unknown"


class ScanType(str, Enum):
    account_watchtower = "account_watchtower"
    champion_mobility = "champion_mobility"
    lookalike_discovery = "lookalike_discovery"


class ScanStatus(str, Enum):
    queued = "queued"
    discovering = "discovering"
    scraping = "scraping"
    extracting = "extracting"
    graphing = "graphing"
    scoring = "scoring"
    briefing = "briefing"
    completed = "completed"
    failed = "failed"


class ScanMode(str, Enum):
    mock = "mock"
    live = "live"
    cached = "cached"


class SourceType(str, Enum):
    company_site = "company_site"
    careers = "careers"
    blog = "blog"
    news = "news"
    github = "github"
    docs = "docs"
    serp_result = "serp_result"
    review = "review"
    public_profile = "public_profile"
    other = "other"


class FetchStatus(str, Enum):
    success = "success"
    failed = "failed"
    skipped = "skipped"


class FetchMethod(str, Enum):
    brightdata_mcp = "brightdata_mcp"
    serp_api = "serp_api"
    unlocker = "unlocker"
    browser_api = "browser_api"
    web_scraper_api = "web_scraper_api"
    mock = "mock"
    cached = "cached"


class SignalType(str, Enum):
    hiring = "hiring"
    tech_stack = "tech_stack"
    migration = "migration"
    funding = "funding"
    product_launch = "product_launch"
    leadership_change = "leadership_change"
    competitor_mention = "competitor_mention"
    champion_move = "champion_move"
    market_event = "market_event"
    other = "other"


class OutreachTone(str, Enum):
    warm = "warm"
    technical = "technical"
    executive = "executive"
    concise = "concise"


class OutreachStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    edited = "edited"


class ScanEventType(str, Enum):
    phase_started = "phase_started"
    phase_completed = "phase_completed"
    bright_data_call = "bright_data_call"
    bright_data_call_replayed = "bright_data_call_replayed"
    aiml_call = "aiml_call"
    aiml_call_replayed = "aiml_call_replayed"
    memory_write = "memory_write"
    memory_write_replayed = "memory_write_replayed"
    warning = "warning"
    error = "error"
    info = "info"
