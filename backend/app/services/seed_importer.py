"""Seed CSV importer.

Required columns (per kiro/codex-backend-implementation-plan.md Section 7):

    record_type, account_name, account_domain, industry, company_size,
    person_name, title, email, previous_company, role_type,
    github_url, personal_site_url, tech_keywords, outcome_notes

Allowed `record_type` values: target_account, customer_account, champion,
icp_example.

Behavior:
- accounts upserted by `account_domain`, falling back to normalized name.
- people upserted by `email`, falling back to normalized name +
  previous/current company.
- An ICP profile is created/updated from the union of `tech_keywords`,
  `industry`, and `company_size` across all `icp_example` rows.
"""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import AccountStatus, RoleType
from app.models.icp import ICPProfile
from app.models.person import Person

REQUIRED_COLUMNS = [
    "record_type",
    "account_name",
    "account_domain",
    "industry",
    "company_size",
    "person_name",
    "title",
    "email",
    "previous_company",
    "role_type",
    "github_url",
    "personal_site_url",
    "tech_keywords",
    "outcome_notes",
]

ALLOWED_RECORD_TYPES = {"target_account", "customer_account", "champion", "icp_example"}

_RECORD_TYPE_TO_STATUS = {
    "target_account": AccountStatus.target,
    "customer_account": AccountStatus.customer,
    "champion": AccountStatus.target,  # champion's current company defaults to target
    "icp_example": AccountStatus.customer,  # icp examples are best-customer references
}


@dataclass
class SeedImportResult:
    import_id: str = field(default_factory=lambda: f"imp_{uuid.uuid4().hex[:12]}")
    accounts_created: int = 0
    accounts_updated: int = 0
    people_created: int = 0
    people_updated: int = 0
    icp_profiles_created: int = 0
    icp_profiles_updated: int = 0
    warnings: list[str] = field(default_factory=list)


def _normalize(s: str | None) -> str:
    return (s or "").strip().lower()


def _split_keywords(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tok.strip() for tok in raw.replace(";", ",").split(",") if tok.strip()]


def _upsert_account(
    db: Session,
    *,
    name: str,
    domain: str | None,
    industry: str | None = None,
    company_size: str | None = None,
    status: AccountStatus | None = None,
    metadata_extra: dict | None = None,
    result: SeedImportResult | None = None,
) -> Account | None:
    if not name and not domain:
        return None

    account: Account | None = None
    if domain:
        account = db.scalar(select(Account).where(Account.domain == domain))
    if account is None and name:
        account = db.scalar(select(Account).where(Account.name == name))

    created = False
    if account is None:
        account = Account(name=name, domain=domain or None, status=status or AccountStatus.target)
        db.add(account)
        created = True

    if domain and not account.domain:
        account.domain = domain
    if industry:
        account.industry = industry
    if company_size:
        account.company_size = company_size
    if status is not None:
        account.status = status

    meta = dict(account.metadata_json or {})
    if metadata_extra:
        for k, v in metadata_extra.items():
            if v in (None, "", [], {}):
                continue
            meta[k] = v
    account.metadata_json = meta or None

    if result is not None:
        if created:
            result.accounts_created += 1
        else:
            result.accounts_updated += 1

    db.flush()
    return account


def _upsert_person(
    db: Session,
    *,
    full_name: str,
    title: str | None,
    email: str | None,
    role_type: RoleType,
    current_company: Account | None,
    previous_company: Account | None,
    github_url: str | None,
    personal_site_url: str | None,
    metadata_extra: dict | None,
    result: SeedImportResult,
) -> Person | None:
    if not full_name and not email:
        return None

    person: Person | None = None
    if email:
        person = db.scalar(select(Person).where(Person.email == email))
    if person is None and full_name:
        stmt = select(Person).where(Person.full_name == full_name)
        if previous_company is not None:
            stmt = stmt.where(Person.previous_company_id == previous_company.id)
        elif current_company is not None:
            stmt = stmt.where(Person.current_company_id == current_company.id)
        person = db.scalar(stmt)

    created = False
    if person is None:
        person = Person(full_name=full_name, role_type=role_type)
        db.add(person)
        created = True

    if email and not person.email:
        person.email = email
    if title:
        person.title = title
    if current_company is not None:
        person.current_company_id = current_company.id
    if previous_company is not None:
        person.previous_company_id = previous_company.id
    if github_url:
        person.github_url = github_url
    if personal_site_url:
        person.personal_site_url = personal_site_url
    person.role_type = role_type

    meta = dict(person.metadata_json or {})
    if metadata_extra:
        for k, v in metadata_extra.items():
            if v in (None, "", [], {}):
                continue
            meta[k] = v
    person.metadata_json = meta or None

    if created:
        result.people_created += 1
    else:
        result.people_updated += 1

    db.flush()
    return person


def _merge_unique(existing: list | None, new_values: list) -> list:
    base = list(existing or [])
    seen = {v.lower() for v in base if isinstance(v, str)}
    for v in new_values:
        if isinstance(v, str) and v.lower() not in seen:
            base.append(v)
            seen.add(v.lower())
        elif not isinstance(v, str) and v not in base:
            base.append(v)
    return base


