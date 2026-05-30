"""Pre-run live web scans across the whole portfolio via the running server's
HTTP API (single writer -> no SQLite lock contention).

Sequential, polite, and resilient: triggers one live scan per account, polls to
completion, and prints a PASS/FAIL summary so we know which accounts scrape
cleanly on this Bright Data account (some big domains are KYC-gated and will
fail — that's expected and we curate around them).

Usage:
    uv run python -m scripts.prerun_portfolio --base http://localhost:8000
    uv run python -m scripts.prerun_portfolio --only Ramp,Plaid,Brex
"""

from __future__ import annotations

import argparse
import sys
import time

import httpx

HEADERS = {"ngrok-skip-browser-warning": "true"}


def _accounts(base: str) -> list[dict]:
    r = httpx.get(f"{base}/api/v1/accounts", params={"limit": 200}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()["items"]


def _trigger(base: str, account_id: str, mode: str, max_sources: int) -> str | None:
    r = httpx.post(
        f"{base}/api/v1/accounts/{account_id}/scans",
        json={"mode": mode, "scan_type": "account_watchtower", "max_sources": max_sources},
        headers=HEADERS,
        timeout=30,
    )
    if r.status_code != 201:
        print(f"   trigger failed: {r.status_code} {r.text[:120]}")
        return None
    return r.json()["scan_id"]


def _poll(base: str, scan_id: str, *, timeout_s: int = 300) -> dict:
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        r = httpx.get(f"{base}/api/v1/scans/{scan_id}", headers=HEADERS, timeout=30)
        r.raise_for_status()
        last = r.json()
        if last["status"] in ("completed", "failed"):
            return last
        time.sleep(6)
    return last


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000")
    parser.add_argument("--mode", default="live", choices=["live", "mock"])
    parser.add_argument("--max-sources", type=int, default=6)
    parser.add_argument("--only", default=None, help="comma-separated account names")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    accounts = _accounts(args.base)
    if args.only:
        wanted = {n.strip().lower() for n in args.only.split(",")}
        accounts = [a for a in accounts if a["name"].lower() in wanted]

    print(f"Pre-running {len(accounts)} accounts in {args.mode} mode via {args.base}\n")
    passed: list[str] = []
    failed: list[tuple[str, str]] = []

    for i, acc in enumerate(accounts, 1):
        name = acc["name"]
        print(f"[{i}/{len(accounts)}] {name} ...", flush=True)
        scan_id = _trigger(args.base, acc["id"], args.mode, args.max_sources)
        if scan_id is None:
            failed.append((name, "trigger_failed"))
            continue
        result = _poll(args.base, scan_id, timeout_s=args.timeout)
        status = result.get("status", "unknown")
        counts = result.get("counts", {})
        if status == "completed":
            passed.append(name)
            print(
                f"   PASS signals={counts.get('signals')} "
                f"bd={counts.get('bright_data_calls')} "
                f"aiml={counts.get('aiml_calls')} mem={counts.get('memory_writes')}"
            )
        else:
            err = result.get("error_message") or "unknown"
            failed.append((name, err))
            print(f"   FAIL status={status} err={err}")

    print("\n================ SUMMARY ================")
    print(f"PASSED ({len(passed)}): {', '.join(passed)}")
    print(f"FAILED ({len(failed)}):")
    for name, err in failed:
        print(f"   - {name}: {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
