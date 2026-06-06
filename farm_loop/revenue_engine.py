from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .assets import AssetDraft, AssetGenerator
from .launch_queue import LaunchTask, build_launch_queue
from .revenue_scoring import RevenueOpportunity, rank_revenue_opportunities


DEFAULT_MILESTONES = [15, 200, 1000, 20000]


@dataclass(frozen=True)
class RevenuePortfolioSummary:
    status: str
    discovered: int
    selected: int
    assets_created: int
    assets_exported: int = 0
    site_pages_exported: int = 0
    launch_tasks_created: int = 0
    launch_tasks_exported: int = 0
    microtools_exported: int = 0


def run_revenue_portfolio_once(
    *,
    sources: list[Any],
    supabase: Any | None,
    max_opportunities: int = 10,
    milestones: list[float] | None = None,
    dry_run: bool = False,
    phase: str = "discover",
    asset_exporter: Any | None = None,
    site_exporter: Any | None = None,
    launch_queue_exporter: Any | None = None,
    microtool_exporter: Any | None = None,
) -> RevenuePortfolioSummary:
    if phase in {"summarize", "prune"}:
        if supabase and not dry_run:
            supabase.insert_event(None, f"revenue_portfolio_{phase}", {"phase": phase})
        return RevenuePortfolioSummary(
            status="success",
            discovered=0,
            selected=0,
            assets_created=0,
            assets_exported=0,
            site_pages_exported=0,
            launch_tasks_created=0,
            launch_tasks_exported=0,
            microtools_exported=0,
        )

    discovered: list[RevenueOpportunity] = []
    for source in sources:
        discovered.extend(source.discover())

    selected = rank_revenue_opportunities(discovered, max_items=max_opportunities)
    generator = AssetGenerator()
    assets_created = 0
    assets_exported = 0
    portfolio_assets: list[tuple[RevenueOpportunity, list[AssetDraft]]] = []
    opportunity_ids: dict[tuple[str, str], str | None] = {}

    for opportunity in selected:
        opportunity_id = None
        if supabase and not dry_run:
            rows = supabase.upsert_revenue_opportunity(opportunity.to_payload())
            if isinstance(rows, list) and rows:
                opportunity_id = rows[0].get("id")
        opportunity_ids[(opportunity.source, opportunity.external_id)] = opportunity_id

        assets = generator.generate_all(opportunity)
        for asset in assets:
            if supabase and not dry_run:
                supabase.insert_asset(asset.to_payload(opportunity_id, opportunity))
            assets_created += 1
        if asset_exporter:
            asset_exporter.export_opportunity(opportunity, assets)
            assets_exported += len(assets)
        portfolio_assets.append((opportunity, assets))

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

    site_pages_exported = 0
    if site_exporter:
        site_pages_exported = len(site_exporter.export_portfolio(portfolio_assets))

    launch_tasks = build_launch_queue(portfolio_assets)
    launch_tasks_created = len(launch_tasks)
    launch_tasks_exported = 0
    if supabase and not dry_run:
        for task in launch_tasks:
            supabase.insert_launch_task(task.to_payload(_task_opportunity_id(task, opportunity_ids)))
    if launch_queue_exporter:
        launch_tasks_exported = len(launch_queue_exporter.export(launch_tasks))

    microtools_exported = 0
    if microtool_exporter:
        microtools_exported = len(microtool_exporter.export_portfolio(portfolio_assets))

    if supabase and not dry_run:
        supabase.insert_event(
            None,
            "revenue_portfolio_cycle",
            {
                "discovered": len(discovered),
                "selected": len(selected),
                "assets_created": assets_created,
                "assets_exported": assets_exported,
                "site_pages_exported": site_pages_exported,
                "launch_tasks_created": launch_tasks_created,
                "launch_tasks_exported": launch_tasks_exported,
                "microtools_exported": microtools_exported,
                "milestones": milestones or DEFAULT_MILESTONES,
                "phase": phase,
            },
        )

    return RevenuePortfolioSummary(
        status="success",
        discovered=len(discovered),
        selected=len(selected),
        assets_created=assets_created,
        assets_exported=assets_exported,
        site_pages_exported=site_pages_exported,
        launch_tasks_created=launch_tasks_created,
        launch_tasks_exported=launch_tasks_exported,
        microtools_exported=microtools_exported,
    )


def _task_opportunity_id(task: LaunchTask, opportunity_ids: dict[tuple[str, str], str | None]) -> str | None:
    if not task.source or not task.external_id:
        return None
    return opportunity_ids.get((task.source, task.external_id))
