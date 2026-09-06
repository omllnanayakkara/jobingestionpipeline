from urllib.parse import quote_plus


def build_jobs_search_url(
    keywords: str,
    location: str,
) -> str:
    encoded_keywords = quote_plus(keywords)
    encoded_location = quote_plus(location)

    return (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={encoded_keywords}"
        f"&location={encoded_location}"
        "&f_TPR=r3600"
    )