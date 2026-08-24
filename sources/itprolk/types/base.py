import json
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from sources.base import BaseResponse, SOURCE

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
    website: Optional[str]
    views_count: Optional[int]
    created_on: Optional[datetime]
    raw_data: dict

    @property
    def source(self) -> str:
        return SOURCE.ITPROLK.value

    @property
    def source_url(self) -> str:
        return f"https://itpro.lk/job/{self.external_id}/"

    @property
    def avg_salary(self) -> Optional[float]:
        return None

    @property
    def category(self) -> Optional[str]:
        return CATEGORY_MAP.get(self.category_id, self.category_id)

    @property
    def raw(self) -> str:
        return json.dumps(self.raw_data, default=str)

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
            website=item.get("website"),
            views_count=int(views_count) if views_count is not None else None,
            created_on=_parse_datetime(item.get("created_on")),
            raw_data=item,
        )
