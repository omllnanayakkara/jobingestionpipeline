import os

from dotenv import load_dotenv

from sources.linkedin.search_url import build_jobs_search_url
from sources.linkedin.schemas import LINKEDIN_DISCOVERY_SCHEMA
from sources.linkedin.thunderbit_client import ThunderbitClient


load_dotenv()


def validate_configuration() -> str:
    missing = []
    if not os.environ.get("THUNDERBIT_API_KEY"):
        missing.append("THUNDERBIT_API_KEY")

    url = build_jobs_search_url(
        keywords="Software Engineer",
        location="Sri Lanka",
    )
    if not url:
        missing.append("LINKEDIN_SEARCH_URLS")

    if missing:
        raise RuntimeError(f"Missing configuration: {', '.join(missing)}")

    return url


def main() -> None:
    url = validate_configuration()
    client = ThunderbitClient()

    print("Testing single LinkedIn search URL:")
    print(url)

    print("\nSending minimal Thunderbit extraction request:")
    payload = {
        "url": url,
        "schema": LINKEDIN_DISCOVERY_SCHEMA,
        "renderMode": "full",
        "timeout": 30,
    }
    print(payload)

    try:
        result = client.extract(
            url=url,
            schema=LINKEDIN_DISCOVERY_SCHEMA,
            render_mode="full",
            timeout=30,
            retries=2,
        )
        print("\nSuccess. Discovered job URLs:")
        print(result)
    except Exception as exc:
        print(f"\nLinkedIn discovery failed: {exc}")
        raise


if __name__ == "__main__":
    main()