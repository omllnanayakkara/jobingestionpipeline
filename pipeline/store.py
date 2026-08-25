from typing import Sequence
from models.job_listing import JobListing as ScrapedJobListing
from db.converters import build_company_model, build_job_listing_model
from db.session import SessionLocal
from db.models import JobListing, Company
from sqlalchemy.dialects.postgresql import insert as pg_insert

JOB_LISTING_REFRESHABLE_COLUMNS = [
    "title", "summary", "description",
    "job_type", "category", "location", "remote",
    "min_salary", "max_salary", "avg_salary", "salary_currency", "salary_frequency",
    "posted_at", "updated_at", "expires_at",
    "experience_level", "min_experience_years",
    "required_skills", "preferred_skills", "education_requirements",
    "company_id",
]


def store(data: Sequence[ScrapedJobListing]):
    companies_by_name = {}
    for item in data:
        if not item.company_name:
            continue
        if item.company_name not in companies_by_name:
            companies_by_name[item.company_name] = build_company_model(item)
    company_data = list(companies_by_name.values())

    with SessionLocal.begin() as session:
        name_to_id = {}
        if company_data:
            company_stmt = pg_insert(Company)
            company_upsert_stmt = company_stmt.on_conflict_do_update(
                index_elements=["name"],
                set_=dict(
                    company_url=company_stmt.excluded.company_url,
                    company_logo_url=company_stmt.excluded.company_logo_url,
                ),
            ).returning(Company.id, Company.name)
            for row in session.execute(company_upsert_stmt, company_data):
                name_to_id[row.name] = row.id

        job_data = [
            build_job_listing_model(item, company_id=name_to_id[item.company_name])
            for item in data
            if item.company_name
        ]

        if job_data:
            job_stmt = pg_insert(JobListing)
            job_upsert_stmt = job_stmt.on_conflict_do_update(
                index_elements=["external_id"],
                set_={col: getattr(job_stmt.excluded, col) for col in JOB_LISTING_REFRESHABLE_COLUMNS},
            )
            session.execute(job_upsert_stmt, job_data)
