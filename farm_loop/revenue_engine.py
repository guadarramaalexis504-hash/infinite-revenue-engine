from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .assets import AssetGenerator
from .revenue_scoring import RevenueOpportunity, rank_revenue_opportunities


DEFAULT_MILESTONES = [15, 200, 1000, 20000]


@dataclass(frozen=True)
class RevenuePortfolioSummary:
    status: str
    discovered: int
    selected: int
    assets_created: int


def run_revenue_portfolio_once(
    *,
    sources: list[Any],
    supabase: Any | None,
    max_opportunities: int = 10,
    milestones: list[float] | None = None,
    dry_run: bool = False,
    phase: str = "discover",
) -> RevenuePortfolioSummary:
    if phase in {"summarize", "prune"}:
        if supabase and not dry_run:
            supabase.insert_event(None, f"revenue_portfolio_{phase}", {"phase": phase})
        return RevenuePortfolioSummary(status="success", discovered=0, selected=0, assets_created=0)

    discovered: list[RevenueOpportunity] = []
    for source in sources:
        discovered.extend(source.discover())

    selected = rank_revenue_opportunities(discovered, max_items=max_opportunities)
    generator = AssetGenerator()
    assets_created = 0

    for opportunity in selected:
        opportunity_id = None
        if supabase and not dry_run:
            rows = supabase.upsert_revenue_opportunity(opportunity.to_payload())
            if isinstance(rows, list) and rows:
                opportunity_id = rows[0].get("id")

        assets = generator.generate_all(opportunity)
        for asset in assets:
            if supabase and not dry_run:
                supabase.insert_asset(asset.to_payload(opportunity_id, opportunity))
            assets_created += 1

        if supabase and not dry_run:
            supabase.insert_experiment(
                {
                    "opportunity_id": opportunity_id,
                    "name": f"{opportunity.channel}:{opportunity.external_id}",
                    "status": "planned",
                    "hypothesis": f"{opportunity.title} can produce revenue through {opportunity.channel}.",
                    "payload": asdict(opportunity),
                }
            )

    if supabase and not dry_run:
        supabase.insert_event(
            None,
            "revenue_portfolio_cycle",
            {
                "discovered": len(discovered),
                "selected": len(selected),
                "assets_created": assets_created,
                "milestones": milestones or DEFAULT_MILESTONES,
                "phase": phase,
            },
        )

    return RevenuePortfolioSummary(
        status="success",
        discovered=len(discovered),
        selected=len(selected),
        assets_created=assets_created,
    )
