"""Featherless AI client (cheap, open-model gateway).

Featherless is OpenAI-compatible, so we reuse the `openai` SDK pointed at the
Featherless base URL. In the media pipeline this model does the *cheap* work:

- ranking candidate sources before spending transcription money, and
- chunk-level relevance filtering before the expensive AIMLAPI extraction.

This deliberate split keeps cost down: a small open model gates the work and
the stronger AIMLAPI model only runs on the high-value chunks.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, BadRequestError

from app.config import Settings, get_settings
from app.logging_setup import get_logger

log = get_logger("featherless_client")


class FeatherlessNotConfiguredError(RuntimeError):
    """Raised when a Featherless call is attempted without an API key."""


class FeatherlessResponseError(RuntimeError):
    """Raised when Featherless returns content that cannot be parsed."""


@dataclass
class FeatherlessResult:
    text: str
    model: str
    duration_ms: int


class FeatherlessClient:
    """Thin async wrapper around the OpenAI-compatible Featherless endpoint."""

    def __init__(self, *, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.featherless_api_key:
            raise FeatherlessNotConfiguredError("FEATHERLESS_API_KEY not set")
        self._client = AsyncOpenAI(
            api_key=self.settings.featherless_api_key,
            base_url=self.settings.featherless_api_base_url,
        )
        self._model = self.settings.featherless_ranking_model

    async def aclose(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> FeatherlessClient:
        return self

    async def __aexit__(self, *_exc) -> None:
        await self.aclose()

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1200,
        temperature: float = 0.0,
    ) -> tuple[dict[str, Any], FeatherlessResult]:
        start = time.monotonic()
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except BadRequestError:
            # Some open models reject json_object; retry plain.
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nReturn JSON only."},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except (APIConnectionError, APIStatusError) as exc:
            raise FeatherlessResponseError(f"featherless_unavailable: {exc}") from exc

        duration_ms = int((time.monotonic() - start) * 1000)
        text = (resp.choices[0].message.content or "").strip()
        result = FeatherlessResult(text=text, model=self._model, duration_ms=duration_ms)
        try:
            return json.loads(text), result
        except json.JSONDecodeError:
            repaired = _strip_code_fence(text)
            try:
                return json.loads(repaired), result
            except json.JSONDecodeError as exc:
                raise FeatherlessResponseError(
                    "featherless returned non-JSON content"
                ) from exc


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        first_nl = t.find("\n")
        if first_nl != -1:
            t = t[first_nl + 1 :]
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()
