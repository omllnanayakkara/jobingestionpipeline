import os
import json
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from sources.base import BaseResponse, SOURCE
from models.job_listing import NormalizedListing, JobType, match_job_category

ITPRO_JOB_TYPE_MAP = {
    "FULL_TIME": JobType.FULL_TIME,
    "PART_TIME": JobType.PART_TIME,
    "CONTRACTOR": JobType.CONTRACT,
    "INTERN": JobType.INTERNSHIP,
}

CATEGORY_MAP = {
    "18": "AI and Data",
    "19": "Hardware and Networking",
    "20": "Management and Business",
    "21": "Software Engineering",
    "27": "Design and Creative",
    "37": "IT and Operations",
    "39": "Quality Assurance",
    "40": "Digital Marketing",
    "41": "Mobile Development",
    "42": "Web Development",
    "43": "Academic",
    "44": "DevOps and Cloud",
}

TYPE_MAP = {
    "1": "FULL_TIME",
    "2": "PART_TIME",
    "3": "CONTRACTOR",
    "4": "INTERN",
}

LOCATION_MAP = {
    "74": "Kandy",
    "75": "Jaffna",
    "79": "Colombo",
    "80": "Gampaha",
    "81": "Kurunegala",
    "82": "Galle",
    "83": "Matara",
    "85": "Vavuniya",
}


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


@dataclass
class ItProlkResponse(BaseResponse):
    summary: Optional[str]
    type_id: Optional[str]
    job_type: Optional[str]
    category_id: Optional[str]
    location_id: Optional[str]
    location: Optional[str]
    company_url: Optional[str]
    views_count: Optional[int]
    created_on: Optional[datetime]
    raw_data: dict

    @property
    def source(self) -> str:
        return SOURCE.ITPROLK.value

    @property
    def source_url(self) -> str:
        source_base_url=os.environ.get("ITPROLK_JOB_DETAILS_URL")
        if source_base_url is None:
            raise ValueError("ITPROLK_JOB_DETAILS_URL is not defined")
        return f"{source_base_url}/{self.external_id}/"

    @property
    def avg_salary(self) -> Optional[float]:
        return None

    @property
    def category(self) -> Optional[str]:
        return CATEGORY_MAP.get(self.category_id, self.category_id)

    @property
    def raw(self) -> str:
        return json.dumps(self.raw_data, default=str)

    def to_normalized_listing(self) -> NormalizedListing:
        listing = super().to_normalized_listing()
        listing.summary = self.summary
        listing.company_url = self.company_url
        listing.job_type = ITPRO_JOB_TYPE_MAP.get(self.job_type, JobType.OTHER)
        listing.category = match_job_category(self.category)
        listing.location = self.location
        listing.posted_at = self.created_on
        return listing

    @classmethod
    def from_api(cls, item: dict) -> "ItProlkResponse":
        type_id = item.get("type_id")
        location_id = item.get("location")
        views_count = item.get("views_count")
        return cls(
            external_id=str(item["id"]),
            title=item["title"],
            description=item["description"],
            company_name=item.get("company"),
            summary=item.get("summary"),
            type_id=type_id,
            job_type=TYPE_MAP.get(type_id, type_id),
            category_id=item.get("category_id"),
            location_id=location_id,
            location=LOCATION_MAP.get(location_id, location_id),
            company_url=item.get("website"),
            views_count=int(views_count) if views_count is not None else None,
            created_on=_parse_datetime(item.get("created_on")),
            raw_data=item,
        )
