import unittest

from dotenv import load_dotenv

from models.job_listing import JobListing
from notifications.factory import get_notification_service


class AzureEventGridNotificationServiceTests(unittest.TestCase):
    def test_backend_notification_service_reaches_azure(self):
        load_dotenv(dotenv_path=".env", override=True)
        service, recipient = get_notification_service()
        self.assertIsNotNone(service)
        self.assertIsNotNone(recipient)

        job = JobListing(
            external_id="test-001",
            source="notification-test",
            source_url="https://example.test/jobs/test-001",
            raw="real Event Grid notification service test",
            title="Notification Service Integration Test",
            summary="Synthetic test event for Azure Event Grid.",
            description="This is a synthetic integration test and is not a real job listing.",
            company_name="Notification Test Company",
            company_url=None,
            company_logo_url=None,
            job_type=None,
            category=None,
            location="Remote",
            remote=True,
            min_salary=None,
            max_salary=None,
            avg_salary=None,
            salary_currency=None,
            salary_frequency=None,
            posted_at=None,
            updated_at=None,
            expires_at=None,
            run_id=None,
            required_skills=[],
            preferred_skills=[],
            experience_level=None,
            min_experience_years=None,
            education_requirements=None,
        )

        result = service.publish_new_match(job, recipient)

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()