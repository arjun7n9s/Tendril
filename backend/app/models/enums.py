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
    memory_read = "memory_read"
    warning = "warning"
    error = "error"
    info = "info"


# ----- Multimodal / media signal engine -----


class MediaSourceType(str, Enum):
    youtube = "youtube"
    podcast = "podcast"
    earnings_call = "earnings_call"
    webinar = "webinar"
    conference = "conference"
    interview = "interview"
    other = "other"


class MediaScanMode(str, Enum):
    mock = "mock"
    live = "live"


class MediaScanStage(str, Enum):
    """Durable pipeline stages, in execution order."""

    queued = "queued"
    discover_sources = "discover_sources"
    rank_sources = "rank_sources"
    resolve_media = "resolve_media"
    hash_media = "hash_media"
    transcribe = "transcribe"
    scrub_transcript = "scrub_transcript"
    extract_signals = "extract_signals"
    write_memory = "write_memory"
    score_account = "score_account"
    notify = "notify"
    completed = "completed"
    failed = "failed"


class MediaSourceStatus(str, Enum):
    discovered = "discovered"
    ranked = "ranked"
    selected = "selected"
    skipped = "skipped"
    resolved = "resolved"
    transcribed = "transcribed"
    extracted = "extracted"
    failed = "failed"


class MediaDownloadStatus(str, Enum):
    pending = "pending"
    resolved = "resolved"
    downloaded = "downloaded"
    cached = "cached"
    failed = "failed"


class TranscriptionStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    reused = "reused"
    failed = "failed"


class TranscriptProvider(str, Enum):
    speechmatics = "speechmatics"
    captions = "captions"
    existing_transcript = "existing_transcript"
    mock = "mock"


class PrivacyStatus(str, Enum):
    clean = "clean"
    scrubbed = "scrubbed"
    sensitive_blocked = "sensitive_blocked"


class MediaScanEventType(str, Enum):
    stage_started = "stage_started"
    stage_completed = "stage_completed"
    stage_skipped = "stage_skipped"
    bright_data_call = "bright_data_call"
    featherless_call = "featherless_call"
    aiml_call = "aiml_call"
    speechmatics_call = "speechmatics_call"
    cache_hit = "cache_hit"
    memory_write = "memory_write"
    pii_redaction = "pii_redaction"
    notification = "notification"
    warning = "warning"
    error = "error"
    info = "info"


class NotificationType(str, Enum):
    media_scan_completed = "media_scan_completed"
    media_scan_failed = "media_scan_failed"
    conversation_signal = "conversation_signal"
    score_change = "score_change"
    new_source = "new_source"
    info = "info"
