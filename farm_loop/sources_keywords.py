from __future__ import annotations

import csv
from pathlib import Path

from .revenue_scoring import RevenueOpportunity


class KeywordCSVSource:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[RevenueOpportunity]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8", newline="") as handle:
            return [self._from_row(row) for row in csv.DictReader(handle)]

    def discover(self) -> list[RevenueOpportunity]:
        return self.load()

    def _from_row(self, row: dict[str, str]) -> RevenueOpportunity:
        tags = [tag.strip() for tag in (row.get("tags") or "").split(";") if tag.strip()]
        external_id = row.get("id") or row.get("external_id") or row.get("title") or "keyword"
        return RevenueOpportunity(
            source="manual_keywords",
            external_id=external_id,
            title=row.get("title", ""),
            url=f"file://{self.path.name}#{external_id}",
            problem=row.get("problem", ""),
            tags=tags,
            channel=row.get("channel") or "microtool_seo",
            payout_estimate_usd=float(row.get("payout_estimate_usd") or 50),
            conversion_probability=float(row.get("conversion_probability") or 0.03),
            estimated_cost_usd=float(row.get("estimated_cost_usd") or 2),
            risk_penalty_usd=float(row.get("risk_penalty_usd") or 1),
            build_minutes=int(float(row.get("build_minutes") or 60)),
        )
