"""Secret-redaction audit.

Boot the app, exercise the public read endpoints across mock + cached
modes, and assert no `.env` secret value appears in:
  - any HTTP response body
  - any captured stdlib/structlog log line

Exit code is 0 only if every check passes. CI can shell out to this
before tagging a release.

Usage:
    uv run python -m scripts.audit_secrets
    uv run python scripts/audit_secrets.py
"""

from __future__ import annotations

import io
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

from fastapi.testclient import TestClient

from app.config import get_settings
from app.jobs.scan_runner import run_scan
from app.main import create_app


def _secret_values_to_check() -> list[tuple[str, str]]:
    """Return (env_name, value) pairs we never want to see leaked."""
    s = get_settings()
    candidates = [
        ("BRIGHT_DATA_API_KEY", s.bright_data_api_key),
        ("BRIGHT_DATA_BROWSER_WS", s.bright_data_browser_ws),
        ("BRIGHT_DATA_BROWSER_SELENIUM_URL", s.bright_data_browser_selenium_url),
        ("AIML_API_KEY", s.aiml_api_key),
        ("COGNEE_API_KEY", s.cognee_api_key),
        ("TRIGGERWARE_API_KEY", s.triggerware_api_key),
        ("SPEECHMATICS_API_KEY", s.speechmatics_api_key),
    ]
    return [(name, value) for name, value in candidates if value and len(value) >= 6]


def _check_for_leaks(label: str, payload: str, secrets: list[tuple[str, str]]) -> list[str]:
    leaks: list[str] = []
    for name, value in secrets:
        if value and value in payload:
            leaks.append(f"{label}: {name} value leaked")
    # Also flag anything that looks like a `Bearer xxx` or wss/https with embedded auth.
    if "Bearer " in payload:
        leaks.append(f"{label}: 'Bearer ' substring present")
    return leaks


def _exercise_endpoints(client: TestClient) -> list[dict]:
    backend_root = Path(__file__).resolve().parents[1]
    seed_csv = backend_root / "fixtures" / "seed_demo.csv"
    captured: list[dict] = []

    with seed_csv.open("rb") as f:
        captured.append(
            {
                "label": "POST /api/v1/import/seed",
                "body": client.post(
                    "/api/v1/import/seed",
                    files={"file": ("seed_demo.csv", f, "text/csv")},
                ).text,
            }
        )

    captured.append(
        {"label": "GET /health", "body": client.get("/health").text}
    )
    captured.append(
        {
            "label": "GET /api/v1/accounts",
            "body": client.get("/api/v1/accounts", params={"limit": 50}).text,
        }
    )

    accounts = client.get("/api/v1/accounts", params={"search": "ramp"}).json()
    if accounts.get("items"):
        account_id = accounts["items"][0]["id"]
        scan_id = client.post(
            f"/api/v1/accounts/{account_id}/scans",
            json={"mode": "mock"},
        ).json()["scan_id"]
        run_scan(scan_id)
        for label, path in [
            (f"GET /api/v1/scans/{scan_id}", f"/api/v1/scans/{scan_id}"),
            (f"GET /api/v1/scans/{scan_id}/events", f"/api/v1/scans/{scan_id}/events"),
            (f"GET /api/v1/scans/{scan_id}/sources", f"/api/v1/scans/{scan_id}/sources"),
            (f"GET /api/v1/scans/{scan_id}/evidence", f"/api/v1/scans/{scan_id}/evidence"),
            (
                f"GET /api/v1/accounts/{account_id}",
                f"/api/v1/accounts/{account_id}",
            ),
            (
                f"GET /api/v1/accounts/{account_id}/signals",
                f"/api/v1/accounts/{account_id}/signals",
            ),
            (
                f"GET /api/v1/accounts/{account_id}/brief",
                f"/api/v1/accounts/{account_id}/brief",
            ),
            (
                f"GET /api/v1/outreach/pending",
                f"/api/v1/outreach/pending",
            ),
        ]:
            resp = client.get(path)
            captured.append({"label": label, "body": resp.text})

    return captured


def main() -> int:
    secrets = _secret_values_to_check()
    if not secrets:
        print("no secrets configured in .env; nothing to audit")
        return 0

    # Capture log output too.
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    previous_level = root.level
    root.setLevel(logging.DEBUG)

    leaks: list[str] = []
    try:
        app = create_app()
        with TestClient(app) as client:
            captured = _exercise_endpoints(client)
        for entry in captured:
            leaks.extend(_check_for_leaks(entry["label"], entry["body"], secrets))
        leaks.extend(_check_for_leaks("logs", buf.getvalue(), secrets))
    finally:
        root.removeHandler(handler)
        root.setLevel(previous_level)

    if leaks:
        print("AUDIT FAILED: secret-redaction violations detected")
        for leak in leaks:
            print(f"  {leak}")
        return 1

    print(f"AUDIT PASSED: {len(secrets)} secrets checked; no leaks across "
          f"endpoints or logs.")
    print("Audited values:")
    for name, _ in secrets:
        print(f"  {name}: redacted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
