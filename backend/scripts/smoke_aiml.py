"""AI/ML API smoke test.

Probes each of the three configured model slots with a tiny completion
to verify the API key works and the configured model IDs are reachable.
The probe results are cached on `AimlClient`, so a successful run
warms the cache for the rest of the process.

Usage:
    uv run python -m scripts.smoke_aiml
"""

from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.services.aiml_client import AimlClient, AimlNotConfiguredError


async def main() -> int:
    settings = get_settings()
    if not settings.aiml_configured():
        print("AIML is not configured. Check .env for:")
        print("  AIML_API_KEY, AIML_EXTRACTION_MODEL, AIML_BRIEFING_MODEL, AIML_DRAFT_MODEL")
        return 2

    print("AIML base URL:", settings.aiml_api_base_url)
    print("Configured models:")
    print("  extraction:", settings.aiml_extraction_model)
    print("  briefing:  ", settings.aiml_briefing_model)
    print("  draft:     ", settings.aiml_draft_model)

    try:
        async with AimlClient() as client:
            for slot in ("extraction", "briefing", "draft"):
                try:
                    chosen = await client.resolve_model(slot)
                    print(f"  resolved {slot}: {chosen}")
                except AimlNotConfiguredError as exc:
                    print(f"  resolved {slot}: FAILED - {exc}")
                    return 1

            print("\nRunning a tiny JSON completion against the extraction model...")
            payload, meta = await client.complete_json(
                slot="extraction",
                system_prompt='You return JSON with one field: {"ok": true}.',
                user_prompt="Return JSON.",
                max_tokens=20,
            )
            print(f"  model: {meta.model}")
            print(f"  duration_ms: {meta.duration_ms}")
            print(f"  payload: {payload}")
            if not isinstance(payload, dict):
                print("WARNING: model did not return a JSON object")
                return 1
            print("OK: AIML smoke succeeded")
            return 0
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
