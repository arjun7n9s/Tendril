"""Scan pipeline orchestrator.

Walks states queued -> discovering -> scraping -> extracting -> graphing
-> scoring -> briefing -> completed (or failed). Every transition
commits to the DB before yielding so progress survives process restarts.

Phase 2: only the `mock` mode path is exercised end to end.
Phase 3: `live` mode wires up Bright Data SERP + Web Unlocker (with
Browser API fallback). Live extraction stays mock until Phase 4.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_sessionmaker
from app.logging_setup import get_logger
from app.models.account import Account
from app.models.brief import Brief
from app.models.enums import (
    FetchMethod,
    FetchStatus,
    OutreachStatus,
    OutreachTone,
    ScanEventType,
    ScanMode,
    ScanStatus,
    SignalType,
    SourceType,
)
from app.models.evidence import EvidenceDocument
from app.models.helpers import as_str
from app.models.outreach import OutreachDraft
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal
from app.models.source import Source
from app.services.brightdata_client import BrightDataRestClient
from app.services.briefing import generate_brief, generate_outreach
from app.services.guardrails import check_outreach
from app.services.memory_service import JsonlMemoryService, MemoryPacket
from app.services.mock_fixtures import (
    load_evidence_for,
    load_serp_results,
    load_signal_seeds,
)
from app.services.scan_events import ScanEventLogger
from app.services.scorer import ScoringInput, compute_scores, load_default_icp
from app.services.scraper import scrape_source_live
from app.services.source_discovery import discover_sources_live

log = get_logger("scan_runner")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = PROJECT_ROOT / "var" / "memory"


def _now() -> datetime:
    return datetime.now(UTC)


def _commit_phase(db: Session, scan: Scan, phase: ScanStatus, percent: int) -> None:
    scan.status = phase
    scan.progress_percent = percent
    db.add(scan)
    db.commit()


def _percent_for_phase(phase: ScanStatus) -> int:
    return {
        ScanStatus.queued: 0,
        ScanStatus.discovering: 15,
        ScanStatus.scraping: 35,
        ScanStatus.extracting: 60,
        ScanStatus.graphing: 75,
        ScanStatus.scoring: 85,
        ScanStatus.briefing: 95,
        ScanStatus.completed: 100,
        ScanStatus.failed: 100,
    }[phase]


def run_scan(scan_id: str) -> None:
    """Entry point used by FastAPI BackgroundTasks. Opens its own session."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        scan = db.get(Scan, scan_id)
        if scan is None:
            log.warning("scan_runner.missing_scan", scan_id=scan_id)
            return
        if scan.status in (ScanStatus.completed, ScanStatus.failed):
            log.info(
                "scan_runner.skip_terminal",
                scan_id=scan_id,
                status=as_str(scan.status),
            )
            return
        if scan.status != ScanStatus.queued:
            log.info(
                "scan_runner.skip_in_progress",
                scan_id=scan_id,
                status=as_str(scan.status),
            )
            return
        try:
            _execute(db, scan)
        except Exception as exc:  # noqa: BLE001
            log.error("scan_runner.failed", scan_id=scan_id, error=str(exc))
            scan.status = ScanStatus.failed
            scan.error_message = f"{type(exc).__name__}: {exc}"
            scan.progress_percent = 100
            scan.completed_at = _now()
            db.add(scan)
            db.commit()
            try:
                events = ScanEventLogger(db, scan_id)
                events.error("scan failed", error=str(exc), error_type=type(exc).__name__)
                db.commit()
            except Exception:  # noqa: BLE001
                pass


