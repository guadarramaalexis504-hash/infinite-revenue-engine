from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from .revenue_scoring import RevenueOpportunity, rank_revenue_opportunities, score_opportunity


def build_all_ideas_catalog(
    *,
    ideas: list[RevenueOpportunity],
    selected_external_ids: set[str] | None = None,
    milestones: list[float],
) -> dict[str, Any]:
    selected_ids = selected_external_ids or set()
    normalized_milestones = sorted(float(milestone) for milestone in milestones)
    ranked = rank_revenue_opportunities(ideas, max_items=max(len(ideas), 1))
    rows = [_idea_row(idea, selected_ids, normalized_milestones) for idea in ranked]
    return {
        "total_ideas": len(rows),
        "milestones": normalized_milestones,
        "channel_summary": _channel_summary(ranked),
        "ideas": rows,
        "guardrails": [
            "No third-party autoposting, no mass outreach, and no payment links injected into communities.",
            "Use third-party sites as discovery signals unless their rules explicitly allow the post.",
            "Publish on owned site, owned repository, owned store, newsletter, or approved partner channel first.",
            "Keep generating and pruning after each milestone; $20,000 is a checkpoint, not a stop condition.",
        ],
    }


class AllIdeasCatalogExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(
        self,
        *,
        ideas: list[RevenueOpportunity],
        selected_external_ids: set[str],
        milestones: list[float],
    ) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        catalog = build_all_ideas_catalog(
            ideas=ideas,
            selected_external_ids=selected_external_ids,
            milestones=milestones,
        )
        json_path = self.output_dir / "all_revenue_ideas.json"
        markdown_path = self.output_dir / "ALL_REVENUE_IDEAS.md"
        json_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(_to_markdown(catalog), encoding="utf-8")
        return [json_path, markdown_path]


def _idea_row(idea: RevenueOpportunity, selected_ids: set[str], milestones: list[float]) -> dict[str, Any]:
    scored = score_opportunity(idea)
    plan = _channel_plan(scored.channel)
    return {
        "source": scored.source,
        "external_id": scored.external_id,
        "title": scored.title,
        "channel": scored.channel,
        "problem": scored.problem,
        "tags": scored.tags,
        "expected_value_usd": scored.expected_value_usd,
        "payout_estimate_usd": scored.payout_estimate_usd,
        "conversion_probability": scored.conversion_probability,
        "build_minutes": scored.build_minutes,
        "selected_this_run": scored.external_id in selected_ids,
        "first_asset": plan["first_asset"],
        "monetization_path": plan["monetization_path"],
        "allowed_distribution": plan["allowed_distribution"],
        "unit_targets": {
            _milestone_key(milestone): _units_needed(milestone, scored.payout_estimate_usd)
            for milestone in milestones
        },
        "url": scored.url,
    }


def _channel_summary(ideas: list[RevenueOpportunity]) -> list[dict[str, Any]]:
    grouped: dict[str, list[RevenueOpportunity]] = defaultdict(list)
    for idea in ideas:
        grouped[idea.channel].append(score_opportunity(idea))

    rows: list[dict[str, Any]] = []
    for channel, channel_ideas in grouped.items():
        top = max(channel_ideas, key=lambda idea: idea.expected_value_usd)
        rows.append(
            {
                "channel": channel,
                "count": len(channel_ideas),
                "total_expected_value_usd": round(sum(idea.expected_value_usd for idea in channel_ideas), 2),
                "average_build_minutes": round(sum(idea.build_minutes for idea in channel_ideas) / len(channel_ideas)),
                "top_external_id": top.external_id,
                "top_title": top.title,
            }
        )
    rows.sort(key=lambda row: (row["total_expected_value_usd"], -row["average_build_minutes"]), reverse=True)
    return rows


