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

    def search_bounty_issues(
        self,
        *,
        query_terms: list[str],
        max_items: int = 20,
    ) -> list[RevenueOpportunity]:
        query_variants = [
            " ".join(query_terms + ["is:issue", "state:open", "bounty"]),
            " ".join(query_terms + ["is:issue", "state:open", 'label:"good first issue"', "documentation"]),
        ]
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        opportunities: list[RevenueOpportunity] = []
        seen_ids: set[str] = set()
        for query in query_variants:
            response = self.session.get(
                GITHUB_ISSUE_SEARCH_URL,
                headers=headers,
                params={"q": query, "sort": "updated", "order": "desc", "per_page": max_items},
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                raise RuntimeError(f"GitHub bounty issue search failed: {response.status_code} {response.text}")

            for item in response.json().get("items") or []:
                external_id = str(item["id"])
                if external_id in seen_ids or "pull_request" in item:
                    continue
                labels = [label.get("name", "") for label in item.get("labels") or []]
                if self._is_unsafe_security_issue(labels):
                    continue
                seen_ids.add(external_id)
                repo_name = str(item.get("repository_url") or "").removeprefix("https://api.github.com/repos/")
                tags = self._unique_tags(labels + [part for part in repo_name.split("/") if part] + ["bounty"])
                payout_estimate_usd, conversion_probability, risk_penalty_usd, build_minutes = self._bounty_estimates(
                    labels=labels,
                    title=str(item.get("title") or ""),
                    body=str(item.get("body") or ""),
                )
                opportunities.append(
                    RevenueOpportunity(
                        source="github_bounty",
                        external_id=external_id,
                        title=str(item.get("title") or ""),
                        url=str(item.get("html_url") or ""),
                        problem=str(item.get("body") or "")[:2000],
                        tags=tags,
                        channel="bounty_scanner",
                        payout_estimate_usd=payout_estimate_usd,
                        conversion_probability=conversion_probability,
                        estimated_cost_usd=3.0,
                        risk_penalty_usd=risk_penalty_usd,
                        build_minutes=build_minutes,
                    )
                )
                if len(opportunities) >= max_items:
                    return opportunities
        return opportunities

    def discover(self) -> list[RevenueOpportunity]:
        query_terms = ["supabase", "github actions", "fastapi", "openai api"]
        return self.search_help_wanted_issues(
            query_terms=query_terms,
            max_items=20,
        ) + self.search_bounty_issues(
            query_terms=query_terms,
            max_items=20,
        )

    @staticmethod
    def _is_unsafe_security_issue(labels: list[str]) -> bool:
        normalized = {label.lower() for label in labels}
        security_labels = {"security", "vulnerability", "cve"}
        safe_security_labels = {"documentation", "docs", "triage"}
        return bool(normalized & security_labels) and not bool(normalized & safe_security_labels)

    @staticmethod
    def _unique_tags(tags: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            normalized = tag.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        return unique

    @staticmethod
    def _bounty_estimates(
        *,
        labels: list[str],
        title: str,
        body: str,
    ) -> tuple[float, float, float, int]:
        searchable = " ".join(labels + [title, body]).lower()
        has_paid_signal = any(term in searchable for term in ("bounty", "paid", "reward", "sponsor"))
        is_docs_work = any(term in searchable for term in ("documentation", "docs", "readme", "guide"))
        is_good_first = "good first issue" in searchable
        has_safe_security_label = "security" in searchable and any(
            term in searchable for term in ("docs", "documentation", "triage")
        )

        if has_paid_signal:
            payout = 220.0
            conversion = 0.14
            build_minutes = 75
        elif is_docs_work or is_good_first:
            payout = 120.0
            conversion = 0.10
            build_minutes = 45
        else:
            payout = 90.0
            conversion = 0.08
            build_minutes = 60

        risk = 4.0 if has_safe_security_label else 1.5
        return payout, conversion, risk, build_minutes
