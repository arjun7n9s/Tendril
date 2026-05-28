"""Capture a completed scan as a blessed-run snapshot.

Usage:
    uv run python -m scripts.snapshot_run --scan-id scan_xxx
    uv run python -m scripts.snapshot_run --account-domain ramp.com  # latest scan for that account
    uv run python -m scripts.snapshot_run --account-id acc_xxx       # latest scan for that account

The snapshot lands at backend/fixtures/blessed_runs/<account_id>.json
and can be replayed via `mode=cached`.
"""

from __future__ import annotations

import argparse
import json
import sys

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models.account import Account
from app.models.enums import ScanStatus
from app.models.scan import Scan
from app.services.blessed_runs import snapshot_scan, write_snapshot


def _resolve_scan(
    db,
    *,
    scan_id: str | None,
    account_id: str | None,
    account_domain: str | None,
) -> Scan | None:
    if scan_id:
        return db.get(Scan, scan_id)
    target_account_id = account_id
    if not target_account_id and account_domain:
        account = db.scalar(
            select(Account).where(Account.domain == account_domain.lower())
        )
        if account is None:
            print(f"no account found with domain={account_domain}")
            return None
        target_account_id = account.id
    if not target_account_id:
        print("must supply --scan-id, --account-id, or --account-domain")
        return None
    return db.scalar(
        select(Scan)
        .where(
            Scan.account_id == target_account_id,
            Scan.status == ScanStatus.completed,
        )
        .order_by(Scan.completed_at.desc())
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a blessed-run snapshot")
    parser.add_argument("--scan-id", default=None)
    parser.add_argument("--account-id", default=None)
    parser.add_argument("--account-domain", default=None)
    parser.add_argument(
        "--print",
        dest="dump",
        action="store_true",
        help="Print the snapshot JSON to stdout instead of writing it.",
    )
    args = parser.parse_args()

    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = _resolve_scan(
            db,
            scan_id=args.scan_id,
            account_id=args.account_id,
            account_domain=args.account_domain,
        )
        if scan is None:
            print("no completed scan found for the supplied selector")
            return 2
        if scan.status != ScanStatus.completed:
            print(
                f"scan {scan.id} is not in 'completed' state (status={scan.status}); "
                "snapshot only captures completed scans"
            )
            return 2

        snapshot = snapshot_scan(db, scan)

    if args.dump:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return 0

    path = write_snapshot(scan.account_id, snapshot)
    print(f"wrote {path}")
    print(
        f"  signals: {len(snapshot.get('signals') or [])}, "
        f"evidence: {len(snapshot.get('evidence_documents') or [])}, "
        f"sources: {len(snapshot.get('sources') or [])}, "
        f"outreach_drafts: {len(snapshot.get('outreach_drafts') or [])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
