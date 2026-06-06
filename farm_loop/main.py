from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

from .asset_exporter import LocalAssetExporter
from .config import Settings
from .drafts import DraftGenerator
from .scoring import rank_questions, to_opportunity_payload
from .sources_stackexchange import StackExchangeClient
from .supabase_client import SupabaseClient
from .revenue_engine import run_revenue_portfolio_once
from .sources_github import GitHubIssuesClient
from .sources_idea_catalog import IdeaCatalogSource
from .sources_keywords import KeywordCSVSource
from .static_site_exporter import StaticSiteExporter


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
    asset_output_dir = args.asset_output_dir or settings.asset_output_dir
    asset_exporter = LocalAssetExporter(asset_output_dir) if asset_output_dir else None
    site_output_dir = args.site_output_dir or settings.site_output_dir
    click_redirect_url = args.click_redirect_url or settings.click_redirect_url or ""
    site_exporter = (
        StaticSiteExporter(site_output_dir, tip_url=settings.tip_url, click_redirect_url=click_redirect_url)
        if site_output_dir
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
    )
    LOGGER.info("portfolio_summary %s", json.dumps(asdict(summary), sort_keys=True))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe review-first technical answer opportunity loop.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one cycle and exit.")
    mode.add_argument("--loop", action="store_true", help="Run continuously.")
    mode.add_argument("--portfolio-once", action="store_true", help="Run one revenue portfolio cycle and exit.")
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
        "--click-redirect-url",
        default=None,
        help="Optional owned click redirect endpoint used for support CTAs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    try:
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
