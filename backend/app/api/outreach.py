"""Outreach endpoints."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.models.enums import OutreachStatus, OutreachTone, ScanMode
from app.models.outreach import OutreachDraft
from app.models.scan import Scan
from app.models.signal import Signal
from app.schemas.outreach import (
    OutreachList,
    OutreachPatch,
    OutreachRead,
    OutreachRegenerate,
    OutreachReject,
)
from app.services.aiml_client import AimlClient, AimlNotConfiguredError
from app.services.briefing import generate_outreach, generate_outreach_live
from app.services.guardrails import check_outreach

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


def _latest_scan_per_account_subq():
    return (
        select(
            Scan.account_id.label("account_id"),
            func.max(Scan.created_at).label("max_created"),
        )
        .group_by(Scan.account_id)
        .subquery()
    )


@router.get("/pending", response_model=OutreachList)
def list_pending(
    all_history: bool = Query(
        default=False,
        description=(
            "When false (default), returns only drafts whose scan is the "
            "most recent for its account. Set true to include all "
            "drafts awaiting review across history."
        ),
    ),
    db: Session = Depends(get_db),
) -> OutreachList:
    # Drafts awaiting human action: not-yet-touched (`pending_review`)
    # plus drafts the reviewer already edited (`edited`). Both still
    # need approve/reject before anything leaves Tendril.
    awaiting_review = [
        OutreachStatus.pending_review,
        OutreachStatus.edited,
    ]
    stmt = select(OutreachDraft).where(
        OutreachDraft.status.in_(awaiting_review)
    )
    count_stmt = select(func.count()).select_from(OutreachDraft).where(
        OutreachDraft.status.in_(awaiting_review)
    )
    if not all_history:
        latest = _latest_scan_per_account_subq()
        join_condition = and_(
            Scan.id == OutreachDraft.scan_id,
            Scan.account_id == latest.c.account_id,
            Scan.created_at == latest.c.max_created,
        )
        stmt = stmt.join(Scan, Scan.id == OutreachDraft.scan_id).join(
            latest, join_condition
        )
        count_stmt = count_stmt.join(Scan, Scan.id == OutreachDraft.scan_id).join(
            latest, join_condition
        )
    rows = db.scalars(stmt.order_by(OutreachDraft.created_at.desc())).all()
    total = db.scalar(count_stmt) or 0
    return OutreachList(
        items=[OutreachRead.model_validate(r) for r in rows], total=total
    )


@router.get("/{draft_id}", response_model=OutreachRead)
def get_draft(draft_id: str, db: Session = Depends(get_db)) -> OutreachRead:
    row = db.get(OutreachDraft, draft_id)
    if row is None:
        raise HTTPException(status_code=404, detail="draft_not_found")
    return OutreachRead.model_validate(row)


@router.post("/{draft_id}/approve", response_model=OutreachRead)
def approve_draft(draft_id: str, db: Session = Depends(get_db)) -> OutreachRead:
    row = db.get(OutreachDraft, draft_id)
    if row is None:
        raise HTTPException(status_code=404, detail="draft_not_found")
    row.status = OutreachStatus.approved
    db.add(row)
    db.commit()
    return OutreachRead.model_validate(row)


@router.post("/{draft_id}/reject", response_model=OutreachRead)
def reject_draft(
    draft_id: str, body: OutreachReject, db: Session = Depends(get_db)
) -> OutreachRead:
    row = db.get(OutreachDraft, draft_id)
    if row is None:
        raise HTTPException(status_code=404, detail="draft_not_found")
    row.status = OutreachStatus.rejected
    if body.feedback:
        row.reviewer_feedback = body.feedback
    db.add(row)
    db.commit()
    return OutreachRead.model_validate(row)


@router.patch("/{draft_id}", response_model=OutreachRead)
def edit_draft(
    draft_id: str, body: OutreachPatch, db: Session = Depends(get_db)
) -> OutreachRead:
    row = db.get(OutreachDraft, draft_id)
    if row is None:
        raise HTTPException(status_code=404, detail="draft_not_found")
    if body.subject is not None:
        row.subject = body.subject
    if body.body is not None:
        row.body = body.body
    if body.tone is not None:
        row.tone = body.tone
    if row.status == OutreachStatus.pending_review:
        row.status = OutreachStatus.edited
    db.add(row)
    db.commit()
    return OutreachRead.model_validate(row)


@router.post("/{draft_id}/regenerate", response_model=OutreachRead)
def regenerate_draft(
    draft_id: str, body: OutreachRegenerate, db: Session = Depends(get_db)
) -> OutreachRead:
    """Rewrite a draft's subject + body in a different tone.

    This is what makes the tone toggle change the email. It reuses the
    draft's scan signals (no rescrape), regenerates via AIML in live mode
    (deterministic tone presets otherwise / on failure), re-runs guardrails,
    and keeps the draft in a reviewable state. Terminal drafts are immutable.
    """
    row = db.get(OutreachDraft, draft_id)
    if row is None:
        raise HTTPException(status_code=404, detail="draft_not_found")
    if row.status in (OutreachStatus.approved, OutreachStatus.rejected):
        raise HTTPException(status_code=409, detail="draft_is_terminal")

    try:
        tone = OutreachTone(body.tone)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid_tone") from None

    account = db.get(Account, row.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account_not_found")

    signals = list(
        db.scalars(
            select(Signal)
            .where(Signal.scan_id == row.scan_id)
            .order_by(Signal.confidence.desc())
        )
    )
    top_signal = signals[0] if signals else None

    scan = db.get(Scan, row.scan_id)
    use_live = scan is not None and scan.mode == ScanMode.live

    payload = None
    if use_live:
        try:
            payload, _telemetry = asyncio.run(
                _regenerate_via_aiml(account, signals, top_signal, tone.value)
            )
        except AimlNotConfiguredError:
            payload = None
    if payload is None:
        payload = generate_outreach(account, None, top_signal, tone.value)

    gr = check_outreach(
        subject=payload.subject,
        body=payload.body,
        evidence_urls=[s.evidence_url for s in signals],
    )

    row.subject = payload.subject
    row.body = payload.body
    row.tone = tone
    row.guardrail_notes_json = gr.notes
    if row.status == OutreachStatus.pending_review:
        row.status = OutreachStatus.edited
    db.add(row)
    db.commit()
    return OutreachRead.model_validate(row)


async def _regenerate_via_aiml(account, signals, top_signal, tone: str):
    async with AimlClient() as aiml:
        return await generate_outreach_live(
            aiml=aiml,
            account=account,
            signals=signals,
            top_signal=top_signal,
            tone=tone,
        )
