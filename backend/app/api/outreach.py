"""Outreach endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.enums import OutreachStatus
from app.models.outreach import OutreachDraft
from app.schemas.outreach import (
    OutreachList,
    OutreachPatch,
    OutreachRead,
    OutreachReject,
)

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])


@router.get("/pending", response_model=OutreachList)
def list_pending(db: Session = Depends(get_db)) -> OutreachList:
    rows = db.scalars(
        select(OutreachDraft)
        .where(OutreachDraft.status == OutreachStatus.pending_review)
        .order_by(OutreachDraft.created_at.desc())
    ).all()
    total = db.scalar(
        select(func.count()).select_from(OutreachDraft).where(
            OutreachDraft.status == OutreachStatus.pending_review
        )
    ) or 0
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
