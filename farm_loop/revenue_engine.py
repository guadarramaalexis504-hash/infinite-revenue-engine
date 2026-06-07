from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .assets import AssetDraft, AssetGenerator
from .launch_queue import LaunchTask, build_launch_queue
from .offers import OfferDraft, generate_offers
from .revenue_dashboard import build_dashboard_snapshot
from .revenue_pruning import build_prune_plan
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
    offers_created: int = 0
    offers_exported: int = 0
    checkout_setup_exported: int = 0
    tracking_deploy_exported: int = 0
    lead_magnets_exported: int = 0
    digital_products_exported: int = 0
    service_packages_exported: int = 0
    niche_reports_exported: int = 0
    affiliate_articles_exported: int = 0
    sponsor_repos_exported: int = 0
    roadmap_exported: int = 0
    activation_manifest_exported: int = 0
    revenue_forecast_exported: int = 0
    offer_ladder_exported: int = 0
    launch_sprint_exported: int = 0
    traffic_plan_exported: int = 0
    dashboard_snapshots_created: int = 0
    prune_decisions_created: int = 0
    experiments_updated: int = 0


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
    offer_exporter: Any | None = None,
    checkout_setup_exporter: Any | None = None,
    tracking_deploy_exporter: Any | None = None,
    lead_magnet_exporter: Any | None = None,
    digital_product_exporter: Any | None = None,
    service_package_exporter: Any | None = None,
    niche_report_exporter: Any | None = None,
    affiliate_article_exporter: Any | None = None,
    sponsor_repo_exporter: Any | None = None,
    roadmap_exporter: Any | None = None,
    activation_manifest_exporter: Any | None = None,
    revenue_forecast_exporter: Any | None = None,
    offer_ladder_exporter: Any | None = None,
    launch_sprint_exporter: Any | None = None,
    traffic_plan_exporter: Any | None = None,
    activation_report: dict | None = None,
    offer_payment_urls: dict[str, str] | None = None,
    site_base_url: str = "",
    click_redirect_url: str = "",
    lead_capture_url: str = "",
) -> RevenuePortfolioSummary:
    if phase == "summarize":
        dashboard_snapshots_created = 0
        if supabase and not dry_run:
            snapshot = build_dashboard_snapshot(
                conversions=supabase.list_conversion_events(),
                tips=supabase.list_tip_events(),
                assets=supabase.list_assets(),
                clicks=supabase.list_click_events(),
                offers=supabase.list_offers(),
                experiments=supabase.list_experiments(),
                milestones=milestones or DEFAULT_MILESTONES,
            )
            supabase.insert_portfolio_snapshot(snapshot)
            dashboard_snapshots_created = 1
            supabase.insert_event(None, "revenue_portfolio_summarized", snapshot)
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
            offers_created=0,
            offers_exported=0,
            roadmap_exported=0,
            dashboard_snapshots_created=dashboard_snapshots_created,
        )

    if phase == "prune":
        prune_decisions_created = 0
        experiments_updated = 0
        launch_tasks_created = 0
        if supabase and not dry_run:
            decisions = build_prune_plan(
                experiments=supabase.list_experiments(),
                offers=supabase.list_offers(),
                clicks=supabase.list_click_events(),
                conversions=supabase.list_conversion_events(),
            )
            prune_decisions_created = len(decisions)
            for decision in decisions:
                if decision.new_status:
                    supabase.update_experiment_status(
                        decision.experiment_id,
                        decision.new_status,
                        {
                            "prune_action": decision.action,
                            "prune_reason": decision.reason,
                        },
                    )
                    experiments_updated += 1
                if decision.launch_task:
                    supabase.insert_launch_task(decision.launch_task)
                    launch_tasks_created += 1
            supabase.insert_event(
                None,
                "revenue_portfolio_pruned",
                {
                    "phase": phase,
                    "decisions": [asdict(decision) for decision in decisions],
                    "prune_decisions_created": prune_decisions_created,
                    "experiments_updated": experiments_updated,
                    "launch_tasks_created": launch_tasks_created,
                },
            )
        return RevenuePortfolioSummary(
            status="success",
            discovered=0,
            selected=0,
            assets_created=0,
            assets_exported=0,
            site_pages_exported=0,
            launch_tasks_created=launch_tasks_created,
            launch_tasks_exported=0,
            microtools_exported=0,
            offers_created=0,
            offers_exported=0,
            roadmap_exported=0,
            prune_decisions_created=prune_decisions_created,
            experiments_updated=experiments_updated,
        )

    discovered: list[RevenueOpportunity] = []
    for source in sources:
        discovered.extend(source.discover())

    selected = rank_revenue_opportunities(discovered, max_items=max_opportunities)
    generator = AssetGenerator()
    assets_created = 0
    assets_exported = 0
    portfolio_assets: list[tuple[RevenueOpportunity, list[AssetDraft]]] = []
    offer_drafts: list[OfferDraft] = []
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

        offers = generate_offers(opportunity, payment_urls=offer_payment_urls)
        offer_drafts.extend(offers)
        if supabase and not dry_run:
            for offer in offers:
                supabase.insert_offer(offer.to_payload(opportunity_id))

    site_pages_exported = 0
    if site_exporter:
        site_pages_exported = len(site_exporter.export_portfolio(portfolio_assets))

    launch_tasks = build_launch_queue(portfolio_assets, activation_report=activation_report)
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

    offers_exported = 0
    if offer_exporter:
        offers_exported = len(offer_exporter.export(offer_drafts))

    checkout_setup_exported = 0
    if checkout_setup_exporter:
        checkout_setup_exported = len(checkout_setup_exporter.export(offer_drafts))

    tracking_deploy_exported = 0
    if tracking_deploy_exporter:
        tracking_deploy_exported = len(tracking_deploy_exporter.export())

    lead_magnets_exported = 0
    if lead_magnet_exporter:
        lead_magnets_exported = len(lead_magnet_exporter.export(selected))

    digital_products_exported = 0
    if digital_product_exporter:
        digital_products_exported = len(digital_product_exporter.export(selected))

    service_packages_exported = 0
    if service_package_exporter:
        service_packages_exported = len(service_package_exporter.export(selected))

    niche_reports_exported = 0
    if niche_report_exporter:
        niche_reports_exported = len(niche_report_exporter.export(selected))

    affiliate_articles_exported = 0
    if affiliate_article_exporter:
        affiliate_articles_exported = len(affiliate_article_exporter.export(selected))

    sponsor_repos_exported = 0
    if sponsor_repo_exporter:
        sponsor_repos_exported = len(sponsor_repo_exporter.export(selected))

    roadmap_exported = 0
    if roadmap_exporter:
        roadmap_exported = len(
            roadmap_exporter.export(
                discovered=discovered,
                selected=selected,
                milestones=milestones or DEFAULT_MILESTONES,
                activation_report=activation_report,
            )
        )

    activation_manifest_exported = 0
    if activation_manifest_exporter:
        activation_manifest_exported = len(
            activation_manifest_exporter.export(
                portfolio_assets,
                offers=offer_drafts,
                activation_report=activation_report,
            )
        )

    revenue_forecast_exported = 0
    if revenue_forecast_exporter:
        revenue_forecast_exported = len(
            revenue_forecast_exporter.export(
                offers=offer_drafts,
                milestones=milestones or DEFAULT_MILESTONES,
            )
        )

    offer_ladder_exported = 0
    if offer_ladder_exporter:
        offer_ladder_exported = len(
            offer_ladder_exporter.export(
                offers=offer_drafts,
                milestones=milestones or DEFAULT_MILESTONES,
            )
        )

    launch_sprint_exported = 0
    if launch_sprint_exporter:
        launch_sprint_exported = len(
            launch_sprint_exporter.export(
                opportunities=selected,
                offers=offer_drafts,
                milestones=milestones or DEFAULT_MILESTONES,
                activation_report=activation_report,
            )
        )

    traffic_plan_exported = 0
    if traffic_plan_exporter:
        traffic_plan_exported = len(
            traffic_plan_exporter.export(
                opportunities=selected,
                offers=offer_drafts,
                site_base_url=site_base_url,
                click_redirect_url=click_redirect_url,
                lead_capture_url=lead_capture_url,
            )
        )

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
                "offers_created": len(offer_drafts),
                "offers_exported": offers_exported,
                "checkout_setup_exported": checkout_setup_exported,
                "tracking_deploy_exported": tracking_deploy_exported,
                "lead_magnets_exported": lead_magnets_exported,
                "digital_products_exported": digital_products_exported,
                "service_packages_exported": service_packages_exported,
                "niche_reports_exported": niche_reports_exported,
                "affiliate_articles_exported": affiliate_articles_exported,
                "sponsor_repos_exported": sponsor_repos_exported,
                "roadmap_exported": roadmap_exported,
                "activation_manifest_exported": activation_manifest_exported,
                "revenue_forecast_exported": revenue_forecast_exported,
                "offer_ladder_exported": offer_ladder_exported,
                "launch_sprint_exported": launch_sprint_exported,
                "traffic_plan_exported": traffic_plan_exported,
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
        offers_created=len(offer_drafts),
        offers_exported=offers_exported,
        checkout_setup_exported=checkout_setup_exported,
        tracking_deploy_exported=tracking_deploy_exported,
        lead_magnets_exported=lead_magnets_exported,
        digital_products_exported=digital_products_exported,
        service_packages_exported=service_packages_exported,
        niche_reports_exported=niche_reports_exported,
        affiliate_articles_exported=affiliate_articles_exported,
        sponsor_repos_exported=sponsor_repos_exported,
        roadmap_exported=roadmap_exported,
        activation_manifest_exported=activation_manifest_exported,
        revenue_forecast_exported=revenue_forecast_exported,
        offer_ladder_exported=offer_ladder_exported,
        launch_sprint_exported=launch_sprint_exported,
        traffic_plan_exported=traffic_plan_exported,
    )


def _task_opportunity_id(task: LaunchTask, opportunity_ids: dict[tuple[str, str], str | None]) -> str | None:
    if not task.source or not task.external_id:
        return None
    return opportunity_ids.get((task.source, task.external_id))
