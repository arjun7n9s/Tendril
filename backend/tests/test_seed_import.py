"""Phase 1: seed CSV import tests."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models.account import Account
from app.models.icp import ICPProfile
from app.models.person import Person
from app.services.seed_importer import import_seed_csv


def _read_seed(path: Path) -> bytes:
    return path.read_bytes()


def test_seed_import_creates_accounts_people_and_icp(seed_csv_path: Path) -> None:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        result = import_seed_csv(db, _read_seed(seed_csv_path))

    assert result.accounts_created >= 20  # 23 targets + 2 customers + champion prev co
    assert result.people_created >= 1
    assert result.icp_profiles_created == 1
    assert result.warnings == []

    with SessionLocal() as db:
        ramp = db.scalar(select(Account).where(Account.domain == "ramp.com"))
        assert ramp is not None
        assert ramp.industry == "fintech"

        priya = db.scalar(select(Person).where(Person.email == "priya.nair@example.com"))
        assert priya is not None
        assert priya.previous_company is not None
        assert priya.previous_company.name.lower() == "alpaca"
        assert priya.current_company is not None
        assert priya.current_company.domain == "ramp.com"

        icp = db.scalar(select(ICPProfile).where(ICPProfile.name == "default"))
        assert icp is not None
        assert "fintech" in (icp.industries_json or [])
        assert any("kafka" in (kw or "").lower() for kw in (icp.tech_keywords_json or []))


def test_seed_import_is_idempotent(seed_csv_path: Path) -> None:
    SessionLocal = get_sessionmaker()
    with SessionLocal() as db:
        result1 = import_seed_csv(db, _read_seed(seed_csv_path))

    with SessionLocal() as db:
        result2 = import_seed_csv(db, _read_seed(seed_csv_path))

    # Second run must not create duplicate accounts or people.
    assert result2.accounts_created == 0
    assert result2.people_created == 0
    assert result2.icp_profiles_created == 0
    assert result2.accounts_updated >= result1.accounts_created
    assert result2.people_updated >= result1.people_created


def test_seed_import_rejects_missing_columns() -> None:
    SessionLocal = get_sessionmaker()
    bad_csv = b"record_type,account_name\ntarget_account,Foo\n"
    with SessionLocal() as db:
        try:
            import_seed_csv(db, bad_csv)
            raise AssertionError("expected ValueError")
        except ValueError as exc:
            assert "missing required columns" in str(exc)


def test_seed_import_warns_on_unknown_record_type() -> None:
    SessionLocal = get_sessionmaker()
    headers = (
        "record_type,account_name,account_domain,industry,company_size,person_name,"
        "title,email,previous_company,role_type,github_url,personal_site_url,"
        "tech_keywords,outcome_notes\n"
    )
    bad_row = "alien_thing,Foo,foo.com,,,,,,,,,,,\n"
    with SessionLocal() as db:
        result = import_seed_csv(db, (headers + bad_row).encode("utf-8"))
    assert result.accounts_created == 0
    assert any("unknown record_type" in w for w in result.warnings)
