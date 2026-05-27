"""Seed CSV import endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.import_seed import SeedImportResponse
from app.services.seed_importer import import_seed_csv

router = APIRouter(prefix="/api/v1/import", tags=["imports"])


@router.post("/seed", response_model=SeedImportResponse, status_code=status.HTTP_200_OK)
async def post_seed(
    file: UploadFile = File(..., description="Seed CSV"),
    db: Session = Depends(get_db),
) -> SeedImportResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = import_seed_csv(db, raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SeedImportResponse(
        import_id=result.import_id,
        accounts_created=result.accounts_created,
        accounts_updated=result.accounts_updated,
        people_created=result.people_created,
        people_updated=result.people_updated,
        icp_profiles_created=result.icp_profiles_created,
        icp_profiles_updated=result.icp_profiles_updated,
        warnings=result.warnings,
    )
