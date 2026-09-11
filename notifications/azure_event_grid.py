import os
import uuid
from datetime import datetime, timezone

from azure.core.credentials import AzureKeyCredential
from azure.eventgrid import EventGridEvent, EventGridPublisherClient

from models.job_listing import JobListing
from notifications.base import NotificationRecipient, NotificationService


EVENT_GRID_TOPIC = "new-job-events"


class AzureEventGridNotificationService(NotificationService):
    def __init__(self, client: EventGridPublisherClient):
        self._client = client

    @classmethod
    def from_environment(cls) -> "AzureEventGridNotificationService":
        endpoint = os.environ.get("EVENT_GRID_ENDPOINT")
        access_key = os.environ.get("EVENT_GRID_ACCESS_KEY")
        if not endpoint:
            raise ValueError("EVENT_GRID_ENDPOINT is not defined")
        if not access_key:
            raise ValueError("EVENT_GRID_ACCESS_KEY is not defined")

        return cls(EventGridPublisherClient(endpoint, AzureKeyCredential(access_key)))

    def publish_new_match(self, job: JobListing, recipient: NotificationRecipient) -> bool:
        event = EventGridEvent(
            id=str(uuid.uuid4()),
            subject=f"jobs/{job.external_id}",
            event_type="Job.NewMatch",
            event_time=datetime.now(timezone.utc),
            data_version="1.0",
            data={
                "jobId": str(job.external_id),
                "jobTitle": job.title,
                "company": job.company_name or "Unknown Company",
                "recipient": recipient.email,
            },
        )
        self._client.send([event])
        return True