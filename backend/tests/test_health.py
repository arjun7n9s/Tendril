"""Phase 0 smoke test: app boots and /health returns expected shape."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_expected_shape() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()

        # Keys promised by the plan
        for key in (
            "status",
            "database",
            "bright_data_rest",
            "bright_data_browser",
            "aiml_api",
            "cognee",
            "mock_mode",
        ):
            assert key in body, f"missing key {key} in /health response"

        assert body["status"] == "ok"
        assert body["database"] == "ok"
        assert body["bright_data_rest"] in {"configured", "not_configured"}
        assert body["aiml_api"] in {"configured", "not_configured"}
        assert isinstance(body["mock_mode"], bool)


def test_health_response_does_not_leak_secrets() -> None:
    """No part of the response should contain anything that looks like a token."""
    with TestClient(app) as client:
        body = client.get("/health").json()

    serialized = repr(body)
    # These specific strings should never be in the response.
    forbidden_substrings = [
        "Bearer ",
        "brd-customer-",
        "superproxy.io",
    ]
    for needle in forbidden_substrings:
        assert needle not in serialized, f"secret-like substring {needle!r} leaked in response"
