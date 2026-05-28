"""Phase 4 end-to-end live smoke against real Bright Data and AIML.

Imports the demo CSV, picks Ramp, triggers a `mode=live` scan, drives
the runner synchronously, and prints the scan summary including the
extracted signals and brief. Costs a small handful of Bright Data
fetches and AIML calls.

Usage:
    uv run python -m scripts.smoke_phase4
    uv run python scripts/smoke_phase4.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force live mode for this smoke run regardless of .env.
os.environ["SIGNALGRAPH_MOCK_MODE"] = "false"

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
            json={"mode": "live", "max_sources": 4},
        )
        print("[scan create]", create.status_code, create.json())
        body = create.json()
        if body.get("mode") != "live":
            print("ERROR: live mode was coerced; safety gate likely tripped")
            return 1
        scan_id = body["scan_id"]

        run_scan(scan_id)

        status = client.get(f"/api/v1/scans/{scan_id}").json()
        print(
            "[status]",
            status["status"],
            status["progress_percent"],
            status["counts"],
        )

        events = client.get(f"/api/v1/scans/{scan_id}/events").json()
        print(f"[events] {events['total']} events; first 8:")
        for ev in events["items"][:8]:
            print(f"  #{ev['sequence']:>2} {ev['event_type']:32s} {ev['message']}")

        signals = client.get(
            f"/api/v1/accounts/{account_id}/signals", params={"limit": 5}
        ).json()
        print(f"[signals] {signals['total']} (showing top {min(5, len(signals['items']))})")
        for s in signals["items"]:
            print(
                f"  {s['signal_type']:20s} conf {s['confidence']:.2f}  {s['title'][:60]}"
            )
            print(f"    -> {s['evidence_url']}")

        try:
            brief = client.get(f"/api/v1/accounts/{account_id}/brief").json()
            print("[brief]", brief.get("title"))
            print("  why_now:", (brief.get("why_now") or "")[:120])
        except Exception as exc:  # noqa: BLE001
            print("[brief] not available:", exc)

        pending = client.get("/api/v1/outreach/pending").json()
        print(f"[outreach pending] {pending['total']}")
        if pending["items"]:
            d = pending["items"][0]
            print("  subject:", d["subject"])
            print("  body:", (d["body"] or "")[:200])
            print("  guardrail_notes:", d["guardrail_notes_json"])

        return 0 if status["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
