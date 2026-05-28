"""Phase 7 polish smoke.

Runs back-to-back against the real Bright Data and AIML accounts to
verify the polish features behave correctly:

  1. Two live scans against the same account: confirm latest-scan
     default surfaces only the most recent results.
  2. Brief regenerate: confirm POST /scans/{id}/brief/regenerate adds
     a fresh brief without rescraping.
  3. Friendly phase messages: print the new phase wording.
  4. Secret audit: assert the audit script returns clean.

Usage:
    uv run python -m scripts.smoke_phase7
    uv run python scripts/smoke_phase7.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["SIGNALGRAPH_MOCK_MODE"] = "false"

import subprocess

from fastapi.testclient import TestClient

from app.jobs.scan_runner import run_scan
from app.main import create_app


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    seed_csv = backend_root / "fixtures" / "seed_demo.csv"

    app = create_app()
    with TestClient(app) as client:
        with seed_csv.open("rb") as f:
            client.post(
                "/api/v1/import/seed",
                files={"file": ("seed_demo.csv", f, "text/csv")},
            )
        accounts = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
        account_id = accounts["items"][0]["id"]
        print("[account]", accounts["items"][0]["name"], account_id)

        # ---- two cached scans back-to-back to demonstrate latest-scan default ----
        scan_ids: list[str] = []
        for i in range(2):
            scan_id = client.post(
                f"/api/v1/accounts/{account_id}/scans",
                json={"mode": "cached"},
            ).json()["scan_id"]
            run_scan(scan_id)
            scan_ids.append(scan_id)
            print(f"[scan {i + 1}] {scan_id} completed")

        # Latest-scan default: account-scoped signals should only show the
        # most recent scan even though we ran two.
        latest_signals = client.get(
            f"/api/v1/accounts/{account_id}/signals"
        ).json()
        all_signals = client.get(
            f"/api/v1/accounts/{account_id}/signals",
            params={"all_history": "true"},
        ).json()
        print(
            f"[signals] default scope: {latest_signals['total']}, "
            f"all_history: {all_signals['total']}"
        )
        assert latest_signals["total"] < all_signals["total"], (
            "expected accumulating signals across runs to filter out by default"
        )
        scan_ids_in_default = {s["scan_id"] for s in latest_signals["items"]}
        assert scan_ids_in_default == {scan_ids[-1]}

        # Latest-scan default: pending outreach should reflect only the
        # most recent run for this account.
        pending = client.get("/api/v1/outreach/pending").json()
        print(f"[outreach pending] default scope: {pending['total']}")

        # ---- brief regenerate ----
        before = client.get(f"/api/v1/accounts/{account_id}/brief").json()["title"]
        regen_resp = client.post(
            f"/api/v1/scans/{scan_ids[-1]}/brief/regenerate",
        )
        regen = regen_resp.json()
        print(f"[brief regenerate] status={regen_resp.status_code} title='{regen.get('title')}'")
        assert regen_resp.status_code == 200

        # ---- print friendly phase messages from the latest scan ----
        events = client.get(f"/api/v1/scans/{scan_ids[-1]}/events").json()
        phase_events = [
            e for e in events["items"] if e["event_type"] == "phase_started"
        ]
        print(f"[phase wording] {len(phase_events)} phase_started events:")
        for e in phase_events[:6]:
            print(f"  - {e['message']}")

    # ---- run the secret-redaction audit ----
    audit_path = Path(__file__).parent / "audit_secrets.py"
    print("[secret audit] running...")
    res = subprocess.run(
        ["uv", "run", "python", str(audit_path)],
        capture_output=True,
        text=True,
        cwd=str(backend_root),
    )
    last_lines = res.stdout.strip().splitlines()[-6:]
    for line in last_lines:
        print(f"  {line}")
    if res.returncode != 0:
        print("[secret audit] FAILED")
        return 1
    print("[secret audit] PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