def _execute(db: Session, scan: Scan) -> None:
    settings = get_settings()
    events = ScanEventLogger(db, scan.id)

    scan.started_at = scan.started_at or _now()
    db.add(scan)
    db.commit()

    if scan.mode == ScanMode.live:
        # Same safety gate as the API: require BOTH SIGNALGRAPH_MOCK_MODE=false
        # AND configured Bright Data REST. This protects against accidental
        # credit burn even if the runner is invoked directly.
        if settings.signalgraph_mock_mode or not settings.bright_data_rest_configured():
            reason = (
                "SIGNALGRAPH_MOCK_MODE is true"
                if settings.signalgraph_mock_mode
                else "Bright Data REST is not configured"
            )
            events.warning(
                f"live mode requested but {reason}; falling back to mock"
            )
            scan.mode = ScanMode.mock
            db.add(scan)
            db.commit()

    account = db.get(Account, scan.account_id)
    if account is None:
        raise RuntimeError(f"account_not_found:{scan.account_id}")

    log.info("scan_runner.start", scan_id=scan.id, account=account.name, mode=as_str(scan.mode))

    # ---------- Phase: discovering ----------
    _commit_phase(db, scan, ScanStatus.discovering, _percent_for_phase(ScanStatus.discovering))
    events.phase_started(ScanStatus.discovering)

    icp = load_default_icp(db)

    if scan.mode == ScanMode.live:
        sources = asyncio.run(_live_discovery(db, scan, account, icp, events))
    else:
        sources = _mock_discovery(db, scan, account, events)

    db.commit()
    events.phase_completed(
        ScanStatus.discovering,
        discovered=len(sources),
        selected=sum(1 for s in sources if s.selected_for_scrape),
    )
    db.commit()

    # ---------- Phase: scraping ----------
    _commit_phase(db, scan, ScanStatus.scraping, _percent_for_phase(ScanStatus.scraping))
    events.phase_started(ScanStatus.scraping)

    selected = [s for s in sources if s.selected_for_scrape]
    evidence_rows: list[EvidenceDocument] = []
    failed_count = 0

    if scan.mode == ScanMode.live:
        evidence_rows, failed_count = asyncio.run(
            _live_scrape(db, scan, account, selected, events)
        )
    else:
        for src in selected:
            ev = _mock_fetch(db, scan, account, src, events)
            if ev is None:
                failed_count += 1
                continue
            evidence_rows.append(ev)

    db.commit()
    if not evidence_rows:
        events.error("all sources failed to fetch")
        raise RuntimeError("no_evidence_fetched")
    events.phase_completed(
        ScanStatus.scraping, fetched=len(evidence_rows), failed=failed_count
    )
    db.commit()

    # ---------- Phase: extracting ----------
    _commit_phase(db, scan, ScanStatus.extracting, _percent_for_phase(ScanStatus.extracting))
    events.phase_started(ScanStatus.extracting)

    if scan.mode == ScanMode.live:
        signals = _placeholder_live_extract(db, scan, account, evidence_rows, events)
    else:
        signals = _mock_extract(db, scan, account, evidence_rows, events)
    db.commit()
    events.phase_completed(ScanStatus.extracting, signals=len(signals))
    db.commit()

    # ---------- Phase: graphing ----------
    _commit_phase(db, scan, ScanStatus.graphing, _percent_for_phase(ScanStatus.graphing))
    events.phase_started(ScanStatus.graphing)

    memory = JsonlMemoryService(MEMORY_DIR, event_logger=events)
    written = 0
    for sig in signals:
        packet = MemoryPacket(
            scan_id=scan.id,
            account_id=account.id,
            dataset=f"{settings.cognee_dataset_prefix}_signals",
            title=f"{account.name}: {sig.title}",
            body=f"{sig.summary or sig.fact_text or sig.title}",
            fact=sig.fact_text,
            inference=sig.inference_text,
            relationship=f"Account: {account.name}",
            evidence_url=sig.evidence_url,
            observed_at=sig.observed_at.isoformat() if sig.observed_at else None,
            signal_id=sig.id,
            metadata={
                "signal_type": as_str(sig.signal_type),
                "confidence": sig.confidence,
            },
        )
        memory.remember(packet)
        written += 1
    db.commit()
    events.phase_completed(ScanStatus.graphing, memory_writes=written)
    db.commit()

    # ---------- Phase: scoring ----------
    _commit_phase(db, scan, ScanStatus.scoring, _percent_for_phase(ScanStatus.scoring))
    events.phase_started(ScanStatus.scoring)

    icp = load_default_icp(db) if icp is None else icp
    has_champion = any(as_str(p.role_type) == "champion" for p in account.people_current)
    scoring = compute_scores(
        ScoringInput(account=account, signals=signals, icp=icp, has_champion=has_champion)
    )
    score_row = Score(
        scan_id=scan.id,
        account_id=account.id,
        fit_score=scoring.fit_score,
        timing_score=scoring.timing_score,
        relationship_score=scoring.relationship_score,
        evidence_score=scoring.evidence_score,
        total_score=scoring.total_score,
        sales_ready=scoring.sales_ready,
        score_reasoning_json=scoring.reasoning,
    )
    db.add(score_row)
    db.commit()
    events.phase_completed(
        ScanStatus.scoring,
        total=scoring.total_score,
        sales_ready=scoring.sales_ready,
    )
    db.commit()

    # ---------- Phase: briefing ----------
    _commit_phase(db, scan, ScanStatus.briefing, _percent_for_phase(ScanStatus.briefing))
    events.phase_started(ScanStatus.briefing)

    brief = generate_brief(account, signals, score_row)
    brief_row = Brief(
        scan_id=scan.id,
        account_id=account.id,
        title=brief.title,
        executive_summary=brief.executive_summary,
        why_now=brief.why_now,
        key_evidence_json=brief.key_evidence,
        risks_json=brief.risks,
        recommended_next_steps_json=brief.recommended_next_steps,
    )
    db.add(brief_row)
    db.flush()

    if scoring.sales_ready and signals:
        top_signal = max(signals, key=lambda s: s.confidence)
        outreach = generate_outreach(account, brief, top_signal)
        gr = check_outreach(
            subject=outreach.subject,
            body=outreach.body,
            competitor_keywords=(icp.competitor_keywords_json if icp else None),
            evidence_urls=[s.evidence_url for s in signals],
        )
        draft = OutreachDraft(
            scan_id=scan.id,
            account_id=account.id,
            person_id=None,
            subject=outreach.subject,
            body=outreach.body,
            tone=OutreachTone.warm,
            status=OutreachStatus.pending_review,
            guardrail_notes_json=gr.notes,
        )
        db.add(draft)
        events.info("outreach draft created", guardrail_notes=gr.notes, ok=gr.ok)
    else:
        events.info(
            "no outreach draft generated",
            sales_ready=scoring.sales_ready,
            signal_count=len(signals),
        )

    db.commit()
    events.phase_completed(ScanStatus.briefing)
    db.commit()

    # ---------- Done ----------
    scan.status = ScanStatus.completed
    scan.progress_percent = 100
    scan.completed_at = _now()
    db.add(scan)
    events.info("scan completed")
    db.commit()


