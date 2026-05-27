"""AI/ML API client wrapper.

AI/ML API is OpenAI-compatible, so we use the official `openai` SDK
pointed at the AIML base URL. We expose three logical model slots:

- extraction (cheap, JSON-stable)
- briefing (stronger reasoning)
- draft (cheap, short emails)

Refinement #6 (availability probe): on first live use, run a tiny
completion against each configured model. If a model rejects the probe,
fall back to nearest-available defaults. The probe is in-memory cached
so it only runs once per process per model slot.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, BadRequestError

from app.config import Settings, get_settings
from app.logging_setup import get_logger

log = get_logger("aiml_client")


# Fallback chain per refinement #6: if a configured ID is rejected, try these
# in order. We deliberately stick to small, JSON-stable chat models for
# extraction/draft and stronger reasoning models for briefing.
_FALLBACKS: dict[str, list[str]] = {
    "extraction": [
        "gpt-4o-mini",
        "openai/gpt-4o-mini",
        "gpt-4.1-mini",
        "openai/gpt-4.1-mini",
    ],
    "briefing": [
        "gpt-4o",
        "openai/gpt-4o",
        "gpt-4.1",
        "openai/gpt-4.1",
        "anthropic/claude-3.5-sonnet",
    ],
    "draft": [
        "gpt-4o-mini",
        "openai/gpt-4o-mini",
        "gpt-4.1-mini",
        "openai/gpt-4.1-mini",
    ],
}


class AimlNotConfiguredError(RuntimeError):
    """Raised when an AI/ML call is attempted without an API key."""


class AimlExtractionError(RuntimeError):
    """Raised when extraction returns content that cannot be parsed as JSON."""


@dataclass
class CompletionResult:
    text: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    duration_ms: int


class AimlClient:
    """Thin async wrapper around the OpenAI-compatible AIML endpoint."""

    _probe_lock = threading.Lock()
    _probe_results: dict[str, str] = {}  # slot -> resolved model id

    def __init__(self, *, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.aiml_api_key:
            raise AimlNotConfiguredError("AIML_API_KEY not set")
        self._client = AsyncOpenAI(
            api_key=self.settings.aiml_api_key,
            base_url=self.settings.aiml_api_base_url,
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "AimlClient":
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.aclose()

    # ---- Model resolution ----

    def _configured_model_for(self, slot: str) -> str:
        if slot == "extraction":
            return self.settings.aiml_extraction_model
        if slot == "briefing":
            return self.settings.aiml_briefing_model
        if slot == "draft":
            return self.settings.aiml_draft_model
        raise ValueError(f"unknown model slot: {slot}")

    async def resolve_model(self, slot: str) -> str:
        """Return a usable model ID for the given slot.

        First call probes the configured model; if it fails, try fallbacks.
        Subsequent calls return the cached result.
        """
        cached = self._probe_results.get(slot)
        if cached:
            return cached

        candidates: list[str] = []
        configured = self._configured_model_for(slot)
        if configured:
            candidates.append(configured)
        for fb in _FALLBACKS.get(slot, []):
            if fb not in candidates:
                candidates.append(fb)
        if not candidates:
            raise AimlNotConfiguredError(f"no model configured for slot {slot}")

        for model in candidates:
            ok = await self._probe_model(model)
            if ok:
                with self._probe_lock:
                    self._probe_results[slot] = model
                if model != configured:
                    log.warning(
                        "aiml_client.model_fallback",
                        slot=slot,
                        configured=configured,
                        chosen=model,
                    )
                return model

        raise AimlNotConfiguredError(
            f"no usable model for slot {slot}; tried {candidates}"
        )

    async def _probe_model(self, model: str) -> bool:
        try:
            await self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "ok"}],
                max_tokens=1,
                temperature=0.0,
            )
            return True
        except BadRequestError:
            return False
        except APIStatusError as exc:
            if 400 <= exc.status_code < 500:
                return False
            raise
        except APIConnectionError:
            return False

    # ---- Completions ----

    async def complete_json(
        self,
        *,
        slot: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.1,
    ) -> tuple[dict[str, Any], CompletionResult]:
        """Call the model with response_format=json_object and parse the result."""
        import time

        model = await self.resolve_model(slot)
        start = time.monotonic()
        try:
            resp = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except BadRequestError as exc:
            # Some models reject json_object; retry without the directive.
            log.warning("aiml_client.json_mode_unsupported", model=model, error=str(exc))
            resp = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nReturn JSON only."},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

        duration_ms = int((time.monotonic() - start) * 1000)
        text = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        meta = CompletionResult(
            text=text,
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
            duration_ms=duration_ms,
        )
        try:
            return json.loads(text), meta
        except json.JSONDecodeError as exc:
            # Try to recover JSON from a fenced code block.
            repaired = _strip_code_fence(text)
            try:
                return json.loads(repaired), meta
            except json.JSONDecodeError:
                raise AimlExtractionError(
                    f"model {model} returned non-JSON content"
                ) from exc

    async def complete_text(
        self,
        *,
        slot: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 600,
        temperature: float = 0.4,
    ) -> CompletionResult:
        import time

        model = await self.resolve_model(slot)
        start = time.monotonic()
        resp = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        text = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        return CompletionResult(
            text=text,
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
            duration_ms=duration_ms,
        )


def _strip_code_fence(text: str) -> str:
    """Remove a surrounding ```json ... ``` fence if present."""
    t = text.strip()
    if t.startswith("```"):
        # Drop the first fence line.
        first_nl = t.find("\n")
        if first_nl != -1:
            t = t[first_nl + 1 :]
        if t.endswith("```"):
            t = t[: -3]
    return t.strip()
