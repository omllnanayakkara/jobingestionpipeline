import os
import requests
import json
from typing import Sequence
from sources.base import BaseResponse, BaseScraper
from sources.rooster.types.base import RoosterResponse
from dotenv import load_dotenv

load_dotenv()

payload={
    "filters": {
        "class": "Information & Communication Technology"
    },
    "limit": 20,
    "page": 1,
    "query": []
}

class RoosterScraper(BaseScraper):
    def __init__(self, list_url, details_url=None):
        self._list_url=list_url
        self._details_url=details_url

    def get_listings(self, payload:dict) -> Sequence[BaseResponse]:
        try:
            response = requests.post(
                url=self._list_url,
                json=payload
            )
            data=json.loads(response.text)
            listings = [RoosterResponse.from_api(item) for item in data["body"]["data"]]
            return listings
        except Exception as e:
            print(f"Error occurred: {e}")
            return []


if __name__=="__main__":
    test_rooster = RoosterScraper(
        list_url=os.environ.get("ROOSTER_LISTING_URL")
    )

    listings=test_rooster.get_listings(payload)
    print(listings)

    normalized = [item.to_normalized_listing() for item in listings]

    print(normalized)

    