# ---------- Mock helpers ----------


def _mock_discovery(
    db: Session, scan: Scan, account: Account, events: ScanEventLogger
) -> list[Source]:
    serp = load_serp_results(account.name, account.domain)
    sources: list[Source] = []
    for r in serp[:8]:
        try:
            source_type = SourceType(r.source_type)
        except ValueError:
            source_type = SourceType.other
        src = Source(
            scan_id=scan.id,
            account_id=account.id,
            url=r.url,
            source_type=source_type,
            discovery_query=r.query,
            rank=r.rank,
            selected_for_scrape=False,
        )
        db.add(src)
        sources.append(src)
    db.flush()

    # Selection: prefer careers + blog + github + news, top 6.
    priority = {
        SourceType.careers: 1,
        SourceType.blog: 2,
        SourceType.docs: 3,
        SourceType.company_site: 4,
        SourceType.github: 5,
        SourceType.news: 6,
        SourceType.serp_result: 7,
        SourceType.other: 9,
    }
    sources.sort(key=lambda s: (priority.get(s.source_type, 9), s.rank))
    seen_urls: set[str] = set()
    selected = 0
    for src in sources:
        if src.url in seen_urls:
            continue
        seen_urls.add(src.url)
        if selected < 6:
            src.selected_for_scrape = True
            selected += 1
            db.add(src)
    db.flush()

    events.emit(
        ScanEventType.bright_data_call,
        message=f"SERP returned {len(serp)} candidate URLs across {len(set(r.query for r in serp))} queries",
        phase=ScanStatus.discovering,
        metadata={
            "tool": "mock_serp",
            "candidate_count": len(serp),
            "selected_count": selected,
            "zone": "mock",
        },
    )
    return sources


def _mock_fetch(
    db: Session,
    scan: Scan,
    account: Account,
    src: Source,
    events: ScanEventLogger,
) -> EvidenceDocument | None:
    content = load_evidence_for(src.url)
    method = FetchMethod.mock
    if content is None:
        ev = EvidenceDocument(
            scan_id=scan.id,
            source_id=src.id,
            account_id=account.id,
            url=src.url,
            title=None,
            content_markdown=None,
            content_hash=None,
            fetched_at=_now(),
            fetch_status=FetchStatus.failed,
            fetch_method=method,
            http_status=404,
            metadata_json={"error": "no_mock_fixture"},
        )
        db.add(ev)
        events.warning(
            "no mock fixture for source",
            url=src.url,
            source_type=as_str(src.source_type),
        )
        return None

    digest = hashlib.sha256(content.markdown.encode("utf-8")).hexdigest()
    ev = EvidenceDocument(
        scan_id=scan.id,
        source_id=src.id,
        account_id=account.id,
        url=content.url,
        title=content.title,
        content_markdown=content.markdown,
        content_hash=digest,
        fetched_at=_now(),
        fetch_status=FetchStatus.success,
        fetch_method=method,
        http_status=200,
        metadata_json={"length": len(content.markdown)},
    )
    db.add(ev)
    db.flush()
    events.emit(
        ScanEventType.bright_data_call,
        message=f"fetched {content.title}",
        phase=ScanStatus.scraping,
        metadata={
            "tool": "mock_unlocker",
            "host": src.url.split("/")[2] if "://" in src.url else None,
            "http_status": 200,
            "length": len(content.markdown),
            "zone": "mock",
        },
    )
    return ev


