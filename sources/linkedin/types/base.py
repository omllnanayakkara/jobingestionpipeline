import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from models.job_listing import NormalizedListing, JobType


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value)


def parse_job_type(value: Optional[str]) -> Optional[JobType]:
    if not value:
        return None
    v = value.lower()
    if "full" in v:
        return JobType.FULL_TIME
    if "part" in v:
        return JobType.PART_TIME
    if "contract" in v:
        return JobType.CONTRACT
    if "intern" in v:
        return JobType.INTERNSHIP
    return JobType.OTHER


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d %b %Y",
        "%d %B %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_salary(value: Optional[str]) -> tuple[Optional[float], Optional[float], Optional[float], Optional[str], Optional[str]]:
    if not value:
        return None, None, None, None, None

    text = value.strip()
    if not text:
        return None, None, None, None, None

    currency = None
    if re.search(r"(LKR|USD|EUR|GBP|AUD|CAD|INR|PKR)", text, re.I):
        currency = re.search(r"(LKR|USD|EUR|GBP|AUD|CAD|INR|PKR)", text, re.I).group(1).upper()

    number_matches = re.findall(r"\d[\d,]*(?:\.\d+)?", text.replace(" ", ""))
    if not number_matches:
        return None, None, None, currency, None

    nums = [float(n.replace(",", "")) for n in number_matches[:4]]
    if len(nums) == 1:
        return nums[0], None, nums[0], currency, None
    if len(nums) >= 2:
        return nums[0], nums[-1], sum(nums) / len(nums), currency, None
    return None, None, None, currency, None


@dataclass
class LinkedInResponse:
    external_id: str
    source_url: str
    title: str
    description: str
    company_name: Optional[str] = None
    company_url: Optional[str] = None
    company_logo_url: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    posted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    remote: Optional[bool] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    avg_salary: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_frequency: Optional[str] = None
    raw_data: dict | None = None

    @classmethod
    def from_api(cls, data: dict, source_url: str, external_id: str) -> "LinkedInResponse":
        if not isinstance(data, dict):
            raise ValueError("LinkedIn detail payload must be a dictionary")

        extraction = {
            "title": data.get("title") or data.get("job_title") or data.get("jobTitle") or "",
            "description": data.get("description") or data.get("job_description") or data.get("jobDescription") or "",
            "company_name": _coerce_str(data.get("company_name") or data.get("company") or data.get("companyName")),
            "company_url": _coerce_str(data.get("company_url") or data.get("companyWebsite") or data.get("company_website")),
            "company_logo_url": _coerce_str(data.get("company_logo_url") or data.get("logo_url") or data.get("logoUrl")),
            "location": _coerce_str(data.get("location") or data.get("job_location") or data.get("jobLocation")),
            "job_type": data.get("job_type") or data.get("employment_type") or data.get("employmentType"),
            "remote": data.get("remote"),
            "posted_at": data.get("posted_at") or data.get("postedDate") or data.get("posted_date"),
            "updated_at": data.get("updated_at") or data.get("updatedDate") or data.get("updated_date"),
            "expires_at": data.get("expires_at") or data.get("expiresAt") or data.get("application_deadline"),
            "salary_text": data.get("salary_text") or data.get("salary") or data.get("salaryText"),
        }

        min_salary, max_salary, avg_salary, salary_currency, salary_frequency = parse_salary(extraction["salary_text"])

        return cls(
            external_id=external_id or source_url,
            source_url=source_url,
            title=extraction["title"],
            description=extraction["description"],
            company_name=extraction["company_name"],
            company_url=extraction["company_url"],
            company_logo_url=extraction["company_logo_url"],
            location=extraction["location"],
            job_type=parse_job_type(extraction["job_type"]),
            posted_at=parse_datetime(extraction["posted_at"]),
            updated_at=parse_datetime(extraction["updated_at"]),
            expires_at=parse_datetime(extraction["expires_at"]),
            remote=extraction["remote"],
            min_salary=min_salary,
            max_salary=max_salary,
            avg_salary=avg_salary,
            salary_currency=salary_currency,
            salary_frequency=salary_frequency,
            raw_data=data,
        )

    def to_normalized_listing(self) -> NormalizedListing:
        return NormalizedListing(
            external_id=self.external_id,
            source="linkedin",
            source_url=self.source_url,
            raw=json.dumps(self.raw_data or {}, ensure_ascii=False),
            title=self.title,
            summary=None,
            description=self.description,
            company_name=self.company_name,
            company_url=self.company_url,
            company_logo_url=self.company_logo_url,
            job_type=self.job_type,
            category=None,
            location=self.location,
            remote=self.remote,
            min_salary=self.min_salary,
            max_salary=self.max_salary,
            avg_salary=self.avg_salary,
            salary_currency=self.salary_currency,
            salary_frequency=self.salary_frequency,
            posted_at=self.posted_at,
            updated_at=self.updated_at,
            expires_at=self.expires_at,
        )