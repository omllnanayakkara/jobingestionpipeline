from abc import ABC, abstractmethod
from typing import Optional, Sequence
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from enum import Enum

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
