import uuid
from models.job_listing import JobListing as ScrapedJobListing, SalaryFrequency
from utils.enums import enum_or_none


def _coerce_salary_frequency(value):
    if isinstance(value, SalaryFrequency) or value is None:
        return value
    return enum_or_none(SalaryFrequency, value)


def build_company_model(job: ScrapedJobListing) -> dict:
    # Company.name is unique + non-nullable: callers must skip/handle
    # listings with no company_name before calling this.
    return dict(
        id=uuid.uuid4(),
        name=job.company_name,
        company_url=job.company_url,
        company_logo_url=job.company_logo_url,
    )


def build_job_listing_model(job: ScrapedJobListing, company_id: uuid.UUID) -> dict:
    return dict(
        external_id=job.external_id,
        source=job.source,
        source_url=job.source_url,
        raw=job.raw,
        title=job.title,
        summary=job.summary,
        description=job.description,
        job_type=job.job_type,
        category=job.category,
        location=job.location,
        remote=job.remote,
        min_salary=job.min_salary,
        max_salary=job.max_salary,
        avg_salary=job.avg_salary,
        salary_currency=job.salary_currency,
        salary_frequency=_coerce_salary_frequency(job.salary_frequency),
        posted_at=job.posted_at,
        updated_at=job.updated_at,
        expires_at=job.expires_at,
        experience_level=job.experience_level,
        min_experience_years=job.min_experience_years,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        education_requirements=job.education_requirements or [],
        company_id=company_id,
        run_id=job.run_id,
    )