def _upsert_default_icp(
    db: Session,
    *,
    industries: list[str],
    company_sizes: list[str],
    tech_keywords: list[str],
    pain_keywords: list[str],
    competitor_keywords: list[str],
    result: SeedImportResult,
) -> ICPProfile:
    name = "default"
    profile = db.scalar(select(ICPProfile).where(ICPProfile.name == name))
    created = False
    if profile is None:
        profile = ICPProfile(name=name)
        db.add(profile)
        created = True

    profile.industries_json = _merge_unique(profile.industries_json, industries)
    profile.company_sizes_json = _merge_unique(profile.company_sizes_json, company_sizes)
    profile.tech_keywords_json = _merge_unique(profile.tech_keywords_json, tech_keywords)
    profile.pain_keywords_json = _merge_unique(profile.pain_keywords_json, pain_keywords)
    profile.competitor_keywords_json = _merge_unique(
        profile.competitor_keywords_json, competitor_keywords
    )
    profile.regions_json = profile.regions_json or []
    profile.target_roles_json = profile.target_roles_json or []

    if created:
        result.icp_profiles_created += 1
    else:
        result.icp_profiles_updated += 1
    db.flush()
    return profile


def import_seed_csv(db: Session, csv_bytes: bytes) -> SeedImportResult:
    """Parse and import a seed CSV. Idempotent."""
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ValueError("CSV is empty or missing a header row")

    missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    result = SeedImportResult()

    icp_industries: list[str] = []
    icp_company_sizes: list[str] = []
    icp_tech_keywords: list[str] = []
    icp_pain_keywords: list[str] = []
    icp_competitor_keywords: list[str] = []

    for line_no, row in enumerate(reader, start=2):  # account for header
        record_type = _normalize(row.get("record_type"))
        if not record_type:
            continue  # blank line
        if record_type not in ALLOWED_RECORD_TYPES:
            result.warnings.append(
                f"row {line_no}: unknown record_type '{record_type}', skipped"
            )
            continue

        account_name = (row.get("account_name") or "").strip()
        account_domain = (row.get("account_domain") or "").strip().lower() or None
        industry = (row.get("industry") or "").strip() or None
        company_size = (row.get("company_size") or "").strip() or None
        tech_keywords = _split_keywords(row.get("tech_keywords"))
        outcome_notes = (row.get("outcome_notes") or "").strip() or None

        # The ICP profile aggregates data from icp_example + customer_account rows.
        if record_type in {"icp_example", "customer_account"}:
            if industry:
                icp_industries.append(industry)
            if company_size:
                icp_company_sizes.append(company_size)
            icp_tech_keywords.extend(tech_keywords)

        if record_type == "icp_example" and not account_name and not account_domain:
            # ICP-only row with no account info, fine.
            continue

        # Upsert the primary account for this row.
        account: Account | None = None
        if account_name or account_domain:
            account_status = _RECORD_TYPE_TO_STATUS.get(record_type, AccountStatus.target)
            account_metadata: dict = {}
            if tech_keywords:
                account_metadata["tech_keywords"] = tech_keywords
            if outcome_notes:
                account_metadata["outcome_notes"] = outcome_notes
            account_metadata["seed_record_type"] = record_type

            account = _upsert_account(
                db,
                name=account_name or (account_domain or "Unnamed account"),
                domain=account_domain,
                industry=industry,
                company_size=company_size,
                status=account_status,
                metadata_extra=account_metadata,
                result=result,
            )

        # If the row also describes a person (champion row most often):
        person_name = (row.get("person_name") or "").strip()
        person_email = (row.get("email") or "").strip().lower() or None
        if person_name or person_email:
            previous_company_name = (row.get("previous_company") or "").strip()
            previous_company: Account | None = None
            if previous_company_name:
                previous_company = _upsert_account(
                    db,
                    name=previous_company_name,
                    domain=None,
                    status=AccountStatus.customer,
                    result=result,
                )

            role_raw = _normalize(row.get("role_type"))
            try:
                role = RoleType(role_raw) if role_raw else RoleType.unknown
            except ValueError:
                result.warnings.append(
                    f"row {line_no}: unknown role_type '{role_raw}', defaulting to 'unknown'"
                )
                role = RoleType.unknown

            person_metadata: dict = {}
            if outcome_notes:
                person_metadata["outcome_notes"] = outcome_notes
            if record_type == "champion":
                person_metadata["seed_record_type"] = "champion"

            _upsert_person(
                db,
                full_name=person_name or person_email or "Unnamed",
                title=(row.get("title") or "").strip() or None,
                email=person_email,
                role_type=role,
                current_company=account if record_type == "champion" else account,
                previous_company=previous_company,
                github_url=(row.get("github_url") or "").strip() or None,
                personal_site_url=(row.get("personal_site_url") or "").strip() or None,
                metadata_extra=person_metadata,
                result=result,
            )

    # Aggregate ICP profile from collected hints.
    if (
        icp_industries
        or icp_company_sizes
        or icp_tech_keywords
        or icp_pain_keywords
        or icp_competitor_keywords
    ):
        _upsert_default_icp(
            db,
            industries=list(dict.fromkeys(icp_industries)),
            company_sizes=list(dict.fromkeys(icp_company_sizes)),
            tech_keywords=list(dict.fromkeys(icp_tech_keywords)),
            pain_keywords=list(dict.fromkeys(icp_pain_keywords)),
            competitor_keywords=list(dict.fromkeys(icp_competitor_keywords)),
            result=result,
        )

    db.commit()
    return result
