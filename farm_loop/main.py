from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .activation_manifest import ActivationManifestExporter
from .affiliate_article_exporter import AffiliateArticleExporter
from .all_ideas_catalog import AllIdeasCatalogExporter
from .asset_exporter import LocalAssetExporter
from .automation import collect_activation_report
from .checkout_setup import CheckoutSetupExporter
from .config import Settings
from .conversions import build_manual_conversion_payload
from .discord_notify import DiscordNotifier, build_conversion_message
from .digital_product_exporter import DigitalProductExporter
from .drafts import DraftGenerator
from .launch_queue import LaunchQueueExporter
from .launch_sprint import LaunchSprintExporter
from .lead_magnet_exporter import LeadMagnetExporter
from .microtool_exporter import MicrotoolExporter
from .niche_report_exporter import NicheReportExporter
from .offer_ladder import OfferLadderExporter
from .offers import OfferCatalogExporter, parse_offer_payment_urls
from .opportunity_roadmap import OpportunityRoadmapExporter
from .scoring import rank_questions, to_opportunity_payload
from .service_package_exporter import ServicePackageExporter
from .sources_stackexchange import StackExchangeClient
from .supabase_client import SupabaseClient
from .revenue_engine import run_revenue_portfolio_once
from .revenue_forecast import RevenueForecastExporter
from .sources_github import GitHubIssuesClient
from .sources_idea_catalog import IdeaCatalogSource
from .sources_keywords import KeywordCSVSource
from .sponsor_repo_exporter import SponsorRepoExporter
from .static_site_exporter import StaticSiteExporter
from .tracking_deploy import TrackingDeployExporter
from .traffic_plan import TrafficPlanExporter


LOGGER = logging.getLogger("farm_loop")


@dataclass(frozen=True)
class RunSummary:
    status: str
    scanned_questions: int
    opportunities: int
    generated_drafts: int
    total_tips_usd: float


def _event(supabase: Any | None, run_id: str | None, event_type: str, payload: dict, dry_run: bool) -> None:
    LOGGER.info("%s %s", event_type, json.dumps(payload, sort_keys=True))
    if dry_run or not supabase:
        return
    supabase.insert_event(run_id, event_type, payload)


def _opportunity_id(rows: Any) -> str | None:
    if isinstance(rows, list) and rows:
        return rows[0].get("id")
    if isinstance(rows, dict):
        return rows.get("id")
    return None


def run_once(
    *,
    source_client: Any,
    supabase: Any | None,
    draft_generator: Any | None,
    tip_url: str,
    max_drafts: int = 3,
    target_usd: float = 15.0,
    dry_run: bool = False,
    force_drafts: bool = False,
    stop_after_target: bool = False,
) -> RunSummary:
    run_id = None if dry_run or not supabase else supabase.create_run()
    generated_drafts = 0
    opportunities_count = 0
    scanned_questions = 0
    status = "success"

    try:
        _event(supabase, run_id, "run_started", {"dry_run": dry_run}, dry_run)
        total_tips = 0.0 if dry_run or not supabase else supabase.total_tips_usd()
        if total_tips >= target_usd:
            _event(
                supabase,
                run_id,
                "target_reached",
                {"total_tips_usd": total_tips, "target_usd": target_usd},
                dry_run,
            )
            if stop_after_target and not force_drafts:
                status = "monitoring"
                if supabase and not dry_run:
                    supabase.finish_run(run_id, status, None)
                return RunSummary(status, 0, 0, 0, total_tips)

        result = source_client.search_unanswered(page_size=20)
        scanned_questions = len(result.questions)
        _event(
            supabase,
            run_id,
            "source_scanned",
            {
                "source": "stackexchange",
                "questions": scanned_questions,
                "quota_remaining": result.quota_remaining,
            },
            dry_run,
        )
        if result.backoff_seconds:
            _event(
                supabase,
                run_id,
                "stackexchange_backoff",
                {"backoff_seconds": result.backoff_seconds},
                dry_run,
            )

        ranked = rank_questions(result.questions, max_items=max_drafts, min_score=50)
        opportunities_count = len(ranked)
        for question in ranked:
            opportunity_payload = to_opportunity_payload(question, score=question.get("farm_score"))
            if dry_run or not supabase:
                LOGGER.info("dry_run_opportunity %s", json.dumps(opportunity_payload, sort_keys=True))
                continue

            opportunity_rows = supabase.upsert_opportunity(opportunity_payload)
            opportunity_id = _opportunity_id(opportunity_rows)
            if not opportunity_id:
                raise RuntimeError("Supabase opportunity upsert did not return an id")
            if not draft_generator:
                raise RuntimeError("Draft generator is required when dry_run is false")

            draft = draft_generator.generate(question, tip_url=tip_url)
            supabase.insert_draft(
                {
                    "opportunity_id": opportunity_id,
                    "answer_markdown": draft.answer_markdown,
                    "code_snippet": draft.code_snippet,
                    "status": "draft",
                }
            )
            generated_drafts += 1
            _event(
                supabase,
                run_id,
                "draft_created",
                {"opportunity_id": opportunity_id, "external_id": opportunity_payload["external_id"]},
                dry_run,
            )

        if supabase and not dry_run:
            supabase.finish_run(run_id, status, None)
        return RunSummary(status, scanned_questions, opportunities_count, generated_drafts, total_tips)
    except Exception as exc:
        status = "error"
        LOGGER.exception("run_failed")
        try:
            _event(supabase, run_id, "run_error", {"error": str(exc)}, dry_run)
            if supabase and not dry_run:
                supabase.finish_run(run_id, status, str(exc))
        finally:
            pass
        raise


