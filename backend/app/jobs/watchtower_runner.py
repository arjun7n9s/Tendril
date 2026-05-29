"""Background watchtower loop.

A single daemon thread wakes every `WATCHTOWER_TICK_SECONDS`, runs one
`watchtower.tick()`, and dispatches due media scans onto worker threads. It is
only started when `WATCHTOWER_ENABLED` is true, so the default build does no
background work at all.

Each due scan runs the existing durable `run_media_scan`, which is idempotent
and resumable, so a crash mid-scan is recovered on the next tick.
"""

from __future__ import annotations

import threading

from app.config import get_settings
from app.db import get_sessionmaker
from app.jobs.media_scan_runner import run_media_scan
from app.logging_setup import get_logger
from app.services import watchtower

log = get_logger("watchtower_runner")


class WatchtowerLoop:
    """Owns the watchtower daemon thread and a worker pool for scans."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._workers: list[threading.Thread] = []

    def _enqueue(self, job_id: str) -> None:
        worker = threading.Thread(
            target=run_media_scan,
            args=(job_id,),
            name=f"media-scan-{job_id[:12]}",
            daemon=True,
        )
        worker.start()
        # Drop references to finished workers so the list doesn't grow forever.
        self._workers = [w for w in self._workers if w.is_alive()]
        self._workers.append(worker)

    def _run(self) -> None:
        settings = get_settings()
        SessionLocal = get_sessionmaker()
        log.info("watchtower_runner.started", tick_seconds=settings.watchtower_tick_seconds)
        while not self._stop.is_set():
            try:
                with SessionLocal() as db:
                    watchtower.tick(db, enqueue=self._enqueue, settings=settings)
            except Exception as exc:
                log.warning("watchtower_runner.tick_failed", error=str(exc))
            self._stop.wait(max(5, settings.watchtower_tick_seconds))
        log.info("watchtower_runner.stopped")

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="watchtower-loop", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)


_loop: WatchtowerLoop | None = None


def start_watchtower() -> None:
    """Start the watchtower loop if enabled. Safe to call once at startup."""
    global _loop
    settings = get_settings()
    if not settings.watchtower_enabled:
        log.info("watchtower_runner.disabled")
        return
    if _loop is not None:
        return
    _loop = WatchtowerLoop()
    _loop.start()


def stop_watchtower() -> None:
    global _loop
    if _loop is not None:
        _loop.stop()
        _loop = None
