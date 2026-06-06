from __future__ import annotations

from typing import Any

import requests

from .revenue_scoring import RevenueOpportunity


GITHUB_ISSUE_SEARCH_URL = "https://api.github.com/search/issues"


class GitHubIssuesClient:
    def __init__(self, *, token: str | None = None, session: Any | None = None, timeout: int = 20) -> None:
        self.token = token
        self.session = session or requests.Session()
        self.timeout = timeout

    def search_help_wanted_issues(
        self,
        *,
        query_terms: list[str],
        max_items: int = 20,
    ) -> list[RevenueOpportunity]:
        query = " ".join(query_terms + ["is:issue", "state:open", 'label:"help wanted"'])
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = self.session.get(
            GITHUB_ISSUE_SEARCH_URL,
            headers=headers,
            params={"q": query, "sort": "updated", "order": "desc", "per_page": max_items},
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub issue search failed: {response.status_code} {response.text}")

        opportunities: list[RevenueOpportunity] = []
        for item in response.json().get("items") or []:
            if "pull_request" in item:
                continue
            labels = [label.get("name", "") for label in item.get("labels") or []]
            repo_name = str(item.get("repository_url") or "").removeprefix("https://api.github.com/repos/")
            tags = [label for label in labels if label] + [part for part in repo_name.split("/") if part]
            opportunities.append(
                RevenueOpportunity(
                    source="github",
                    external_id=str(item["id"]),
                    title=str(item.get("title") or ""),
                    url=str(item.get("html_url") or ""),
                    problem=str(item.get("body") or "")[:2000],
                    tags=tags,
                    channel="github_issue_helper",
                    payout_estimate_usd=120.0,
                    conversion_probability=0.08,
                    estimated_cost_usd=2.0,
                    risk_penalty_usd=1.0,
                    build_minutes=45,
                )
            )
        return opportunities

    def discover(self) -> list[RevenueOpportunity]:
        return self.search_help_wanted_issues(
            query_terms=["supabase", "github actions", "fastapi", "openai api"],
            max_items=20,
        )
