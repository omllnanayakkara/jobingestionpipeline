from abc import ABC, abstractmethod
from dataclasses import dataclass

from models.job_listing import JobListing


@dataclass(frozen=True)
class NotificationRecipient:
    id: str
    email: str


class NotificationService(ABC):
    @abstractmethod
    def publish_new_match(self, job: JobListing, recipient: NotificationRecipient) -> bool:
        raise NotImplementedError