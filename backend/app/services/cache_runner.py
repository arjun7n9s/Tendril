"""Replay a blessed-run snapshot into the live DB as a cached scan.

`mode=cached` returns the same response shapes as `mode=live` but every
external call is replayed from the snapshot. Per refinement #17 events
emit the `_replayed` variants and metadata carries `replayed: true`, so
the trace is honest about what really happened.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.logging_setup import get_logger
from app.models.account import Account
from app.models.brief import Brief
from app.models.enums import (
    FetchMethod,
    FetchStatus,
    OutreachStatus,
    OutreachTone,
    ScanEventType,
    ScanStatus,
    SignalType,
    SourceType,
)
from app.models.evidence import EvidenceDocument
from app.models.outreach import OutreachDraft
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal
from app.models.source import Source
from app.services.blessed_runs import (
    find_snapshot_by_domain,
    load_snapshot_for_account,
)
from app.services.memory_service import JsonlMemoryService, MemoryPacket
from app.services.scan_events import ScanEventLogger

log = get_logger("cache_runner")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = PROJECT_ROOT / "var" / "memory"

# Per-phase pacing so the cached replay feels like a real scan rather
# than instantaneous teleportation. Tunable via env in Phase 7 polish.
_PHASE_PACE_SECONDS = 0.4


class BlessedRunNotFoundError(RuntimeError):
    pass


def _enum_or_default(value, enum_cls, default):
    if value is None:
        return default
    try:
        return enum_cls(value)
    except ValueError:
        return default


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def replay_blessed_run(db: Session, scan: Scan) -> bool:
    """Replay the blessed-run JSON for `scan`'s account into this scan.

    Returns True on success. Raises BlessedRunNotFoundError if no snapshot
    is available for the account (by id or by domain fallback).
    """
    account = db.get(Account, scan.account_id)
    if account is None:
        raise RuntimeError(f"account_not_found:{scan.account_id}")

    snapshot = load_snapshot_for_account(scan.account_id)
    if snapshot is None and account.domain:
        snapshot = find_snapshot_by_domain(account.domain)
    if snapshot is None:
        raise BlessedRunNotFoundError(
            f"no blessed-run snapshot for account_id={scan.account_id} "
            f"domain={account.domain}"
        )

    events = ScanEventLogger(db, scan.id)
    settings = get_settings()
    memory = JsonlMemoryService(MEMORY_DIR, event_logger=events, replayed=True)
    captured_from = snapshot.get("captured_from_scan_id")

    events.info(
        "replaying blessed run",
        captured_from_scan_id=captured_from,
        captured_at=snapshot.get("captured_at"),
        replayed=True,
    )

    scan.started_at = scan.started_at or datetime.now(UTC)
    db.add(scan)
    db.commit()

    # ---- discovering ----
    _commit_phase(db, scan, ScanStatus.discovering, 15)
    events.phase_started(ScanStatus.discovering)

    sources_payload = snapshot.get("sources") or []
    source_id_by_url: dict[str, str] = {}
    for raw in sources_payload:
        src = Source(
            scan_id=scan.id,
            account_id=account.id,
            url=raw["url"],
            source_type=_enum_or_default(
                raw.get("source_type"), SourceType, SourceType.other
            ),
            discovery_query=raw.get("discovery_query"),
            rank=int(raw.get("rank") or 0),
            selected_for_scrape=bool(raw.get("selected_for_scrape")),
        )
        db.add(src)
        db.flush()
        source_id_by_url[raw["url"]] = src.id
    db.flush()

    events.bright_data_call(
        f"SERP replay: {len(sources_payload)} candidate URLs",
        phase=ScanStatus.discovering,
        replayed=True,
        tool="cached_serp",
        candidate_count=len(sources_payload),
        selected_count=sum(1 for s in sources_payload if s.get("selected_for_scrape")),
    )
    db.commit()
    events.phase_completed(
        ScanStatus.discovering,
        discovered=len(sources_payload),
        selected=sum(1 for s in sources_payload if s.get("selected_for_scrape")),
    )
    db.commit()
    asyncio.run(_pace())

    # ---- scraping ----
    _commit_phase(db, scan, ScanStatus.scraping, 35)
    events.phase_started(ScanStatus.scraping)

    evidence_payload = snapshot.get("evidence_documents") or []
    evidence_id_by_url: dict[str, str] = {}
    fetched = 0
    failed = 0
    for raw in evidence_payload:
        fetch_status = _enum_or_default(
            raw.get("fetch_status"), FetchStatus, FetchStatus.success
        )
        ev = EvidenceDocument(
            scan_id=scan.id,
            source_id=source_id_by_url.get(raw["url"]),
            account_id=account.id,
            url=raw["url"],
            title=raw.get("title"),
            content_markdown=raw.get("content_markdown"),
            content_hash=raw.get("content_hash"),
            fetched_at=_parse_dt(raw.get("fetched_at")) or datetime.now(UTC),
            fetch_status=fetch_status,
            fetch_method=_enum_or_default(
                raw.get("fetch_method"), FetchMethod, FetchMethod.cached
            ),
            http_status=raw.get("http_status"),
            metadata_json={
                **(raw.get("metadata_json") or {}),
                "replayed": True,
            },
        )
        db.add(ev)
        db.flush()
        evidence_id_by_url[raw["url"]] = ev.id

        if fetch_status == FetchStatus.success:
            fetched += 1
            events.bright_data_call(
                f"Unlocker replay: fetched {raw['url']}",
                phase=ScanStatus.scraping,
                replayed=True,
                tool="cached_unlocker",
                http_status=raw.get("http_status"),
                content_length=len(raw.get("content_markdown") or ""),
            )
        else:
            failed += 1

    db.commit()
    events.phase_completed(ScanStatus.scraping, fetched=fetched, failed=failed)
    db.commit()
    asyncio.run(_pace())

    # ---- extracting ----
    _commit_phase(db, scan, ScanStatus.extracting, 60)
    events.phase_started(ScanStatus.extracting)

    signal_objs: list[Signal] = []
    for raw in snapshot.get("signals") or []:
        signal = Signal(
            scan_id=scan.id,
            account_id=account.id,
            person_id=None,
            signal_type=_enum_or_default(
                raw.get("signal_type"), SignalType, SignalType.other
            ),
            title=raw.get("title") or "",
            summary=raw.get("summary"),
            fact_text=raw.get("fact_text"),
            inference_text=raw.get("inference_text"),
            recommended_action=raw.get("recommended_action"),
            evidence_url=raw["evidence_url"],
            evidence_document_id=evidence_id_by_url.get(raw["evidence_url"]),
            observed_at=_parse_date(raw.get("observed_at")),
            confidence=float(raw.get("confidence") or 0.0),
            recency_days=raw.get("recency_days"),
            metadata_json={
                **(raw.get("metadata_json") or {}),
                "replayed": True,
            },
        )
        db.add(signal)
        signal_objs.append(signal)
    db.flush()

    events.aiml_call(
        f"extraction replay: {len(signal_objs)} signals",
        phase=ScanStatus.extracting,
        replayed=True,
        tool="cached_extractor",
        signal_count=len(signal_objs),
    )
    db.commit()
    events.phase_completed(ScanStatus.extracting, signals=len(signal_objs))
    db.commit()
    asyncio.run(_pace())

    # ---- graphing ----
    _commit_phase(db, scan, ScanStatus.graphing, 75)
    events.phase_started(ScanStatus.graphing)

    written = 0
    for sig in signal_objs:
        memory.remember(
            MemoryPacket(
                scan_id=scan.id,
                account_id=account.id,
                dataset=f"{settings.cognee_dataset_prefix}_signals",
                title=f"{account.name}: {sig.title}",
                body=sig.summary or sig.fact_text or sig.title,
                fact=sig.fact_text,
                inference=sig.inference_text,
                relationship=f"Account: {account.name}",
                evidence_url=sig.evidence_url,
                observed_at=sig.observed_at.isoformat() if sig.observed_at else None,
                signal_id=sig.id,
                metadata={
                    "signal_type": (
                        sig.signal_type.value
                        if hasattr(sig.signal_type, "value")
                        else str(sig.signal_type)
                    ),
                    "confidence": sig.confidence,
                    "replayed": True,
                },
            )
        )
        written += 1
    db.commit()
    events.phase_completed(ScanStatus.graphing, memory_writes=written)
    db.commit()
    asyncio.run(_pace())

    # ---- scoring ----
    _commit_phase(db, scan, ScanStatus.scoring, 85)
    events.phase_started(ScanStatus.scoring)

    score_payload = snapshot.get("score") or {}
    if score_payload:
        score_row = Score(
            scan_id=scan.id,
            account_id=account.id,
            fit_score=int(score_payload.get("fit_score") or 0),
            timing_score=int(score_payload.get("timing_score") or 0),
            relationship_score=int(score_payload.get("relationship_score") or 0),
            evidence_score=int(score_payload.get("evidence_score") or 0),
            total_score=int(score_payload.get("total_score") or 0),
            sales_ready=bool(score_payload.get("sales_ready")),
            score_reasoning_json={
                **(score_payload.get("score_reasoning_json") or {}),
                "replayed": True,
            },
        )
        db.add(score_row)
        db.flush()
        events.phase_completed(
            ScanStatus.scoring,
            total=score_row.total_score,
            sales_ready=score_row.sales_ready,
        )
    else:
        events.phase_completed(ScanStatus.scoring, total=0, sales_ready=False)
    db.commit()
    asyncio.run(_pace())

    # ---- briefing ----
    _commit_phase(db, scan, ScanStatus.briefing, 95)
    events.phase_started(ScanStatus.briefing)

    brief_payload = snapshot.get("brief") or {}
    if brief_payload:
        brief = Brief(
            scan_id=scan.id,
            account_id=account.id,
            title=brief_payload.get("title") or f"{account.name}: GTM brief",
            executive_summary=brief_payload.get("executive_summary"),
            why_now=brief_payload.get("why_now"),
            key_evidence_json=brief_payload.get("key_evidence_json"),
            risks_json=brief_payload.get("risks_json"),
            recommended_next_steps_json=brief_payload.get("recommended_next_steps_json"),
        )
        db.add(brief)
        events.aiml_call(
            "brief replay",
            phase=ScanStatus.briefing,
            replayed=True,
            tool="cached_briefer",
        )

    for raw in snapshot.get("outreach_drafts") or []:
        draft = OutreachDraft(
            scan_id=scan.id,
            account_id=account.id,
            person_id=None,
            subject=raw.get("subject") or "",
            body=raw.get("body") or "",
            tone=_enum_or_default(raw.get("tone"), OutreachTone, OutreachTone.warm),
            status=OutreachStatus.pending_review,  # always pending in replay
            guardrail_notes_json=raw.get("guardrail_notes_json") or [],
            reviewer_feedback=None,
        )
        db.add(draft)
    db.commit()
    events.phase_completed(ScanStatus.briefing)
    db.commit()

    # ---- done ----
    scan.status = ScanStatus.completed
    scan.progress_percent = 100
    scan.completed_at = datetime.now(UTC)
    db.add(scan)
    events.info("scan completed (cached replay)", replayed=True)
    db.commit()
    return True


def _commit_phase(db: Session, scan: Scan, phase: ScanStatus, percent: int) -> None:
    scan.status = phase
    scan.progress_percent = percent
    db.add(scan)
    db.commit()


async def _pace() -> None:
    """Tiny pause so the live UI gets to render each phase transition."""
    await asyncio.sleep(_PHASE_PACE_SECONDS)
