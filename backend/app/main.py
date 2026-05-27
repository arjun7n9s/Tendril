"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import accounts, briefs, health, imports, outreach, scans, signals
from app.config import get_settings
from app.db import init_db
from app.logging_setup import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log = get_logger("signalgraph")
    settings = get_settings()
    init_db()
    log.info(
        "app.startup",
        env=settings.app_env,
        mock_mode=settings.signalgraph_mock_mode,
        bright_data_rest=settings.bright_data_rest_configured(),
        aiml_api=settings.aiml_configured(),
        cognee=settings.cognee_configured(),
        version=__version__,
    )
    yield
    log.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SignalGraph Backend",
        description="Autonomous GTM Change Intelligence",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router, prefix="/api/v1")
    # Phase 0 also exposes /health at root for convenience.
    app.include_router(health.router)
    # Phase 1
    app.include_router(imports.router)
    app.include_router(accounts.router)
    # Phase 2
    app.include_router(scans.router)
    app.include_router(signals.router)
    app.include_router(briefs.router)
    app.include_router(outreach.router)

    return app


app = create_app()
