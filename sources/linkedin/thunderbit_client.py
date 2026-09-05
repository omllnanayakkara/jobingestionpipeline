import json
import logging
import os
import time
from typing import Any

import requests

logger = logging.getLogger("thunderbit_client")


class ThunderbitError(Exception):
    pass


class ThunderbitClient:

    DEFAULT_BASE_URL = "https://openapi.thunderbit.com/openapi/v1"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.environ.get("THUNDERBIT_API_KEY")
        self.base_url = (base_url or os.environ.get("THUNDERBIT_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")

        if not self.api_key:
            raise ValueError("THUNDERBIT_API_KEY is not defined")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    @staticmethod
    def _looks_like_schema_metadata(item: Any) -> bool:
        if not isinstance(item, dict):
            return False

        keys = set(item.keys())
        if not {"type", "properties", "required"}.issubset(keys):
            return False

        properties = item.get("properties")
        required = item.get("required")
        if isinstance(properties, str) and isinstance(required, str):
            try:
                embedded_properties = json.loads(properties)
            except (TypeError, ValueError):
                return True
            return isinstance(embedded_properties, dict) and (
                "type" in embedded_properties or "properties" in embedded_properties
            )

        if item.get("type") in {"object", "array", "string", "number", "boolean"}:
            return True

        return False

    @staticmethod
    def _decode_embedded_object(item: Any) -> Any:
        if not isinstance(item, dict) or not isinstance(item.get("properties"), str):
            return item

        try:
            properties = json.loads(item["properties"])
        except (TypeError, ValueError):
            return item

        if isinstance(properties, dict) and "type" not in properties and "properties" not in properties:
            return properties
        return item

    def _normalise_data(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            if payload.get("data") is not None:
                return self._normalise_data(payload.get("data"))
            if payload.get("jobs") is not None:
                return payload.get("jobs")
            if payload.get("result") is not None:
                return self._normalise_data(payload.get("result"))
            return payload

        if isinstance(payload, list):
            cleaned = []
            for item in payload:
                if self._looks_like_schema_metadata(item):
                    continue
                cleaned.append(self._decode_embedded_object(item))
            return cleaned

        return payload

    def _log_debug_response(self, *, url: str, status_code: int | None, response_text: str, elapsed_seconds: float, request_payload: dict):
        logger.debug(
            "Thunderbit request summary: url=%s status=%s elapsed_seconds=%.2f request_payload=%s response_body=%s",
            url,
            status_code,
            elapsed_seconds,
            json.dumps({k: v for k, v in request_payload.items() if k != "schema"}, default=str),
            response_text[:2000],
        )

    def extract(
        self,
        url: str,
        schema: dict,
        render_mode: str = "full",
        timeout: int = 30,
        retries: int = 2,
    ) -> dict | list | None:
        if not url:
            raise ThunderbitError("LinkedIn extraction URL is empty")

        request_payload = {
            "url": url,
            "schema": schema,
            "renderMode": render_mode,
            "timeout": timeout,
        }

        last_error = None
        for attempt in range(retries + 1):
            started = time.monotonic()
            try:
                response = self.session.post(
                    f"{self.base_url}/extract",
                    json=request_payload,
                    timeout=timeout + 10,
                )
                elapsed = time.monotonic() - started
                body = response.text[:4000]
                self._log_debug_response(
                    url=url,
                    status_code=response.status_code,
                    response_text=body,
                    elapsed_seconds=elapsed,
                    request_payload=request_payload,
                )

                if not response.ok:
                    raise ThunderbitError(
                        f"Thunderbit extraction failed for {url} ({response.status_code}): {body}"
                    )

                try:
                    payload = response.json()
                except ValueError as exc:
                    raise ThunderbitError(f"Thunderbit returned invalid JSON for {url}: {body}") from exc

                if payload.get("success") is False:
                    msg = payload.get("error", {}).get("message") or "Unknown Thunderbit error"
                    raise ThunderbitError(f"Thunderbit extraction failed for {url}: {msg}")

                data = self._normalise_data(payload)
                if isinstance(data, dict):
                    if data.get("success") is False:
                        raise ThunderbitError(data.get("error", {}).get("message") or "Unknown Thunderbit error")
                    if "jobs" in data:
                        return data.get("jobs") or []
                    if "data" in data:
                        cleaned = self._normalise_data(data.get("data"))
                        if not cleaned:
                            raise ThunderbitError(
                                "Thunderbit returned schema metadata instead of actual LinkedIn job data for this URL"
                            )
                        return cleaned
                    if self._looks_like_schema_metadata(data):
                        raise ThunderbitError(
                            "Thunderbit returned schema metadata instead of actual LinkedIn job data for this URL"
                        )
                    return data
                if isinstance(data, list):
                    if not data:
                        return []
                    if all(self._looks_like_schema_metadata(item) for item in data):
                        raise ThunderbitError(
                            "Thunderbit returned schema metadata instead of actual LinkedIn job data for this URL"
                        )
                    return data
                return []

            except requests.exceptions.Timeout as exc:
                last_error = exc
                if attempt < retries:
                    sleep_seconds = 2 ** attempt
                    logger.warning("Thunderbit timeout for %s; retrying in %s seconds (attempt %s/%s)", url, sleep_seconds, attempt + 1, retries + 1)
                    time.sleep(sleep_seconds)
                    continue
                raise ThunderbitError(f"Thunderbit request timed out for {url} after {retries + 1} attempts") from exc
            except requests.RequestException as exc:
                last_error = exc
                if attempt < retries:
                    sleep_seconds = 2 ** attempt
                    logger.warning("Thunderbit HTTP error for %s; retrying in %s seconds (attempt %s/%s)", url, sleep_seconds, attempt + 1, retries + 1)
                    time.sleep(sleep_seconds)
                    continue
                raise ThunderbitError(f"Thunderbit request failed for {url}: {exc}") from exc
            except ThunderbitError:
                raise

        if last_error is not None:
            raise ThunderbitError(f"Thunderbit extraction failed for {url}: {last_error}")
        return []

    def batch_extract(
        self,
        urls: list[str],
        schema: dict,
        render_mode: str = "full",
        timeout: int = 60000,
    ) -> str:

        response = self.session.post(
            f"{self.BASE_URL}/batch/extract",
            json={
                "urls": urls,
                "schema": schema,
                "renderMode": render_mode,
                "timeout": timeout,
            },
            timeout=30,
        )

        if not response.ok:
            raise ThunderbitError(
                f"Thunderbit batch extraction failed "
                f"({response.status_code}): {response.text}"
            )

        result = response.json()

        if not result.get("success"):
            raise ThunderbitError(
                result.get("error", {}).get(
                    "message",
                    "Unknown Thunderbit error"
                )
            )

        return result["data"]["id"]

    def get_batch_extract_status(
        self,
        batch_id: str,
    ) -> dict:

        response = self.session.get(
            f"{self.BASE_URL}/batch/extract/{batch_id}",
            timeout=30,
        )

        if not response.ok:
            raise ThunderbitError(
                f"Thunderbit batch status failed "
                f"({response.status_code}): {response.text}"
            )

        result = response.json()

        if not result.get("success"):
            raise ThunderbitError(
                result.get("error", {}).get(
                    "message",
                    "Unknown Thunderbit error"
                )
            )

        return result["data"]

    def wait_for_batch(
        self,
        batch_id: str,
        poll_interval: int = 5,
        max_wait: int = 600,
    ) -> dict:

        started = time.time()

        while True:

            result = self.get_batch_extract_status(batch_id)

            status = result.get("status")

            if status == "COMPLETED":
                return result

            if status in {
                "FAILED",
                "CANCELLED",
            }:
                raise ThunderbitError(
                    f"Thunderbit batch {status}: "
                    f"{result}"
                )

            if time.time() - started > max_wait:
                raise ThunderbitError(
                    f"Thunderbit batch timed out: {batch_id}"
                )

            time.sleep(poll_interval)