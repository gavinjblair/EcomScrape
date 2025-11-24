from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Iterable
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .config import RequestSettings, DEFAULT_USER_AGENTS


@dataclass
class FetchRecord:
    url: str
    html: Optional[str]
    headers: Dict[str, str]
    status_code: Optional[int]
    error: Optional[str] = None


class Fetcher:
    def __init__(self, request_settings: RequestSettings, logger: Optional[logging.Logger] = None) -> None:
        # Keep network behaviours configurable so different sites can be tuned without code edits.
        self.settings = request_settings
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        # Retry strategy mirrors config, avoiding hard-coded status lists.
        retry_strategy = Retry(
            total=self.settings.max_retries,
            backoff_factor=self.settings.backoff_factor,
            status_forcelist=self.settings.retry_status_forcelist or [500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.failed_urls: List[str] = []
        self.records: List[FetchRecord] = []

    def _choose_headers(self) -> Dict[str, str]:
        headers = dict(self.settings.headers or {})
        user_agents = self.settings.user_agents or DEFAULT_USER_AGENTS
        # Rotate user-agents to appear more like real visitors.
        headers["User-Agent"] = random.choice(user_agents)
        return headers

    def fetch(self, url: str) -> FetchRecord:
        headers = self._choose_headers()
        parsed = urlparse(url)
        self.logger.debug("Requesting %s (host=%s) with User-Agent='%s'", url, parsed.netloc, headers.get("User-Agent"))
        try:
            response = self.session.get(url, headers=headers, timeout=self.settings.timeout)
            status = response.status_code
            response.raise_for_status()
            html = response.text
            error = None
        except Exception as exc:  # broad to continue scraping
            html = None
            status = None
            error = str(exc)
            self.failed_urls.append(url)
            self.logger.warning("Request failed for %s: %s", url, exc)

        if self.settings.delay_between_requests > 0:
            # Respect polite scraping by pausing between calls when requested.
            time.sleep(self.settings.delay_between_requests)

        record = FetchRecord(url=url, html=html, headers=headers, status_code=status, error=error)
        self.records.append(record)
        return record

    def fetch_all(self, urls: Iterable[str]) -> List[FetchRecord]:
        results: List[FetchRecord] = []
        url_list = list(urls)
        if self.settings.max_workers <= 1:
            for url in url_list:
                results.append(self.fetch(url))
            return results

        from concurrent.futures import ThreadPoolExecutor, as_completed

        self.logger.debug("Fetching %s URLs with max_workers=%s", len(url_list), self.settings.max_workers)
        with ThreadPoolExecutor(max_workers=self.settings.max_workers) as executor:
            future_to_url = {executor.submit(self.fetch, url): url for url in url_list}
            for future in as_completed(future_to_url):
                try:
                    results.append(future.result())
                except Exception as exc:
                    failing_url = future_to_url[future]
                    self.logger.warning("Fetch failed for %s: %s", failing_url, exc)
        return results

    def summary(self) -> Dict[str, int]:
        # Provide a lightweight roll-up for CLI logging and tests.
        successes = len([r for r in self.records if r.html is not None])
        failures = len(self.failed_urls)
        return {"successes": successes, "failures": failures}
