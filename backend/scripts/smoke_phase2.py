"""Phase 2 end-to-end smoke against the dev DB.

Run with: uv run python scripts/smoke_phase2.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.jobs.scan_runner import run_scan
from app.main import create_app


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    seed_csv = backend_root / "fixtures" / "seed_demo.csv"

    app = create_app()
    with TestClient(app) as client:
        with seed_csv.open("rb") as f:
            r = client.post(
                "/api/v1/import/seed",
                files={"file": ("seed_demo.csv", f, "text/csv")},
            )
        print("[seed]", r.status_code, r.json())

        accounts = client.get(
            "/api/v1/accounts", params={"search": "ramp"}
        ).json()
        account_id = accounts["items"][0]["id"]
        print("[account]", account_id, accounts["items"][0]["name"])

        create = client.post(
            f"/api/v1/accounts/{account_id}/scans",
            json={"mode": "mock"},
        )
        print("[scan create]", create.status_code, create.json())
        scan_id = create.json()["scan_id"]

        run_scan(scan_id)

        status = client.get(f"/api/v1/scans/{scan_id}").json()
        print("[scan status]", status["status"], status["progress_percent"], status["counts"])

        events = client.get(f"/api/v1/scans/{scan_id}/events").json()
        print("[events]", events["total"], "events")
        for ev in events["items"][:8]:
            print(f"  #{ev['sequence']} {ev['event_type']:32s} {ev['message']}")

        signals = client.get(
            f"/api/v1/accounts/{account_id}/signals"
        ).json()
        print("[signals]", signals["total"])
        for s in signals["items"][:3]:
            print(
                "  ",
                s["signal_type"],
                round(s["confidence"], 2),
                s["title"],
                "->",
                s["evidence_url"],
            )

        brief = client.get(f"/api/v1/accounts/{account_id}/brief").json()
        print("[brief]", brief["title"])
        print("  why_now:", brief["why_now"][:80])

        pending = client.get("/api/v1/outreach/pending").json()
        print("[outreach pending]", pending["total"])
        if pending["items"]:
            d = pending["items"][0]
            print("  subject:", d["subject"])
            print("  guardrail_notes:", d["guardrail_notes_json"])


if __name__ == "__main__":
    main()
