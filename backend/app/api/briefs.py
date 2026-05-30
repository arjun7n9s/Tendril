"""Brief endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.models.brief import Brief
from app.models.enums import ScanMode, ScanStatus
from app.models.helpers import as_str
from app.models.scan import Scan
from app.models.score import Score
from app.models.signal import Signal
from app.schemas.brief import BriefRead
from app.services.aiml_client import AimlClient, AimlNotConfiguredError
from app.services.briefing import (
    generate_brief,
    generate_brief_live,
)
from app.services.scan_events import ScanEventLogger

router = APIRouter(tags=["briefs"])


@router.get("/api/v1/accounts/{account_id}/brief", response_model=BriefRead)
def get_latest_brief(account_id: str, db: Session = Depends(get_db)) -> BriefRead:
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")
    row = db.scalar(
        select(Brief)
        .where(Brief.account_id == account_id)
        .order_by(Brief.created_at.desc())
    )
    if row is None:
        raise HTTPException(status_code=404, detail="brief_not_found")
    return BriefRead.model_validate(row)


@router.post(
    "/api/v1/scans/{scan_id}/brief/regenerate",
    response_model=BriefRead,
)
def regenerate_brief(scan_id: str, db: Session = Depends(get_db)) -> BriefRead:
    """Regenerate the brief for an existing scan from already-stored data.

    Does NOT rescrape: this endpoint reuses the persisted signals, score,
    and (in live mode) makes a single AIML call to draft a new brief.
    Falls back to the deterministic helper if AIML is not configured or
    the live model fails. The fresh brief is appended (the prior brief
    rows remain) so we keep an audit trail; the latest-scan-default
    endpoints surface the most recent one.
    """
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="scan_not_found")
    if scan.status != ScanStatus.completed:
        raise HTTPException(
            status_code=409,
            detail=f"scan_not_completed (status={as_str(scan.status)})",
        )

    account = db.get(Account, scan.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")

    score = db.scalar(select(Score).where(Score.scan_id == scan_id))
    if score is None:
        raise HTTPException(status_code=409, detail="score_not_found_for_scan")

    signals = list(
        db.scalars(
            select(Signal)
            .where(Signal.scan_id == scan_id)
            .order_by(Signal.confidence.desc())
        )
    )

    events = ScanEventLogger(db, scan_id)

    # Recall accumulated account memory so the regenerated brief is grounded in
    # history, consistent with the live scan's read loop.
    from pathlib import Path

    from app.services.memory_retrieval import recall_account_memory
    from app.services.memory_service import build_memory_service

    memory_dir = Path(__file__).resolve().parents[2] / "var" / "memory"
    memory = build_memory_service(memory_dir)
    graph_recall = recall_account_memory(
        memory,
        account_id=account.id,
        account_name=account.name,
        current_signal_titles=[s.title for s in signals],
        current_scan_id=scan_id,
    )
    graph_context = graph_recall.context_text

    if scan.mode == ScanMode.live:
        try:
            brief, telemetry = asyncio.run(
                _regenerate_via_aiml(account, signals, score, graph_context)
            )
            events.memory_read(
                f"recalled {graph_recall.total} memory packets for regenerate",
                phase=ScanStatus.briefing,
                recalled=graph_recall.total,
                prior=graph_recall.prior_count,
            )
            events.aiml_call(
                f"brief regenerated via {telemetry.get('model') or 'fallback'}",
                phase=ScanStatus.briefing,
                tool="aiml_briefer",
                model=telemetry.get("model"),
                duration_ms=telemetry.get("duration_ms"),
                fallback=telemetry.get("fallback", False),
                regenerate=True,
            )
        except AimlNotConfiguredError:
            events.warning(
                "AIML not configured during regenerate; using deterministic brief"
            )
            brief = generate_brief(account, signals, score, graph_context)
    else:
        brief = generate_brief(account, signals, score, graph_context)
        events.info("brief regenerated (deterministic)", regenerate=True)

    new_row = Brief(
        scan_id=scan.id,
        account_id=account.id,
        title=brief.title,
        executive_summary=brief.executive_summary,
        why_now=brief.why_now,
        key_evidence_json=brief.key_evidence,
        risks_json=brief.risks,
        recommended_next_steps_json=brief.recommended_next_steps,
    )
    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return BriefRead.model_validate(new_row)


async def _regenerate_via_aiml(account, signals, score, graph_context: str = ""):
    async with AimlClient() as aiml:
        return await generate_brief_live(
            aiml=aiml,
            account=account,
            signals=signals,
            score=score,
            graph_context=graph_context,
        )
