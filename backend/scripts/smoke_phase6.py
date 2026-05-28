"""Phase 6 cached-mode smoke.

Imports the demo CSV, triggers a `mode=cached` scan, runs it, and prints
the summary so we can verify the replay produces the same response shape
as a live scan with no external credits spent.

Usage:
    uv run python -m scripts.smoke_phase6
    uv run python scripts/smoke_phase6.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force mock_mode=true: cached replay should work without any external creds.
os.environ["SIGNALGRAPH_MOCK_MODE"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from app.jobs.scan_runner import run_scan  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    seed_csv = backend_root / "fixtures" / "seed_demo.csv"

    app = create_app()
    with TestClient(app) as client:
        with seed_csv.open("rb") as f:
            r = client.post(
                "/api/v1/import/seed",
                files={"file": ("seed_demo.csv", f, "text/csv")},
            )
        print("[seed]", r.status_code, r.json()["accounts_created"], "created")

        accounts = client.get(
            "/api/v1/accounts", params={"search": "ramp"}
        ).json()
        if not accounts["items"]:
            print("ERROR: no Ramp account in seed")
            return 1
        account_id = accounts["items"][0]["id"]
        print("[account]", accounts["items"][0]["name"], account_id)

        create = client.post(
            f"/api/v1/accounts/{account_id}/scans",
            json={"mode": "cached"},
        )
        print("[scan create]", create.status_code, create.json())
        body = create.json()
        scan_id = body["scan_id"]

        run_scan(scan_id)

        status = client.get(f"/api/v1/scans/{scan_id}").json()
        print("[status]", status["status"], status["progress_percent"], status["counts"])

        events = client.get(f"/api/v1/scans/{scan_id}/events").json()
        print(f"[events] {events['total']} events; replayed event types:")
        replayed_count = 0
        for ev in events["items"]:
            etype = ev["event_type"]
            if "replayed" in etype:
                replayed_count += 1
                if replayed_count <= 6:
                    print(f"  #{ev['sequence']:>2} {etype:32s} {ev['message']}")
        print(f"  total replayed events: {replayed_count}")

        signals = client.get(
            f"/api/v1/accounts/{account_id}/signals", params={"limit": 5}
        ).json()
        print(f"[signals] {signals['total']} (showing top {min(5, len(signals['items']))})")
        for s in signals["items"][:3]:
            print(
                f"  {s['signal_type']:20s} conf {s['confidence']:.2f}  {s['title'][:60]}"
            )

        try:
            brief = client.get(f"/api/v1/accounts/{account_id}/brief").json()
            print("[brief]", brief.get("title"))
        except Exception as exc:  # noqa: BLE001
            print("[brief] not available:", exc)

        pending = client.get("/api/v1/outreach/pending").json()
        print(f"[outreach pending] {pending['total']}")

        return 0 if status["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