def build_runtime(settings: Settings, *, dry_run: bool) -> tuple[StackExchangeClient, SupabaseClient | None, DraftGenerator | None]:
    settings.require_runtime_secrets(dry_run)
    source = StackExchangeClient(key=settings.stackexchange_key, tags=settings.tags)
    supabase = None
    draft_generator = None
    if not dry_run:
        supabase = SupabaseClient(settings.supabase_url or "", settings.supabase_key or "")
        draft_generator = DraftGenerator(settings.openai_api_key or "", model=settings.openai_model)
    return source, supabase, draft_generator


def run_loop(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    source, supabase, draft_generator = build_runtime(settings, dry_run=args.dry_run)
    while True:
        try:
            summary = run_once(
                source_client=source,
                supabase=supabase,
                draft_generator=draft_generator,
                tip_url=settings.tip_url,
                max_drafts=settings.max_drafts,
                target_usd=settings.target_usd,
                dry_run=args.dry_run,
                force_drafts=args.force_drafts,
                stop_after_target=args.stop_after_target or settings.stop_after_target,
            )
            LOGGER.info("run_summary %s", json.dumps(asdict(summary), sort_keys=True))
        except Exception as exc:
            LOGGER.error("loop_iteration_failed: %s", exc)
        time.sleep(args.interval_seconds)


def run_single(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    source, supabase, draft_generator = build_runtime(settings, dry_run=args.dry_run)
    summary = run_once(
        source_client=source,
        supabase=supabase,
        draft_generator=draft_generator,
        tip_url=settings.tip_url,
        max_drafts=settings.max_drafts,
        target_usd=settings.target_usd,
        dry_run=args.dry_run,
        force_drafts=args.force_drafts,
        stop_after_target=args.stop_after_target or settings.stop_after_target,
    )
    LOGGER.info("run_summary %s", json.dumps(asdict(summary), sort_keys=True))
    return 0


def run_portfolio_single(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    supabase = None
    if not args.dry_run:
        settings.require_runtime_secrets(False)
        supabase = SupabaseClient(settings.supabase_url or "", settings.supabase_key or "")

    sources = [
        GitHubIssuesClient(token=settings.github_token),
        KeywordCSVSource(settings.keyword_csv_path),
        IdeaCatalogSource(settings.idea_catalog_path),
    ]
    cli_bundle_paths = bundle_output_paths(args.bundle_output_dir) if args.bundle_output_dir else {}
    env_bundle_paths = bundle_output_paths(settings.bundle_output_dir) if settings.bundle_output_dir else {}
    asset_output_dir = (
        args.asset_output_dir
        or cli_bundle_paths.get("asset_output_dir")
        or settings.asset_output_dir
        or env_bundle_paths.get("asset_output_dir")
    )
    asset_exporter = LocalAssetExporter(asset_output_dir) if asset_output_dir else None
    site_output_dir = (
        args.site_output_dir
        or cli_bundle_paths.get("site_output_dir")
        or settings.site_output_dir
        or env_bundle_paths.get("site_output_dir")
    )
    site_base_url = args.site_base_url or settings.site_base_url or ""
    click_redirect_url = args.click_redirect_url or settings.click_redirect_url or ""
    intake_url = args.intake_url or settings.service_intake_url or ""
    offer_payment_urls = parse_offer_payment_urls(args.offer_payment_urls or settings.offer_payment_urls)
    microtool_output_dir = (
        args.microtool_output_dir
        or cli_bundle_paths.get("microtool_output_dir")
        or settings.microtool_output_dir
        or env_bundle_paths.get("microtool_output_dir")
    )
    tools_path = tools_path_for_site(site_output_dir, microtool_output_dir) if site_output_dir and microtool_output_dir else ""
    site_exporter = (
        StaticSiteExporter(
            site_output_dir,
            tip_url=settings.tip_url,
            click_redirect_url=click_redirect_url,
            intake_url=intake_url,
            tools_path=tools_path,
            site_base_url=site_base_url,
            offer_payment_urls=offer_payment_urls,
        )
        if site_output_dir
        else None
    )
    launch_queue_output_dir = (
        args.launch_queue_output_dir
        or cli_bundle_paths.get("launch_queue_output_dir")
        or settings.launch_queue_output_dir
        or env_bundle_paths.get("launch_queue_output_dir")
    )
    launch_queue_exporter = LaunchQueueExporter(launch_queue_output_dir) if launch_queue_output_dir else None
    activation_report = collect_activation_report() if launch_queue_exporter else None
    microtool_exporter = MicrotoolExporter(microtool_output_dir, tip_url=settings.tip_url) if microtool_output_dir else None
    offer_output_dir = (
        args.offer_output_dir
        or cli_bundle_paths.get("offer_output_dir")
        or settings.offer_output_dir
        or env_bundle_paths.get("offer_output_dir")
    )
    offer_exporter = OfferCatalogExporter(offer_output_dir) if offer_output_dir else None
    checkout_setup_output_dir = (
        args.checkout_setup_output_dir
        or cli_bundle_paths.get("checkout_setup_output_dir")
        or settings.checkout_setup_output_dir
        or env_bundle_paths.get("checkout_setup_output_dir")
    )
    conversion_webhook_base_url = args.conversion_webhook_base_url or settings.conversion_webhook_base_url or ""
    checkout_setup_exporter = (
        CheckoutSetupExporter(
            checkout_setup_output_dir,
            conversion_webhook_base_url=conversion_webhook_base_url,
            click_redirect_url=click_redirect_url,
        )
        if checkout_setup_output_dir
        else None
    )
    tracking_deploy_output_dir = (
        args.tracking_deploy_output_dir
        or cli_bundle_paths.get("tracking_deploy_output_dir")
        or settings.tracking_deploy_output_dir
        or env_bundle_paths.get("tracking_deploy_output_dir")
    )
    tracking_public_base_url = args.tracking_public_base_url or settings.tracking_public_base_url or ""
    tracking_deploy_exporter = (
        TrackingDeployExporter(tracking_deploy_output_dir, public_base_url=tracking_public_base_url)
        if tracking_deploy_output_dir
        else None
    )
    lead_magnet_output_dir = (
        args.lead_magnet_output_dir
        or cli_bundle_paths.get("lead_magnet_output_dir")
        or settings.lead_magnet_output_dir
        or env_bundle_paths.get("lead_magnet_output_dir")
    )
    lead_capture_url = args.lead_capture_url or settings.lead_capture_url or ""
    lead_magnet_exporter = (
        LeadMagnetExporter(
            lead_magnet_output_dir,
            lead_capture_url=lead_capture_url,
            click_redirect_url=click_redirect_url,
        )
        if lead_magnet_output_dir
        else None
    )
    digital_product_output_dir = (
        args.digital_product_output_dir
        or cli_bundle_paths.get("digital_product_output_dir")
        or settings.digital_product_output_dir
        or env_bundle_paths.get("digital_product_output_dir")
    )
    digital_product_exporter = (
        DigitalProductExporter(
            digital_product_output_dir,
            payment_urls=offer_payment_urls,
            click_redirect_url=click_redirect_url,
        )
        if digital_product_output_dir
        else None
    )
    service_package_output_dir = (
        args.service_package_output_dir
        or cli_bundle_paths.get("service_package_output_dir")
        or settings.service_package_output_dir
        or env_bundle_paths.get("service_package_output_dir")
    )
    service_package_exporter = (
        ServicePackageExporter(
            service_package_output_dir,
            payment_urls=offer_payment_urls,
            intake_url=intake_url,
            click_redirect_url=click_redirect_url,
        )
        if service_package_output_dir
        else None
    )
    niche_report_output_dir = (
        args.niche_report_output_dir
        or cli_bundle_paths.get("niche_report_output_dir")
        or settings.niche_report_output_dir
        or env_bundle_paths.get("niche_report_output_dir")
    )
    niche_report_exporter = (
        NicheReportExporter(
            niche_report_output_dir,
            payment_urls=offer_payment_urls,
            click_redirect_url=click_redirect_url,
        )
        if niche_report_output_dir
        else None
    )
    affiliate_article_output_dir = (
        args.affiliate_article_output_dir
        or cli_bundle_paths.get("affiliate_article_output_dir")
        or settings.affiliate_article_output_dir
        or env_bundle_paths.get("affiliate_article_output_dir")
    )
    affiliate_urls = parse_offer_payment_urls(args.affiliate_urls or settings.affiliate_urls)
    affiliate_article_exporter = (
        AffiliateArticleExporter(
            affiliate_article_output_dir,
            affiliate_urls=affiliate_urls,
            click_redirect_url=click_redirect_url,
        )
        if affiliate_article_output_dir
        else None
    )
    sponsor_repo_output_dir = (
        args.sponsor_repo_output_dir
        or cli_bundle_paths.get("sponsor_repo_output_dir")
        or settings.sponsor_repo_output_dir
        or env_bundle_paths.get("sponsor_repo_output_dir")
    )
    sponsor_urls = parse_offer_payment_urls(args.sponsor_urls or settings.sponsor_urls)
    sponsor_repo_exporter = (
        SponsorRepoExporter(
            sponsor_repo_output_dir,
            sponsor_urls=sponsor_urls,
            click_redirect_url=click_redirect_url,
        )
        if sponsor_repo_output_dir
        else None
    )
    roadmap_output_dir = (
        args.roadmap_output_dir
        or cli_bundle_paths.get("roadmap_output_dir")
        or settings.roadmap_output_dir
        or env_bundle_paths.get("roadmap_output_dir")
    )
    roadmap_exporter = OpportunityRoadmapExporter(roadmap_output_dir) if roadmap_output_dir else None
    if roadmap_exporter and not activation_report:
        activation_report = collect_activation_report()
    activation_manifest_output_dir = (
        args.activation_manifest_output_dir
        or cli_bundle_paths.get("activation_manifest_output_dir")
        or settings.activation_manifest_output_dir
        or env_bundle_paths.get("activation_manifest_output_dir")
    )
    artifact_dirs = {
        "asset_output_dir": asset_output_dir or "",
        "site_output_dir": site_output_dir or "",
        "microtool_output_dir": microtool_output_dir or "",
        "offer_output_dir": offer_output_dir or "",
        "checkout_setup_output_dir": checkout_setup_output_dir or "",
        "tracking_deploy_output_dir": tracking_deploy_output_dir or "",
        "lead_magnet_output_dir": lead_magnet_output_dir or "",
        "digital_product_output_dir": digital_product_output_dir or "",
        "service_package_output_dir": service_package_output_dir or "",
        "niche_report_output_dir": niche_report_output_dir or "",
        "affiliate_article_output_dir": affiliate_article_output_dir or "",
        "sponsor_repo_output_dir": sponsor_repo_output_dir or "",
        "roadmap_output_dir": roadmap_output_dir or "",
        "launch_queue_output_dir": launch_queue_output_dir or "",
        "launch_sprint_output_dir": (
            args.launch_sprint_output_dir
            or cli_bundle_paths.get("launch_sprint_output_dir")
            or settings.launch_sprint_output_dir
            or env_bundle_paths.get("launch_sprint_output_dir")
            or ""
        ),
        "traffic_plan_output_dir": (
            args.traffic_plan_output_dir
            or cli_bundle_paths.get("traffic_plan_output_dir")
            or settings.traffic_plan_output_dir
            or env_bundle_paths.get("traffic_plan_output_dir")
            or ""
        ),
        "all_ideas_output_dir": (
            args.all_ideas_output_dir
            or cli_bundle_paths.get("all_ideas_output_dir")
            or settings.all_ideas_output_dir
            or env_bundle_paths.get("all_ideas_output_dir")
            or ""
        ),
    }
    activation_manifest_exporter = (
        ActivationManifestExporter(
            activation_manifest_output_dir,
            artifact_dirs=artifact_dirs,
            repo_root=Path.cwd(),
        )
        if activation_manifest_output_dir
        else None
    )
    if activation_manifest_exporter and not activation_report:
        activation_report = collect_activation_report()
    revenue_forecast_output_dir = (
        args.revenue_forecast_output_dir
        or cli_bundle_paths.get("revenue_forecast_output_dir")
        or settings.revenue_forecast_output_dir
        or env_bundle_paths.get("revenue_forecast_output_dir")
    )
    revenue_forecast_exporter = (
        RevenueForecastExporter(revenue_forecast_output_dir)
        if revenue_forecast_output_dir
        else None
    )
    offer_ladder_output_dir = (
        args.offer_ladder_output_dir
        or cli_bundle_paths.get("offer_ladder_output_dir")
        or settings.offer_ladder_output_dir
        or env_bundle_paths.get("offer_ladder_output_dir")
    )
    offer_ladder_exporter = (
        OfferLadderExporter(offer_ladder_output_dir)
        if offer_ladder_output_dir
        else None
    )
    launch_sprint_output_dir = (
        args.launch_sprint_output_dir
        or cli_bundle_paths.get("launch_sprint_output_dir")
        or settings.launch_sprint_output_dir
        or env_bundle_paths.get("launch_sprint_output_dir")
    )
    launch_sprint_exporter = (
        LaunchSprintExporter(launch_sprint_output_dir)
        if launch_sprint_output_dir
        else None
    )
    if launch_sprint_exporter and not activation_report:
        activation_report = collect_activation_report()
    traffic_plan_output_dir = (
        args.traffic_plan_output_dir
        or cli_bundle_paths.get("traffic_plan_output_dir")
        or settings.traffic_plan_output_dir
        or env_bundle_paths.get("traffic_plan_output_dir")
    )
    traffic_plan_exporter = (
        TrafficPlanExporter(traffic_plan_output_dir)
        if traffic_plan_output_dir
        else None
    )
    all_ideas_output_dir = (
        args.all_ideas_output_dir
        or cli_bundle_paths.get("all_ideas_output_dir")
        or settings.all_ideas_output_dir
        or env_bundle_paths.get("all_ideas_output_dir")
    )
    all_ideas_exporter = (
        AllIdeasCatalogExporter(all_ideas_output_dir)
        if all_ideas_output_dir
        else None
    )
    summary = run_revenue_portfolio_once(
        sources=sources,
        supabase=supabase,
        max_opportunities=args.max_opportunities,
        milestones=settings.revenue_milestones or [15, 200, 1000, 20000],
        dry_run=args.dry_run,
        phase=args.portfolio_phase,
        asset_exporter=asset_exporter,
        site_exporter=site_exporter,
        launch_queue_exporter=launch_queue_exporter,
        microtool_exporter=microtool_exporter,
        offer_exporter=offer_exporter,
        checkout_setup_exporter=checkout_setup_exporter,
        tracking_deploy_exporter=tracking_deploy_exporter,
        lead_magnet_exporter=lead_magnet_exporter,
        digital_product_exporter=digital_product_exporter,
        service_package_exporter=service_package_exporter,
        niche_report_exporter=niche_report_exporter,
        affiliate_article_exporter=affiliate_article_exporter,
        sponsor_repo_exporter=sponsor_repo_exporter,
        roadmap_exporter=roadmap_exporter,
        activation_manifest_exporter=activation_manifest_exporter,
        revenue_forecast_exporter=revenue_forecast_exporter,
        offer_ladder_exporter=offer_ladder_exporter,
        launch_sprint_exporter=launch_sprint_exporter,
        traffic_plan_exporter=traffic_plan_exporter,
        all_ideas_exporter=all_ideas_exporter,
        activation_report=activation_report,
        offer_payment_urls=offer_payment_urls,
        site_base_url=site_base_url,
        click_redirect_url=click_redirect_url,
        lead_capture_url=lead_capture_url,
        notifier=DiscordNotifier(settings.discord_webhook_url),
    )
    LOGGER.info("portfolio_summary %s", json.dumps(asdict(summary), sort_keys=True))
    return 0


def run_record_conversion(args: argparse.Namespace) -> int:
    payload_json = _parse_json_object(args.conversion_payload_json)
    conversion_payload = build_manual_conversion_payload(
        provider=args.conversion_provider,
        external_id=args.conversion_external_id or "",
        amount_usd=args.conversion_amount_usd,
        source=args.conversion_source,
        offer_id=args.conversion_offer_id,
        offer_key=args.conversion_offer_key,
        payload=payload_json,
    )
    if args.dry_run:
        LOGGER.info("dry_run_conversion %s", json.dumps(conversion_payload, sort_keys=True))
        return 0

    settings = Settings.from_env()
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_KEY")
    supabase = SupabaseClient(settings.supabase_url, settings.supabase_key)
    rows = supabase.insert_conversion_event(conversion_payload)
    supabase.insert_event(
        None,
        "conversion_recorded",
        {
            "source": conversion_payload["source"],
            "external_id": conversion_payload["external_id"],
            "amount_usd": conversion_payload["amount_usd"],
        },
    )
    LOGGER.info("conversion_recorded %s", json.dumps({"rows": rows}, sort_keys=True))
    notifier = DiscordNotifier(settings.discord_webhook_url)
    if notifier.enabled:
        notifier.send(
            build_conversion_message(
                amount_usd=float(conversion_payload.get("amount_usd") or 0),
                source=str(conversion_payload.get("source") or "unknown"),
                offer_key=str((conversion_payload.get("payload") or {}).get("offer_key") or "") or None,
            )
        )
    return 0


def run_create_stripe_links(args: argparse.Namespace) -> int:
    from types import SimpleNamespace

    from .stripe_links import StripeLinkBuilder, build_offer_payment_urls_string

    settings = Settings.from_env()
    builder = StripeLinkBuilder(settings.stripe_secret_key)
    if not builder.enabled:
        LOGGER.error("STRIPE_SECRET_KEY missing or placeholder; set it before creating links.")
        return 1
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_KEY")

    supabase = SupabaseClient(settings.supabase_url, settings.supabase_key)
    rows = supabase.list_offers_for_checkout()
    offers = []
    id_by_offer_key: dict[str, str] = {}
    for row in rows if isinstance(rows, list) else []:
        payload = row.get("payload") or {}
        offer_key = payload.get("offer_key") or ""
        if not offer_key or row.get("payment_url"):
            continue  # skip already-linked offers
        id_by_offer_key.setdefault(offer_key, str(row.get("id")))
        offers.append(
            SimpleNamespace(
                offer_type=payload.get("offer_type", ""),
                price_usd=float(row.get("price_usd") or 0),
                offer_key=offer_key,
                title=row.get("title", ""),
                channel=row.get("channel", ""),
                source=payload.get("source", ""),
                external_id=payload.get("external_id", ""),
            )
        )

    links = builder.create_for_offers(offers)
    for offer_key, url in links.items():
        offer_id = id_by_offer_key.get(offer_key)
        if offer_id:
            try:
                supabase.update_offer_payment_url(offer_id, url)
            except Exception as exc:  # noqa: BLE001
                LOGGER.error("could not update offer %s: %s", offer_id, exc)

    payment_urls_string = build_offer_payment_urls_string(links)
    LOGGER.info("stripe_links_created %s", json.dumps({"count": len(links)}, sort_keys=True))
    LOGGER.info("OFFER_PAYMENT_URLS=%s", payment_urls_string)

    notifier = DiscordNotifier(settings.discord_webhook_url)
    if notifier.enabled and links:
        notifier.send(
            f"**💳 {len(links)} Stripe Payment Links creados** y guardados en las ofertas. "
            "El checkout real ya esta vivo.",
            username="Revenue Engine",
        )
    return 0


def _parse_json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("--conversion-payload-json must decode to a JSON object")
    return parsed


def tools_path_for_site(site_output_dir: str | None, microtool_output_dir: str | None) -> str:
    if not site_output_dir or not microtool_output_dir:
        return ""
    site_path = Path(site_output_dir)
    tools_path = Path(microtool_output_dir)
    try:
        relative = tools_path.relative_to(site_path)
    except ValueError:
        return ""
    relative_url = relative.as_posix().strip("/")
    return f"{relative_url}/" if relative_url else ""


def bundle_output_paths(bundle_output_dir: str) -> dict[str, str]:
    base_path = Path(bundle_output_dir)
    site_path = base_path / "site"
    return {
        "asset_output_dir": (base_path / "assets").as_posix(),
        "site_output_dir": site_path.as_posix(),
        "microtool_output_dir": (site_path / "tools").as_posix(),
        "offer_output_dir": (base_path / "offers").as_posix(),
        "checkout_setup_output_dir": (base_path / "checkout-setup").as_posix(),
        "tracking_deploy_output_dir": (base_path / "tracking-deploy").as_posix(),
        "lead_magnet_output_dir": (base_path / "lead-magnets").as_posix(),
        "digital_product_output_dir": (base_path / "digital-products").as_posix(),
        "service_package_output_dir": (base_path / "service-packages").as_posix(),
        "niche_report_output_dir": (base_path / "niche-reports").as_posix(),
        "affiliate_article_output_dir": (base_path / "affiliate-articles").as_posix(),
        "sponsor_repo_output_dir": (base_path / "sponsor-repos").as_posix(),
        "roadmap_output_dir": (base_path / "roadmap").as_posix(),
        "activation_manifest_output_dir": (base_path / "activation").as_posix(),
        "revenue_forecast_output_dir": (base_path / "revenue-forecast").as_posix(),
        "offer_ladder_output_dir": (base_path / "offer-ladder").as_posix(),
        "launch_queue_output_dir": (base_path / "launch-queue").as_posix(),
        "launch_sprint_output_dir": (base_path / "launch-sprint").as_posix(),
        "traffic_plan_output_dir": (base_path / "traffic-plan").as_posix(),
        "all_ideas_output_dir": (base_path / "all-ideas").as_posix(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe review-first technical answer opportunity loop.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one cycle and exit.")
    mode.add_argument("--loop", action="store_true", help="Run continuously.")
    mode.add_argument("--portfolio-once", action="store_true", help="Run one revenue portfolio cycle and exit.")
    mode.add_argument("--record-conversion", action="store_true", help="Record one confirmed conversion and exit.")
    mode.add_argument("--create-stripe-links", action="store_true", help="Create Stripe Payment Links for paid offers in Supabase and write them back.")
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true", help="Avoid Supabase writes and OpenAI draft generation.")
    parser.add_argument("--force-drafts", action="store_true", help="Generate drafts even after TARGET_USD is reached.")
    parser.add_argument("--stop-after-target", action="store_true", help="Pause draft generation once TARGET_USD is reached.")
    parser.add_argument(
        "--portfolio-phase",
        choices=["discover", "generate", "summarize", "prune"],
        default="discover",
        help="Portfolio phase label for scheduled workflows.",
    )
    parser.add_argument("--max-opportunities", type=int, default=10)
    parser.add_argument(
        "--asset-output-dir",
        default=None,
        help="Write generated portfolio assets to a local manual-review directory.",
    )
    parser.add_argument(
        "--site-output-dir",
        default=None,
        help="Write an owned static site for generated portfolio opportunities.",
    )
    parser.add_argument(
        "--site-base-url",
        default=None,
        help="Optional public base URL for sitemap.xml and robots.txt.",
    )
    parser.add_argument(
        "--click-redirect-url",
        default=None,
        help="Optional owned click redirect endpoint used for support CTAs.",
    )
    parser.add_argument(
        "--intake-url",
        default=None,
        help="Optional owned setup intake form URL used for service CTAs.",
    )
    parser.add_argument(
        "--launch-queue-output-dir",
        default=None,
        help="Write a prioritized launch task queue to JSON and Markdown files.",
    )
    parser.add_argument(
        "--microtool-output-dir",
        default=None,
        help="Write supported interactive microtools as static HTML pages.",
    )
    parser.add_argument(
        "--offer-output-dir",
        default=None,
        help="Write monetizable offer drafts to JSON and Markdown files.",
    )
    parser.add_argument(
        "--offer-payment-urls",
        default=None,
        help="Comma-separated offer_type=url or channel=url checkout links used in generated offer CTAs.",
    )
    parser.add_argument(
        "--checkout-setup-output-dir",
        default=None,
        help="Write checkout metadata and webhook setup instructions for generated offers.",
    )
    parser.add_argument(
        "--conversion-webhook-base-url",
        default=None,
        help="Public base URL for conversion webhooks, e.g. https://host/webhooks/conversion.",
    )
    parser.add_argument(
        "--tracking-deploy-output-dir",
        default=None,
        help="Write Docker-based deployment files for the server-side tracking/webhook app.",
    )
    parser.add_argument(
        "--tracking-public-base-url",
        default=None,
        help="Public HTTPS base URL for the deployed tracking app, e.g. https://track.example.com.",
    )
    parser.add_argument(
        "--lead-magnet-output-dir",
        default=None,
        help="Write lead magnet landing pages, checklists, and opt-in metadata.",
    )
    parser.add_argument(
        "--lead-capture-url",
        default=None,
        help="Owned opt-in form or newsletter URL used by generated lead magnet CTAs.",
    )
    parser.add_argument(
        "--digital-product-output-dir",
        default=None,
        help="Write product packs, store listings, and launch checklists for digital product opportunities.",
    )
    parser.add_argument(
        "--service-package-output-dir",
        default=None,
        help="Write fixed-scope service packages, proposals, scopes, delivery checklists, and handoff docs.",
    )
    parser.add_argument(
        "--niche-report-output-dir",
        default=None,
        help="Write paid niche report drafts, validation plans, store listings, and landing pages.",
    )
    parser.add_argument(
        "--affiliate-article-output-dir",
        default=None,
        help="Write disclosed affiliate article drafts, outlines, and landing pages.",
    )
    parser.add_argument(
        "--affiliate-urls",
        default=None,
        help="Comma-separated tag=url or *=url affiliate links used in generated affiliate articles.",
    )
    parser.add_argument(
        "--sponsor-repo-output-dir",
        default=None,
        help="Write GitHub Sponsors-ready open-source repo kits for owned repositories.",
    )
    parser.add_argument(
        "--sponsor-urls",
        default=None,
        help="Comma-separated tag=url, github=url, sponsorship=url, or *=url sponsor links for repo kits.",
    )
    parser.add_argument(
        "--roadmap-output-dir",
        default=None,
        help="Write a ranked opportunity roadmap for all discovered ideas.",
    )
    parser.add_argument(
        "--activation-manifest-output-dir",
        default=None,
        help="Write an activation manifest with exact artifact paths and validation commands.",
    )
    parser.add_argument(
        "--revenue-forecast-output-dir",
        default=None,
        help="Write offer-level unit targets for each revenue milestone.",
    )
    parser.add_argument(
        "--offer-ladder-output-dir",
        default=None,
        help="Write higher-ticket offer ladder paths for each revenue milestone.",
    )
    parser.add_argument(
        "--launch-sprint-output-dir",
        default=None,
        help="Write a 30-day launch plan that turns generated assets into owned-channel revenue tests.",
    )
    parser.add_argument(
        "--traffic-plan-output-dir",
        default=None,
        help="Write allowed traffic and distribution plans for generated revenue assets.",
    )
    parser.add_argument(
        "--all-ideas-output-dir",
        default=None,
        help="Write a complete ranked catalog of all discovered revenue ideas.",
    )
    parser.add_argument(
        "--bundle-output-dir",
        default=None,
        help="Write all reviewable revenue outputs into one standard bundle directory.",
    )
    parser.add_argument("--conversion-provider", default="manual", help="Payment provider, e.g. manual, stripe, gumroad.")
    parser.add_argument("--conversion-external-id", default=None, help="Provider sale/event id used for dedupe.")
    parser.add_argument("--conversion-amount-usd", type=float, default=0.0, help="Confirmed conversion amount in USD.")
    parser.add_argument("--conversion-source", default="manual", help="Revenue source/channel attribution.")
    parser.add_argument("--conversion-offer-id", default=None, help="Optional Supabase offers.id attribution.")
    parser.add_argument("--conversion-offer-key", default=None, help="Optional deterministic offer key attribution.")
    parser.add_argument("--conversion-payload-json", default="{}", help="Optional JSON payload to store with the conversion.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
        if args.record_conversion:
            return run_record_conversion(args)
        if args.create_stripe_links:
            return run_create_stripe_links(args)
        if args.portfolio_once:
            return run_portfolio_single(args)
        if args.loop:
            return run_loop(args)
        return run_single(args)
    except Exception as exc:
        LOGGER.error("fatal: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
