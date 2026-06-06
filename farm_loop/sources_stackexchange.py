from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .config import DEFAULT_TAGS


STACKEXCHANGE_ADVANCED_SEARCH_URL = "https://api.stackexchange.com/2.3/search/advanced"


@dataclass(frozen=True)
class SearchResult:
    questions: list[dict[str, Any]]
    backoff_seconds: int | None = None
    quota_remaining: int | None = None


class StackExchangeClient:
    def __init__(
        self,
        *,
        key: str | None = None,
        tags: str = DEFAULT_TAGS,
        site: str = "stackoverflow",
        session: Any | None = None,
        timeout: int = 20,
    ) -> None:
        self.key = key
        self.tags = tags
        self.site = site
        self.session = session or requests.Session()
        self.timeout = timeout

    def search_unanswered(self, *, page_size: int = 20) -> SearchResult:
        params: dict[str, Any] = {
            "site": self.site,
            "order": "desc",
            "sort": "activity",
            "accepted": "False",
            "answers": 0,
            "closed": "False",
            "tagged": self.tags,
            "pagesize": page_size,
            "filter": "withbody",
        }
        if self.key:
            params["key"] = self.key

        response = self.session.get(
            STACKEXCHANGE_ADVANCED_SEARCH_URL,
            params=params,
            timeout=self.timeout,
        )
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
        data = response.json()

        if data.get("error_id"):
            name = data.get("error_name", "stackexchange_error")
            message = data.get("error_message", "unknown error")
            raise RuntimeError(f"{name}: {message}")

        return SearchResult(
            questions=list(data.get("items") or []),
            backoff_seconds=data.get("backoff"),
            quota_remaining=data.get("quota_remaining"),
        )
