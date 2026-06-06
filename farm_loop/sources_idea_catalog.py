from __future__ import annotations

import json
from pathlib import Path

from .revenue_scoring import RevenueOpportunity


class IdeaCatalogSource:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def discover(self) -> list[RevenueOpportunity]:
        if not self.path.exists():
            return []
        ideas = json.loads(self.path.read_text(encoding="utf-8"))
        return [self._from_idea(idea) for idea in ideas]

    def _from_idea(self, idea: dict) -> RevenueOpportunity:
        tags = [str(tag) for tag in idea.get("tags") or []]
        external_id = str(idea["id"])
        return RevenueOpportunity(
            source="idea_catalog",
            external_id=external_id,
            title=str(idea.get("title") or external_id),
            url=f"file://{self.path.name}#{external_id}",
            problem=str(idea.get("problem") or ""),
            tags=tags,
            channel=str(idea.get("channel") or "microtool_seo"),
            payout_estimate_usd=float(idea.get("payout_estimate_usd") or 50),
            conversion_probability=float(idea.get("conversion_probability") or 0.03),
            estimated_cost_usd=float(idea.get("estimated_cost_usd") or 2),
            risk_penalty_usd=float(idea.get("risk_penalty_usd") or 1),
            build_minutes=int(float(idea.get("build_minutes") or 60)),
        )
