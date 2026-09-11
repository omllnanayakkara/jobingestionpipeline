import os
import json
from dataclasses import asdict
import time

from .collector import collect
from .llm_extractor import extract
from .store import store
from models.job_listing import JobListing, KnownFields, FreeTextFields, LLMExtractionInput, JobCategory, ExperienceLevel, JobType
from utils.run_config import start_run, update_run
from notifications.factory import get_notification_service

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "extraction_sample.json")

def coalesce(*args):
    return next((item for item in args if item is not None), None)

if __name__ == "__main__":
    run_id = start_run()
    start_clock = time.perf_counter()

    batch_items = collect()                 # scrape from sources and deterministic normialization
    fianl_batch_items = []
        
    for item in batch_items:
        enriched_item = extract(            # LLM-base enhancements
            LLMExtractionInput(
                title=item.title,
                description=item.description,
                known_fields=KnownFields(),
                free_text_fields=FreeTextFields()
            )
        )

        job_listing_item = JobListing.from_normalized(item, run_id)
        job_listing_item.category = coalesce(item.category, enriched_item.category, JobCategory.OTHER)
        job_listing_item.experience_level = coalesce(enriched_item.experience_level, ExperienceLevel.OTHER)
        job_listing_item.job_type = coalesce(item.job_type, enriched_item.job_type, JobType.OTHER)
        job_listing_item.remote = coalesce(item.remote, enriched_item.remote, None)
        job_listing_item.avg_salary = coalesce(item.avg_salary, enriched_item.avg_salary, None)
        job_listing_item.salary_frequency = coalesce(item.salary_frequency, enriched_item.salary_frequency, None)
        job_listing_item.salary_currency = coalesce(item.salary_currency, enriched_item.salary_currency, None)
        job_listing_item.location = coalesce(item.location, enriched_item.location, None)
        job_listing_item.min_experience_years = enriched_item.min_experience_years
        job_listing_item.required_skills = enriched_item.required_skills
        job_listing_item.preferred_skills = enriched_item.preferred_skills
        job_listing_item.education_requirements = enriched_item.education_requirements

        fianl_batch_items.append(job_listing_item)

    store(fianl_batch_items)                # store in database

    notification_service, recipient = get_notification_service()
    if notification_service and recipient:
        for job in fianl_batch_items:
            notification_service.publish_new_match(job, recipient)

    end_clock = time.perf_counter()
    execution_time = end_clock - start_clock
    update_run(run_id, {"duration":execution_time})

    


