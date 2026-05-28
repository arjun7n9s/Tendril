"""Dump a real SERP response to disk so we can inspect it.

Usage:
    uv run python -m scripts.debug_serp "Ramp careers Kafka Snowflake"
    uv run python scripts/debug_serp.py "Ramp careers Kafka Snowflake"
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio

from app.services.brightdata_client import BrightDataRestClient
from app.services.serp_parser import parse_serp_html


async def main(query: str) -> int:
    out_dir = Path(__file__).resolve().parents[1] / "var" / "debug"
    out_dir.mkdir(parents=True, exist_ok=True)
    async with BrightDataRestClient() as client:
        result = await client.serp_search(query)
    print(f"status={result.http_status} bytes={result.content_length} ms={result.duration_ms}")
    out_path = out_dir / "serp_sample.html"
    out_path.write_text(result.body, encoding="utf-8")
    print(f"wrote {out_path}")

    hits = parse_serp_html(result.body)
    print(f"parser found {len(hits)} hits")
    for h in hits[:10]:
        print(f"  {h.url}  ({h.title!r})")
    return 0


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Ramp careers data engineer"
    sys.exit(asyncio.run(main(query)))