def _channel_plan(channel: str) -> dict[str, str]:
    plans = {
        "microtool_seo": {
            "first_asset": "Owned static microtool page",
            "monetization_path": "support CTA, setup service, and template upsell",
            "allowed_distribution": "owned site, search index, newsletter, owned repo",
        },
        "paid_setup_kit": {
            "first_asset": "Fixed-scope service page and intake form",
            "monetization_path": "fixed-scope service package with bounded delivery",
            "allowed_distribution": "owned site, intake form, newsletter, case study",
        },
        "digital_product": {
            "first_asset": "Downloadable template pack and store listing",
            "monetization_path": "digital product plus setup-service upsell",
            "allowed_distribution": "owned store, owned site, opt-in newsletter",
        },
        "article_affiliate": {
            "first_asset": "Reviewed affiliate article with disclosure",
            "monetization_path": "affiliate commission and related paid template",
            "allowed_distribution": "owned site, search index, newsletter",
        },
        "lead_magnet": {
            "first_asset": "Free checklist or calculator landing page",
            "monetization_path": "email opt-in to paid setup, template, or report",
            "allowed_distribution": "owned site, newsletter, approved partner mentions",
        },
        "open_source_sponsorship": {
            "first_asset": "Owned repository kit with README and funding file",
            "monetization_path": "GitHub Sponsors and paid support",
            "allowed_distribution": "owned repo, docs, newsletter",
        },
        "github_issue_helper": {
            "first_asset": "Patch plan or owned helper repo",
            "monetization_path": "sponsorship, consulting, and fixed-scope support",
            "allowed_distribution": "owned repo and useful PRs without payment links",
        },
        "niche_report": {
            "first_asset": "Paid mini-report draft and landing page",
            "monetization_path": "paid report, lead capture, and consulting upsell",
            "allowed_distribution": "owned site, owned store, newsletter",
        },
        "bounty_scanner": {
            "first_asset": "Bounty qualification brief",
            "monetization_path": "allowed public bounty payout or owned service follow-up",
            "allowed_distribution": "bounty platform rules, owned notes, no spam",
        },
    }
    return plans.get(
        channel,
        {
            "first_asset": "Owned review asset",
            "monetization_path": "support, service, product, or sponsorship path",
            "allowed_distribution": "owned channels or explicitly permitted communities",
        },
    )


def _units_needed(milestone: float, payout_estimate_usd: float) -> int:
    payout = max(float(payout_estimate_usd), 1.0)
    return max(1, math.ceil(float(milestone) / payout))


def _to_markdown(catalog: dict[str, Any]) -> str:
    lines = [
        "# All Revenue Ideas",
        "",
        f"- Total ideas: {catalog['total_ideas']}",
        f"- Top milestone: {_money(max(catalog['milestones']) if catalog['milestones'] else 0)}",
        "",
        "## Channel Summary",
        "",
        "| Channel | Ideas | Expected value | Avg build minutes | Top idea |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for channel in catalog["channel_summary"]:
        lines.append(
            f"| {channel['channel']} | {channel['count']} | "
            f"{_money(channel['total_expected_value_usd'])} | "
            f"{channel['average_build_minutes']} | {channel['top_title']} |"
        )

    lines.extend(["", "## Ideas", ""])
    for idea in catalog["ideas"]:
        marker = "selected this run" if idea["selected_this_run"] else "backlog"
        top_key = _milestone_key(max(catalog["milestones"]) if catalog["milestones"] else 0)
        lines.extend(
            [
                f"### {idea['title']}",
                "",
                f"- Status: {marker}",
                f"- Channel: {idea['channel']}",
                f"- Expected value: {_money(idea['expected_value_usd'])}",
                f"- Payout estimate: {_money(idea['payout_estimate_usd'])}",
                f"- Units to {_money(float(top_key or 0))}: {idea['unit_targets'].get(top_key, 0)}",
                f"- First asset: {idea['first_asset']}",
                f"- Monetization: {idea['monetization_path']}",
                f"- Allowed distribution: {idea['allowed_distribution']}",
                f"- Problem: {idea['problem']}",
                "",
            ]
        )

    lines.extend(["## Guardrails", ""])
    lines.extend(f"- {guardrail}" for guardrail in catalog["guardrails"])
    lines.append("")
    return "\n".join(lines)


def _milestone_key(value: float) -> str:
    amount = float(value)
    if amount.is_integer():
        return str(int(amount))
    return str(amount)


def _money(value: float | int) -> str:
    amount = float(value)
    if amount.is_integer():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"
