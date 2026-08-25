import os
import requests
from typing import Sequence
from sources.base import BaseResponse, BaseScraper
from sources.itprolk.types.base import ItProlkResponse
from dotenv import load_dotenv

load_dotenv()

class ItProlkScraper(BaseScraper):
    def __init__(self, list_url, details_url=None):
        self._list_url = list_url
        self._details_url = details_url

    def get_listings(self, payload: dict) -> Sequence[BaseResponse]:
        try:
            response = requests.get(
                url=self._list_url,
                params=payload
            )
            data = response.json()
            listings = [ItProlkResponse.from_api(item) for item in data]
            return listings
        except Exception as e:
            print(f"Error occurred: {e}")
            return []


if __name__ == "__main__":
    test_itprolk = ItProlkScraper(
        list_url=os.environ.get("ITPROLK_LISTING_URL")
    )

    listings = test_itprolk.get_listings({"limit": 20})
    print(listings)

    normalized = [item.to_normalized_listing() for item in listings]
    
    print(normalized)