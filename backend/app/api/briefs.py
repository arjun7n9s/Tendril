"""Brief endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.account import Account
from app.models.brief import Brief
from app.schemas.brief import BriefRead

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
