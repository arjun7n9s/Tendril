"""Application configuration loaded from environment variables.

Secrets are loaded but never logged. Use `Settings.is_configured(...)` to
expose configuration status without leaking values.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env at the project root (one level above backend/).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Strongly-typed settings backed by `.env` at the project root."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_env: str = Field(default="development")
    database_url: str = Field(default="sqlite:///./signalgraph.db")
    signalgraph_mock_mode: bool = Field(default=True)
    cors_allowed_origins: str = Field(default="http://localhost:3000")
    # Optional regex for CORS, useful for Vercel preview URLs that
    # rotate per branch (e.g. `^https://.*\\.vercel\\.app$`). Empty
    # disables regex matching and only `cors_allowed_origins` applies.
    cors_allow_origin_regex: str = Field(default="")

    # Memory backend selector. "jsonl" is safest for demos; "cognee" uses
    # hosted Cognee behind the existing MemoryService protocol.
    tendril_memory_backend: str = Field(default="jsonl")

    # Scan watchdog
    signalgraph_scan_phase_timeout_seconds: int = Field(default=300)

    # Bright Data REST
    bright_data_api_key: str = Field(default="")
    bright_data_api_endpoint: str = Field(default="https://api.brightdata.com/request")
    bright_data_serp_zone: str = Field(default="")
    bright_data_unlocker_zone: str = Field(default="")

    # Bright Data Browser API
    bright_data_browser_ws: str = Field(default="")
    bright_data_browser_selenium_url: str = Field(default="")

    # Bright Data MCP (optional / future)
    bright_data_mcp_url: str = Field(default="")

    # AI/ML API
    aiml_api_key: str = Field(default="")
    aiml_api_base_url: str = Field(default="https://api.aimlapi.com/v1")
    aiml_extraction_model: str = Field(default="")
    aiml_briefing_model: str = Field(default="")
    aiml_draft_model: str = Field(default="")

    # Featherless AI (cheap open-model gateway, OpenAI-compatible).
    # Used for source ranking and chunk relevance filtering in the media
    # pipeline, where a low-cost model gates the expensive AIMLAPI extraction.
    featherless_api_key: str = Field(default="")
    featherless_api_base_url: str = Field(default="https://api.featherless.ai/v1")
    featherless_ranking_model: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.3"
    )

    # Media / multimodal signal engine
    media_scan_max_sources: int = Field(default=3)
    media_scan_phase_timeout_seconds: int = Field(default=600)
    media_transcript_retention_raw: bool = Field(default=False)
    speechmatics_poll_seconds: int = Field(default=10)
    speechmatics_max_poll_attempts: int = Field(default=60)
    # Per-scan budget ceiling (USD, estimated). 0 disables the hard stop.
    # The feature's whole premise is cost discipline, so a scan that would
    # exceed this is stopped before the expensive transcribe/extract stages.
    # Default is generous enough for a normal multi-source scan but still
    # catches a runaway (e.g. many long sources with no cache hits).
    media_scan_budget_usd: float = Field(default=25.0)
    # Rough provider price estimates used only for budgeting/telemetry.
    cost_asr_per_minute_usd: float = Field(default=0.02)
    cost_llm_per_call_usd: float = Field(default=0.01)

    # Autonomous watchtower (Phase 7). OFF by default so scheduled scans
    # never burn provider credits without an explicit opt-in.
    watchtower_enabled: bool = Field(default=False)
    watchtower_tick_seconds: int = Field(default=60)
    watchtower_default_interval_seconds: int = Field(default=86400)
    watchtower_batch_size: int = Field(default=2)
    # Mode used for scheduled scans: "mock" (safe default) or "live".
    watchtower_default_mode: str = Field(default="mock")

    # Cognee (hosted Cognee Cloud REST API)
    cognee_api_key: str = Field(default="")
    cognee_api_url: str = Field(default="")
    cognee_tenant_id: str = Field(default="")
    cognee_user_id: str = Field(default="")
    cognee_dataset_prefix: str = Field(default="signalgraph")
    cognee_operation_timeout_seconds: int = Field(default=30)
    # remember() builds the graph server-side; run it in the background so a
    # scan's graphing phase stays fast. The read loop recalls *prior* scans'
    # accumulated memory, so the current run's writes don't need to be
    # immediately queryable.
    cognee_run_in_background: bool = Field(default=True)
    # Search strategy for recall. GRAPH_COMPLETION returns an LLM-synthesized
    # answer grounded in the account's graph — ideal for brief "why now".
    cognee_search_type: str = Field(default="GRAPH_COMPLETION")

    # Optional integrations
    triggerware_api_key: str = Field(default="")
    speechmatics_api_key: str = Field(default="")

    # ----- Helpers (no secret values exposed) -----

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    def bright_data_rest_configured(self) -> bool:
        return bool(
            self.bright_data_api_key
            and self.bright_data_api_endpoint
            and self.bright_data_serp_zone
            and self.bright_data_unlocker_zone
        )

    def bright_data_browser_configured(self) -> bool:
        return bool(self.bright_data_browser_ws)

    def aiml_configured(self) -> bool:
        return bool(
            self.aiml_api_key
            and self.aiml_api_base_url
            and self.aiml_extraction_model
            and self.aiml_briefing_model
            and self.aiml_draft_model
        )

    def featherless_configured(self) -> bool:
        return bool(self.featherless_api_key and self.featherless_api_base_url)

    def cognee_configured(self) -> bool:
        return bool(self.cognee_api_key and self.cognee_api_url and self.cognee_tenant_id)

    def triggerware_configured(self) -> bool:
        return bool(self.triggerware_api_key)

    def speechmatics_configured(self) -> bool:
        return bool(self.speechmatics_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
