"""Schema for the seed CSV import response."""

from __future__ import annotations

from pydantic import BaseModel


class SeedImportResponse(BaseModel):
    import_id: str
    accounts_created: int
    accounts_updated: int
    people_created: int
    people_updated: int
    icp_profiles_created: int
    icp_profiles_updated: int
    warnings: list[str]
