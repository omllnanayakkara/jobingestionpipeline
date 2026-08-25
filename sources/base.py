from abc import ABC, abstractmethod
from typing import Optional, Sequence
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from enum import Enum
from models.job_listing import NormalizedListing

class SOURCE(Enum):
    ROOSTER = "rooster"
    ITPROLK = "itprolk"
    TOPJOBSLK = "topjobslk"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    

@dataclass
class BaseResponse:
    external_id: str
    title: str
    description: str
    company_name: Optional[str]

    @property
    @abstractmethod
    def source(self) -> str:
        ...

    @property
    @abstractmethod
    def source_url(self) -> str:
        ...

    @property
    @abstractmethod
    def avg_salary(self) -> Optional[float]:
        ...

    @property
    @abstractmethod
    def category(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def raw(self) -> str:
        ...

    def to_normalized_listing(self) -> NormalizedListing:
        return NormalizedListing(
            external_id=self.external_id,
            source=self.source,
            source_url=self.source_url,
            raw=self.raw,
            title=self.title,
            summary=None,
            description=self.description,
            company_name=self.company_name,
            company_url=None,
            company_logo_url=None,
            job_type=None,
            category=None,
            location=None,
            remote=None,
            min_salary=None,
            max_salary=None,
            avg_salary=self.avg_salary,
            salary_currency=None,
            salary_frequency=None,
            posted_at=None,
            updated_at=None,
            expires_at=None
        )

class BaseScraper(ABC):
    _list_url: str
    _details_url: Optional[str]

    @property
    def list_url(self) -> str:
        return self._list_url

    @property
    def details_url(self) -> Optional[str]:
        return self._details_url

    @abstractmethod
    def get_listings(self, payload:dict) -> Sequence[BaseResponse]:
        NotImplementedError()

    
