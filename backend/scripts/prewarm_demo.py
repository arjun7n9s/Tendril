"""Pre-warm an account's Cognee graph before a demo recording.

Runs two scans (with a pause between) so the account's Cognee dataset has
accumulated, queryable memory by the time you record. Prints the memory_read
event from the second scan so you can confirm recall is hitting Cognee Cloud
(backend=cognee_cloud) and not the JSONL fallback.

Usage:
    uv run python -m scripts.prewarm_demo --account Ramp
    uv run python -m scripts.prewarm_demo --account-id acc_xxx --mode mock
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db import get_sessionmaker
from app.jobs.scan_runner import run_scan
from app.models.account import Account
from app.models.enums import ScanEventType, ScanMode, ScanStatus
from app.models.scan import Scan
from app.models.scan_event import ScanEvent


def _resolve_account(db, *, account_id: str | None, name: str | None) -> Account:
    if account_id:
        acc = db.get(Account, account_id)
        if acc is None:
            raise SystemExit(f"no account with id={account_id}")
        return acc
    acc = db.scalar(select(Account).where(Account.name.ilike(f"%{name}%")))
    if acc is None:
        raise SystemExit(f"no account matching name={name}")
    return acc


def _run_one(account_id: str, mode: str) -> str:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = Scan(
            account_id=account_id,
            scan_type="account_watchtower",
            status=ScanStatus.queued,
            mode=ScanMode(mode),
            progress_percent=0,
        )
        db.add(scan)
        db.commit()
        scan_id = scan.id
    run_scan(scan_id)
    return scan_id


def _print_memory_read(scan_id: str) -> None:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        rows = db.scalars(
            select(ScanEvent)
            .where(
                ScanEvent.scan_id == scan_id,
                ScanEvent.event_type == ScanEventType.memory_read,
            )
            .order_by(ScanEvent.sequence)
        ).all()
        if not rows:
            print(f"  [scan {scan_id[-6:]}] no memory_read event found")
            return
        for ev in rows:
            meta = ev.metadata_json or {}
            print(f"  [scan {scan_id[-6:]}] {ev.message}")
            print(
                f"     recalled={meta.get('recalled')} prior={meta.get('prior')} "
                f"backend={meta.get('backend')} themes={meta.get('recurring_themes')}"
            )

        # Also show the write backend so we can confirm cloud writes happened.
        writes = db.scalars(
            select(ScanEvent)
            .where(
                ScanEvent.scan_id == scan_id,
                ScanEvent.event_type == ScanEventType.memory_write,
            )
            .order_by(ScanEvent.sequence)
            .limit(1)
        ).all()
        for ev in writes:
            meta = ev.metadata_json or {}
            print(f"     first memory_write backend={meta.get('backend')} degraded={meta.get('degraded')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", default=None, help="account name (fuzzy)")
    parser.add_argument("--account-id", default=None, help="exact account id")
    parser.add_argument("--mode", default="mock", choices=["mock", "live"])
    parser.add_argument("--wait", type=int, default=45, help="seconds between scans")
    args = parser.parse_args()

    if not args.account and not args.account_id:
        args.account = "Ramp"

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        acc = _resolve_account(db, account_id=args.account_id, name=args.account)
        account_id, account_name = acc.id, acc.name

    print(f"Pre-warming '{account_name}' ({account_id}) in {args.mode} mode")

    print("\n[1/2] First scan (seeds the Cognee graph)...")
    s1 = _run_one(account_id, args.mode)
    _print_memory_read(s1)

    print(f"\nWaiting {args.wait}s for Cognee to build the graph...")
    time.sleep(args.wait)

    print("\n[2/2] Second scan (should recall prior memory from Cognee)...")
    s2 = _run_one(account_id, args.mode)
    _print_memory_read(s2)

    print(
        "\nDone. If the second scan shows recalled>0 with backend=cognee_cloud, "
        "the demo account is recording-ready."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
