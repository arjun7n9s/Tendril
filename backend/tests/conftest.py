"""Shared pytest fixtures.

We isolate each test by pointing SQLAlchemy at an in-memory SQLite
database before the app modules cache their engine.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    tmpdir = Path(tempfile.mkdtemp(prefix="signalgraph-test-"))
    db_path = tmpdir / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("SIGNALGRAPH_MOCK_MODE", "true")

    # Reset cached singletons so the new DATABASE_URL is picked up.
    from app.config import get_settings
    from app.db import get_engine, get_sessionmaker

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()

    # Recreate schema cleanly.
    from app.db import init_db

    init_db()

    yield

    # Clear caches again so subsequent tests get a fresh slate.
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def seed_csv_path() -> Path:
    here = Path(__file__).resolve().parents[1]
    return here / "fixtures" / "seed_demo.csv"


@pytest.fixture
def client():
    """A TestClient against a fresh app instance."""
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
