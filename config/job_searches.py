import os

from sources.linkedin.search_url import build_jobs_search_url

LINKEDIN_SEARCHES = [
    {
        "role": "Software Engineer",
        "keywords": "Software Engineer",
        "location": "Sri Lanka",
        "enabled": True,
    },
    {
        "role": "Software Engineer Intern",
        "keywords": "Software Engineer Intern",
        "location": "Sri Lanka",
        "enabled": True,
    },
    {
        "role": "Associate Software Engineer",
        "keywords": "Associate Software Engineer",
        "location": "Sri Lanka",
        "enabled": True,
    },
]


def get_linkedin_search_urls() -> list[str]:
    raw_urls = os.environ.get("LINKEDIN_SEARCH_URLS", "").strip()
    if raw_urls:
        return [url.strip() for url in raw_urls.split(",") if url.strip()]

    urls = []
    for item in LINKEDIN_SEARCHES:
        if not item.get("enabled", True):
            continue
        urls.append(
            build_jobs_search_url(
                keywords=item["keywords"],
                location=item["location"],
            )
        )
    return urls