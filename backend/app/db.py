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

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)


def ensure_schema(engine=None) -> None:
    """Idempotently add any model columns missing from existing tables.

    `create_all` never alters existing tables, so when we add a column to a
    model the pre-existing dev SQLite DB would lack it. This walks every mapped
    table and issues `ALTER TABLE ... ADD COLUMN` for columns the DB is missing.

    Additive only — it never drops or rewrites columns, so it is safe to run on
    every startup. Non-SQLite backends are skipped (use Alembic there).
    """
    from sqlalchemy import inspect, text

    engine = engine or get_engine()
    if not engine.url.get_backend_name().startswith("sqlite"):
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.tables.values():
            if table.name not in existing_tables:
                continue
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_cols:
                    continue
                ddl_type = column.type.compile(dialect=engine.dialect)
                default_clause = ""
                if column.default is not None and getattr(
                    column.default, "is_scalar", False
                ):
                    value = column.default.arg
                    if isinstance(value, bool):
                        default_clause = f" DEFAULT {1 if value else 0}"
                    elif isinstance(value, (int, float)):
                        default_clause = f" DEFAULT {value}"
                    elif isinstance(value, str):
                        default_clause = f" DEFAULT '{value}'"
                conn.execute(
                    text(
                        f'ALTER TABLE "{table.name}" '
                        f'ADD COLUMN "{column.name}" {ddl_type}{default_clause}'
                    )
                )
