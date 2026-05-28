"""Pytest-runnable secret-redaction audit.

Synthetic secrets are stamped into the env, then the public read
endpoints are exercised end-to-end. The synthetic values must never
appear in any response body or log line.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.jobs.scan_runner import run_scan
from app.main import create_app

# Distinctive synthetic secrets so a leak is unambiguous.
SYNTHETIC = {
    "BRIGHT_DATA_API_KEY": "AUDIT-SECRET-BD-KEY-zzzz1111",
    "BRIGHT_DATA_BROWSER_WS": "wss://AUDIT-SECRET-USER:AUDIT-SECRET-PW@brd.example.com:9222",
    "AIML_API_KEY": "AUDIT-SECRET-AIML-KEY-aaaa9999",
    "COGNEE_API_KEY": "AUDIT-SECRET-COGNEE-KEY-bbbb8888",
    "TRIGGERWARE_API_KEY": "AUDIT-SECRET-TW-KEY-cccc7777",
    "SPEECHMATICS_API_KEY": "AUDIT-SECRET-SPEECH-KEY-dddd6666",
}


@pytest.fixture
def _stamped_secrets(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    for name, value in SYNTHETIC.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "true")
    get_settings.cache_clear()
    return SYNTHETIC


def _check_no_leak(label: str, payload: str, secrets: dict[str, str]) -> list[str]:
    leaks: list[str] = []
    for name, value in secrets.items():
        if value in payload:
            leaks.append(f"{label}: {name} value leaked")
    if "Bearer " in payload:
        leaks.append(f"{label}: 'Bearer ' substring present")
    return leaks


def test_secret_audit_no_leaks_across_endpoints_or_logs(
    seed_csv_path: Path, _stamped_secrets: dict[str, str]
) -> None:
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    previous = root.level
    root.setLevel(logging.DEBUG)

    leaks: list[str] = []
    try:
        app = create_app()
        with TestClient(app) as client:
            with seed_csv_path.open("rb") as f:
                resp = client.post(
                    "/api/v1/import/seed",
                    files={"file": ("seed_demo.csv", f, "text/csv")},
                )
            leaks.extend(_check_no_leak("seed", resp.text, _stamped_secrets))

            health = client.get("/health")
            leaks.extend(_check_no_leak("health", health.text, _stamped_secrets))

            list_resp = client.get("/api/v1/accounts", params={"limit": 50})
            leaks.extend(_check_no_leak("accounts", list_resp.text, _stamped_secrets))

            account_id = list_resp.json()["items"][0]["id"]
            scan_id = client.post(
                f"/api/v1/accounts/{account_id}/scans",
                json={"mode": "mock"},
            ).json()["scan_id"]
            run_scan(scan_id)

            for label, path in [
                (f"scans/{scan_id}", f"/api/v1/scans/{scan_id}"),
                (f"scans/{scan_id}/events", f"/api/v1/scans/{scan_id}/events"),
                (f"scans/{scan_id}/sources", f"/api/v1/scans/{scan_id}/sources"),
                (f"scans/{scan_id}/evidence", f"/api/v1/scans/{scan_id}/evidence"),
                (
                    f"accounts/{account_id}",
                    f"/api/v1/accounts/{account_id}",
                ),
                (
                    f"accounts/{account_id}/signals",
                    f"/api/v1/accounts/{account_id}/signals",
                ),
                (
                    f"accounts/{account_id}/brief",
                    f"/api/v1/accounts/{account_id}/brief",
                ),
                ("outreach/pending", "/api/v1/outreach/pending"),
            ]:
                r = client.get(path)
                leaks.extend(_check_no_leak(label, r.text, _stamped_secrets))

        leaks.extend(_check_no_leak("logs", buf.getvalue(), _stamped_secrets))
    finally:
        root.removeHandler(handler)
        root.setLevel(previous)

    assert not leaks, "secret leaks detected:\n" + "\n".join(leaks)
