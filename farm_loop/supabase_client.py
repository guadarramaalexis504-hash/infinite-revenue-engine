from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests


RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class SupabaseClient:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        *,
        session: Any | None = None,
        timeout: int = 15,
        max_retries: int = 3,
    ) -> None:
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self, prefer: str = "return=representation") -> dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": prefer,
        }

    def _url(self, path: str) -> str:
        return f"{self.supabase_url}/rest/v1/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        prefer: str = "return=representation",
    ) -> Any:
        url = self._url(path)
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    headers=self._headers(prefer),
                    json=json_body,
                    timeout=self.timeout,
                )
                if response.status_code in RETRY_STATUS_CODES and attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                if response.status_code >= 400:
                    raise RuntimeError(f"Supabase {method} {url} failed: {response.status_code} {response.text}")
                return response.json()
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.max_retries - 1:
                    break
                time.sleep(2**attempt)
        raise RuntimeError(f"Supabase {method} {url} failed after retries: {last_error}")

    def create_run(self) -> str | None:
        rows = self.request(
            "POST",
            "runs",
            json_body={
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "running",
            },
        )
        if isinstance(rows, list) and rows:
            return rows[0].get("id")
        return None

    def finish_run(self, run_id: str | None, status: str, error: str | None = None) -> None:
        if not run_id:
            return
        path = f"runs?id=eq.{quote(str(run_id), safe='')}"
        self.request(
            "PATCH",
            path,
            json_body={
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "error": error,
            },
            prefer="return=minimal",
        )

    def insert_event(self, run_id: str | None, event_type: str, payload: dict) -> Any:
        return self.request(
            "POST",
            "events",
            json_body={"run_id": run_id, "event_type": event_type, "payload": payload},
        )

    def upsert_opportunity(self, payload: dict) -> Any:
        return self.request(
            "POST",
            "opportunities?on_conflict=source,external_id",
            json_body=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def upsert_revenue_opportunity(self, payload: dict) -> Any:
        return self.upsert_opportunity(payload)

    def insert_draft(self, payload: dict) -> Any:
        return self.request("POST", "drafts", json_body=payload)

    def insert_asset(self, payload: dict) -> Any:
        return self.request("POST", "assets", json_body=payload)

    def insert_offer(self, payload: dict) -> Any:
        return self.request("POST", "offers", json_body=payload)

    def insert_experiment(self, payload: dict) -> Any:
        return self.request("POST", "experiments", json_body=payload)

    def insert_conversion_event(self, payload: dict) -> Any:
        return self.request("POST", "conversion_events", json_body=payload)

    def insert_click_event(self, payload: dict) -> Any:
        return self.request("POST", "click_events", json_body=payload)

    def insert_launch_task(self, payload: dict) -> Any:
        return self.request("POST", "launch_tasks", json_body=payload)

    def insert_tip_event(self, payload: dict) -> Any:
        return self.request("POST", "tip_events", json_body=payload)

    def total_tips_usd(self) -> float:
        rows = self.request("GET", "tip_events?select=amount_usd", prefer="return=representation")
        total = 0.0
        for row in rows or []:
            try:
                total += float(row.get("amount_usd") or 0)
            except (TypeError, ValueError):
                continue
        return total

    def total_revenue_usd(self) -> float:
        tips = self.total_tips_usd()
        rows = self.request("GET", "conversion_events?select=amount_usd", prefer="return=representation")
        conversions = 0.0
        for row in rows or []:
            try:
                conversions += float(row.get("amount_usd") or 0)
            except (TypeError, ValueError):
                continue
        return round(tips + conversions, 2)
