"""Database engine and session setup.

SQLAlchemy 2.x with SQLite for MVP. The engine and SessionLocal are
constructed lazily so settings (and tests) can override `DATABASE_URL`.
"""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    connect_args: dict = {}
    if settings.database_url.startswith("sqlite"):
        # Required so the engine works inside FastAPI background tasks
        # which may run in different threads than the request handler.
        connect_args["check_same_thread"] = False
    return create_engine(settings.database_url, connect_args=connect_args, future=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Used at app startup for MVP; Alembic later."""
    # Import models so they register on Base.metadata.
    from app import models  # noqa: F401  (registers models on Base)

    Base.metadata.create_all(bind=get_engine())
