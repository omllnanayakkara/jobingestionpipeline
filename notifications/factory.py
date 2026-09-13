import os

from notifications.azure_event_grid import AzureEventGridNotificationService
from notifications.base import NotificationRecipient, NotificationService


def get_notification_service() -> tuple[NotificationService | None, NotificationRecipient | None]:
    endpoint = os.environ.get("EVENT_GRID_ENDPOINT")
    access_key = os.environ.get("EVENT_GRID_ACCESS_KEY")
    recipient_email = os.environ.get("NOTIFICATION_RECIPIENT_EMAIL")

    if not endpoint and not access_key and not recipient_email:
        return None, None
    if not recipient_email:
        raise ValueError("NOTIFICATION_RECIPIENT_EMAIL is not defined")

    return (
        AzureEventGridNotificationService.from_environment(),
        NotificationRecipient(
            id=os.environ.get("NOTIFICATION_RECIPIENT_ID", recipient_email),
            email=recipient_email,
        ),
    )