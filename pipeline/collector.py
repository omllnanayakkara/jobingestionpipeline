import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from typing import Sequence
from models.job_listing import NormalizedListing
from sources.rooster.rooster_scraper import RoosterScraper
from sources.itprolk.itprolk_scraper import ItProlkScraper


def collect() -> Sequence[NormalizedListing]:
    rooster_listing_url = os.environ.get("ROOSTER_LISTING_URL")
    itprolk_listing_url = os.environ.get("ITPROLK_LISTING_URL")
    max_batch_size = int(os.environ.get("MAX_BATCH_SIZE", 2))
    print("max_batch_size", max_batch_size)
    listings = []
    print("collect started...")
    if rooster_listing_url is None:
        raise ValueError("ROOSTER_LISTING_URL is not defined")

    if itprolk_listing_url is None:
        raise ValueError("ITPROLK_LISTING_URL is not defined")
    

    scraper_list: Sequence[tuple] = [
        (
            RoosterScraper(list_url=rooster_listing_url),
            {
                "filters": {
                    "class": "Information & Communication Technology"
                },
                "limit": max_batch_size,
                "page": 1,
                "query": []
            }
        ),
        (
            ItProlkScraper(list_url=itprolk_listing_url),
            {
                "limit": max_batch_size
            }
        )
    ]
    print("thread pool started...")
    with ThreadPoolExecutor(max_workers=len(scraper_list)) as executor:
        futures = [executor.submit(scraper.get_listings, payload) for scraper, payload in scraper_list]
        for future in as_completed(futures, 60):            # lock is unnecessary because 'as_completed' yields futures one at a time on the calling thread, there's no concurrent access to listings
            listings.extend([listing.to_normalized_listing() for listing in future.result()])         # normlization  
    print("thread pool completed...")
    return listings
