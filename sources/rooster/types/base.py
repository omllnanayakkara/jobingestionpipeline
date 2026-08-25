import os
import json
import requests

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from sources.base import BaseResponse, SOURCE
from bs4 import BeautifulSoup
from models.job_listing import NormalizedListing, JobType, match_job_category

ROOSTER_JOB_TYPE_MAP = {
    "full-time": JobType.FULL_TIME,
    "part-time": JobType.PART_TIME,
    "contract": JobType.CONTRACT,
    "internship": JobType.INTERNSHIP,
}



def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

def _extract_company_url(company_id:str) -> Optional[str]:
    company_base_url = os.environ.get("ROOSTER_COMPANY_BASE_URL")
    if company_base_url is None:
        raise ValueError("ROOSTER_COMPANY_BASE_URL is not defined")
    page_content = requests.get(
        url=f"{company_base_url}/{company_id}"
    ).text

    soup = BeautifulSoup(page_content, "html.parser")

    link = soup.find("a", string="Visit Website")
    return str(link.get("href")) if link else None


@dataclass
class RoosterResponse(BaseResponse):
    company_id: int
    company_url: Optional[str]
    job_type: str
    location: str
    department: Optional[str]
    tags: list
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    remote: bool
    subclass: Optional[str]
    subsidiary_company_industry: Optional[str]
    subsidiary_company_name: Optional[str]
    company_logo_url: Optional[str]
    subsidiary_company_logo_url: Optional[str]
    min_salary: Optional[float]
    max_salary: Optional[float]
    salary_frequency: Optional[str]
    salary_currency: Optional[str]
    is_verified: bool
    job_class: Optional[str]
    raw_data: dict

    @property
    def source(self) -> str:
        return SOURCE.ROOSTER.value

    @property
    def source_url(self) -> str:
        source_url = os.environ.get("ROOSTER_COMPANY_BASE_URL")
        if source_url is None:
            raise ValueError("ROOSTER_COMPANY_BASE_URL is not defined")
        return f"{source_url}/{self.external_id}"

    @property
    def avg_salary(self) -> Optional[float]:
        if self.min_salary is not None and self.max_salary is not None:
            return (self.min_salary + self.max_salary) / 2
        return self.min_salary if self.min_salary is not None else self.max_salary

    @property
    def category(self) -> Optional[str]:
        return self.job_class

    @property
    def raw(self) -> str:
        return json.dumps(self.raw_data, default=str)

    def to_normalized_listing(self) -> NormalizedListing:
        listing = super().to_normalized_listing()
        listing.company_url = self.company_url
        listing.company_logo_url = self.company_logo_url
        listing.job_type = ROOSTER_JOB_TYPE_MAP.get(self.job_type, JobType.OTHER)
        listing.category = match_job_category(self.subclass)
        listing.location = self.location
        listing.remote = self.remote
        listing.min_salary = self.min_salary
        listing.max_salary = self.max_salary
        listing.salary_currency = self.salary_currency
        listing.salary_frequency = self.salary_frequency
        listing.posted_at = self.created_at
        listing.updated_at = self.updated_at
        return listing

    @classmethod
    def from_api(cls, item: dict) -> "RoosterResponse":
        return cls(
            external_id=str(item["id"]),
            title=item["title"],
            description=item["description"],
            company_name=item["company_name"],
            company_id=item["company_id"],
            company_url=_extract_company_url(item["company_id"]),
            job_type=item["job_type"],
            location=item["location"],
            department=item["department"],
            tags=item["tags"],
            created_at=_parse_datetime(item["created_at"]),
            updated_at=_parse_datetime(item["updated_at"]),
            remote=item["remote"],
            subclass=item["subclass"],
            subsidiary_company_industry=item["subsidiary_company_industry"],
            subsidiary_company_name=item["subsidiary_company_name"],
            company_logo_url=item["company_logo_url"],
            subsidiary_company_logo_url=item["subsidiary_company_logo_url"],
            min_salary=item["min_salary"],
            max_salary=item["max_salary"],
            salary_frequency=item["salary_frequency"],
            salary_currency=item["salary_currency"],
            is_verified=item["is_verified"],
            job_class=item["class"],
            raw_data=item,
        )