def _mock_extract(
    db: Session,
    scan: Scan,
    account: Account,
    evidence_rows: list[EvidenceDocument],
    events: ScanEventLogger,
) -> list[Signal]:
    seeds = load_signal_seeds(account.name, account.domain)
    url_to_evidence = {ev.url: ev for ev in evidence_rows if ev.fetch_status == FetchStatus.success}
    today = date.today()

    signals: list[Signal] = []
    for seed in seeds:
        ev = url_to_evidence.get(seed.evidence_url)
        if ev is None:
            continue
        try:
            stype = SignalType(seed.signal_type)
        except ValueError:
            stype = SignalType.other
        observed = today + timedelta(days=seed.observed_at_offset_days)
        sig = Signal(
            scan_id=scan.id,
            account_id=account.id,
            person_id=None,
            signal_type=stype,
            title=seed.title,
            summary=seed.summary,
            fact_text=seed.fact_text,
            inference_text=seed.inference_text,
            recommended_action=seed.recommended_action,
            evidence_url=seed.evidence_url,
            evidence_document_id=ev.id,
            observed_at=observed,
            confidence=seed.confidence,
            recency_days=abs(seed.observed_at_offset_days),
            metadata_json={"source": "mock_fixture"},
        )
        db.add(sig)
        signals.append(sig)
    db.flush()

    events.emit(
        ScanEventType.aiml_call,
        message=f"extracted {len(signals)} signals across {len(evidence_rows)} documents",
        phase=ScanStatus.extracting,
        metadata={
            "tool": "mock_extractor",
            "signal_count": len(signals),
            "doc_count": len(evidence_rows),
        },
    )
    return signals



# ---------- Live helpers (Phase 3) ----------


async def _live_discovery(
    db: Session,
    scan: Scan,
    account: Account,
    icp,
    events: ScanEventLogger,
) -> list[Source]:
    async with BrightDataRestClient() as client:
        return await discover_sources_live(
            db,
            scan=scan,
            account=account,
            icp=icp,
            client=client,
            events=events,
            max_sources=6,
        )


async def _live_scrape(
    db: Session,
    scan: Scan,
    account: Account,
    selected: list[Source],
    events: ScanEventLogger,
) -> tuple[list[EvidenceDocument], int]:
    evidence_rows: list[EvidenceDocument] = []
    failed_count = 0
    async with BrightDataRestClient() as client:
        for src in selected:
            try:
                ev = await scrape_source_live(
                    db,
                    scan=scan,
                    account=account,
                    src=src,
                    client=client,
                    events=events,
                )
            except Exception as exc:  # noqa: BLE001
                events.warning(
                    "scraper raised",
                    target_host=src.url.split("/")[2] if "://" in src.url else None,
                    error_type=type(exc).__name__,
                )
                failed_count += 1
                continue
            if ev is None or ev.fetch_status != FetchStatus.success:
                failed_count += 1
                continue
            evidence_rows.append(ev)
    return evidence_rows, failed_count


def _placeholder_live_extract(
    db: Session,
    scan: Scan,
    account: Account,
    evidence_rows: list[EvidenceDocument],
    events: ScanEventLogger,
) -> list[Signal]:
    """Phase 3 placeholder: produce one low-confidence signal per fetched
    evidence document so the rest of the pipeline (graph/score/brief)
    remains functional. Real AI/ML extraction is Phase 4.
    """
    today = date.today()
    signals: list[Signal] = []
    for ev in evidence_rows:
        if ev.fetch_status != FetchStatus.success or not ev.content_markdown:
            continue
        title = ev.title or "Public web evidence"
        sig = Signal(
            scan_id=scan.id,
            account_id=account.id,
            person_id=None,
            signal_type=SignalType.other,
            title=f"Live evidence: {title}"[:512],
            summary=(ev.content_markdown[:280] + "...") if ev.content_markdown else None,
            fact_text=None,
            inference_text="Awaiting structured extraction (Phase 4 wires AI/ML).",
            recommended_action="Re-run scan after AI/ML extraction is wired to score this signal.",
            evidence_url=ev.url,
            evidence_document_id=ev.id,
            observed_at=today,
            confidence=0.45,
            recency_days=0,
            metadata_json={"source": "live_placeholder", "fetch_method": as_str(ev.fetch_method)},
        )
        db.add(sig)
        signals.append(sig)
    db.flush()

    events.aiml_call(
        message=(
            f"placeholder extraction over {len(evidence_rows)} documents "
            "(Phase 4 will replace with live AI/ML)"
        ),
        phase=ScanStatus.extracting,
        tool="placeholder_extractor",
        signal_count=len(signals),
        doc_count=len(evidence_rows),
    )
    return signals
