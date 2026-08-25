import os
import json
from dataclasses import asdict
from dotenv import load_dotenv

from sources.rooster.rooster_scraper import RoosterScraper, payload as rooster_payload
from sources.itprolk.itprolk_scraper import ItProlkScraper
from models.job_listing import LLMExtractionInput, KnownFields, FreeTextFields
from parser.llm_extractor import extract

load_dotenv()

SAMPLE_SIZE = 5
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "extraction_sample.json")


def _to_jsonable(output) -> dict:
    data = asdict(output)
    data["category"] = output.category.value if output.category else None
    data["job_type"] = output.job_type.value if output.job_type else None
    data["experience_level"] = output.experience_level.value if output.experience_level else None
    return data


def run():
    results = []

    rooster = RoosterScraper(list_url=os.environ.get("ROOSTER_LISTING_URL"))
    for r in rooster.get_listings(rooster_payload)[:SAMPLE_SIZE]:
        out = extract(LLMExtractionInput(
            title=r.title,
            description=r.description,
            known_fields=KnownFields(),
            free_text_fields=FreeTextFields(),
        ))
        results.append({
            "source": r.source,
            "external_id": r.external_id,
            "title": r.title,
            "source_url": r.source_url,
            "extraction": _to_jsonable(out),
        })
        print(f"[rooster] extracted: {r.title}")

    itprolk = ItProlkScraper(list_url="https://itpro.lk/api/v1/jobs")
    for r in itprolk.get_listings({"limit": SAMPLE_SIZE})[:SAMPLE_SIZE]:
        out = extract(LLMExtractionInput(
            title=r.title,
            description=r.description,
            known_fields=KnownFields(),
            free_text_fields=FreeTextFields(),
        ))
        results.append({
            "source": r.source,
            "external_id": r.external_id,
            "title": r.title,
            "source_url": r.source_url,
            "extraction": _to_jsonable(out),
        })
        print(f"[itprolk] extracted: {r.title}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nWrote {len(results)} results to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
