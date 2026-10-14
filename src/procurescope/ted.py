from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchPage:
    page_number: int
    body: bytes
    payload: dict
    iteration_next_token: str | None


class TedSearchClient:
    """Small client for the public, read-only TED Search API."""

    def __init__(
        self,
        api_url: str,
        page_size: int = 100,
        timeout_seconds: int = 45,
        session: requests.Session | None = None,
    ) -> None:
        self.api_url = api_url
        self.page_size = min(max(page_size, 1), 250)
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"POST"}),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )

    def iter_pages(self, query: str, fields: list[str]) -> Iterator[SearchPage]:
        token: str | None = None
        page_number = 0
        seen_tokens: set[str] = set()

        while True:
            page_number += 1
            body = {
                "query": query,
                "fields": fields,
                "limit": self.page_size,
                "paginationMode": "ITERATION",
            }
            if token:
                body["iterationNextToken"] = token

            response = self.session.post(
                self.api_url,
                json=body,
                timeout=self.timeout_seconds,
            )
            if response.status_code == 429:
                # Retry handles most rate limits. This delay also covers servers that
                # return 429 without a Retry-After header.
                time.sleep(2)
            response.raise_for_status()
            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"TED returned invalid JSON on page {page_number}"
                ) from exc
            if not isinstance(payload, dict):
                raise ValueError(f"TED response on page {page_number} was not an object")

            next_token = payload.get("iterationNextToken")
            if next_token and next_token in seen_tokens:
                raise RuntimeError("TED repeated an iteration token; stopping to avoid a loop")
            if next_token:
                seen_tokens.add(next_token)

            yield SearchPage(
                page_number=page_number,
                body=response.content,
                payload=payload,
                iteration_next_token=next_token,
            )
            if not next_token:
                break
            token = next_token
