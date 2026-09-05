import logging
import os
import re
from typing import Sequence

import requests
from bs4 import BeautifulSoup

from sources.base import BaseResponse, BaseScraper
from sources.linkedin.schemas import LINKEDIN_DETAIL_SCHEMA, LINKEDIN_DISCOVERY_SCHEMA
from sources.linkedin.thunderbit_client import ThunderbitClient, ThunderbitError
from sources.linkedin.types.base import LinkedInResponse

logger = logging.getLogger("linkedin_scraper")


class LinkedInScraper(BaseScraper):
    def __init__(self, list_url: str | None = None, details_url: str | None = None, thunderbit_client: ThunderbitClient | None = None, search_urls: list[str] | None = None):
        self._list_url = list_url or os.environ.get("LINKEDIN_SEARCH_URLS", "")
        self._details_url = details_url
        self.thunderbit = thunderbit_client or ThunderbitClient()
        self.render_mode = os.environ.get("LINKEDIN_RENDER_MODE", "full")
        self.search_urls = search_urls or []

    def discover_jobs(self, search_url: str) -> list[dict]:
        if not search_url:
            return []

        logger.info("[LinkedIn] Discovering jobs from %s", search_url)
        try:
            result = self.thunderbit.extract(
                url=search_url,
                schema=LINKEDIN_DISCOVERY_SCHEMA,
                render_mode=self.render_mode,
                timeout=60,
            )
        except ThunderbitError as exc:
            logger.warning("[LinkedIn] Failed to discover jobs from %s: %s", search_url, exc)
            return self._discover_from_search_page(search_url)

        if isinstance(result, list):
            jobs = result
        elif isinstance(result, dict):
            jobs = result.get("jobs", [])
        else:
            jobs = []

        if isinstance(jobs, dict):
            jobs = [jobs]

        discovered = [job for job in jobs if isinstance(job, dict)]
        if discovered and all(not (job.get("job_url") or job.get("source_url") or job.get("url")) for job in discovered):
            discovered = self._attach_search_page_urls(search_url, discovered)
        elif not discovered:
            discovered = self._discover_from_search_page(search_url)
        return discovered

    @staticmethod
    def _search_page_links(search_url: str) -> list[str]:
        try:
            response = requests.get(
                search_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("[LinkedIn] Failed to recover job URLs from %s: %s", search_url, exc)
            return []

        links = []
        for anchor in BeautifulSoup(response.text, "html.parser").select('a[href*="/jobs/view/"]'):
            href = anchor.get("href")
            if href and href not in links:
                links.append(href)
        return links

    @classmethod
    def _attach_search_page_urls(cls, search_url: str, jobs: list[dict]) -> list[dict]:
        for job, job_url in zip(jobs, cls._search_page_links(search_url)):
            job["job_url"] = job_url
        return jobs

    @classmethod
    def _discover_from_search_page(cls, search_url: str) -> list[dict]:
        return [{"job_url": job_url} for job_url in cls._search_page_links(search_url)]

    def extract_job(self, job: dict) -> LinkedInResponse | None:
        if not isinstance(job, dict):
            return None

        job_url = job.get("job_url") or job.get("source_url") or job.get("url")
        if not job_url:
            logger.warning("[LinkedIn] Skipping job without URL: %s", job)
            return None

        external_id = job.get("job_id") or job.get("external_id") or self.extract_job_id(job_url)
        if not external_id:
            logger.warning("[LinkedIn] Skipping job without external ID: %s", job_url)
            return None

        logger.info("[LinkedIn] Extracting %s", job_url)
        try:
            result = self.thunderbit.extract(
                url=job_url,
                schema=LINKEDIN_DETAIL_SCHEMA,
                render_mode=self.render_mode,
                timeout=60,
            )
        except ThunderbitError as exc:
            logger.warning("[LinkedIn] Failed to extract %s: %s", job_url, exc)
            return None

        if not result:
            return None

        if isinstance(result, list):
            detail = result[0] if result else {}
        elif isinstance(result, dict):
            detail = result if "title" in result or "description" in result else result.get("data", {})
            if isinstance(detail, list):
                detail = detail[0] if detail else {}
        else:
            detail = {}

        if not isinstance(detail, dict):
            return None

        return LinkedInResponse.from_api(
            data=detail,
            source_url=job_url,
            external_id=str(external_id),
        )

    def get_listings(self, payload: dict) -> Sequence[BaseResponse]:
        search_urls = payload.get("search_urls") or self.search_urls or [self._list_url]
        limit = int(payload.get("limit", 5) or 5)
        results: list[BaseResponse] = []

        for search_url in search_urls:
            discovered_jobs = self.discover_jobs(search_url)
            for job in discovered_jobs[:limit]:
                try:
                    listing = self.extract_job(job)
                    if listing:
                        results.append(listing)
                except Exception as exc:
                    logger.warning("[LinkedIn] Failed to normalize job from %s: %s", search_url, exc)
        return results

    @staticmethod
    def extract_job_id(url: str) -> str | None:
        match = re.search(r"/jobs/view/(?:[^/?]+-)?(\d+)(?:[/?]|$)", url)
        if match:
            return match.group(1)
        return None