"""Health endpoint.

Returns a coarse-grained status of the database and each external
integration without exposing any credential values.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db

router = APIRouter(tags=["health"])


def _check_db(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


def _flag(configured: bool) -> str:
    return "configured" if configured else "not_configured"


@router.get("/health")
def health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return {
        "status": "ok",
        "database": _check_db(db),
        "bright_data_rest": _flag(settings.bright_data_rest_configured()),
        "bright_data_browser": _flag(settings.bright_data_browser_configured()),
        "bright_data_mcp": _flag(bool(settings.bright_data_mcp_url)),
        "aiml_api": _flag(settings.aiml_configured()),
        "cognee": _flag(settings.cognee_configured()),
        "triggerware": _flag(settings.triggerware_configured()),
        "speechmatics": _flag(settings.speechmatics_configured()),
        "mock_mode": settings.signalgraph_mock_mode,
        "app_env": settings.app_env,
    }
