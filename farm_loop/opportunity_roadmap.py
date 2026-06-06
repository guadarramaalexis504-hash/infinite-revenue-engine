from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from .revenue_scoring import RevenueOpportunity, rank_revenue_opportunities


def build_opportunity_roadmap(
    *,
    discovered: list[RevenueOpportunity],
    selected: list[RevenueOpportunity],
    milestones: list[float],
    activation_report: dict | None = None,
) -> dict[str, Any]:
    ranked = rank_revenue_opportunities(discovered, max_items=max(len(discovered), 1))
    selected_ids = {opportunity.external_id for opportunity in selected}
    blockers = _activation_blockers(activation_report)
    channel_summary = _channel_summary(ranked)
    recommended_channel = channel_summary[0]["channel"] if channel_summary else "none"
    top_opportunity = ranked[0] if ranked else None

    return {
        "total_discovered": len(discovered),
        "total_ranked": len(ranked),
        "selected_external_ids": [opportunity.external_id for opportunity in selected],
        "activation_blockers": blockers,
        "recommended_channel": recommended_channel,
        "recommended_next_actions": _recommended_next_actions(blockers, top_opportunity, recommended_channel),
        "channel_summary": channel_summary,
        "milestone_plan": _milestone_plan(milestones, top_opportunity, recommended_channel),
        "backlog": [_opportunity_row(opportunity, selected_ids) for opportunity in ranked],
    }


class OpportunityRoadmapExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(
        self,
        *,
        discovered: list[RevenueOpportunity],
        selected: list[RevenueOpportunity],
        milestones: list[float],
        activation_report: dict | None,
    ) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        roadmap = build_opportunity_roadmap(
            discovered=discovered,
            selected=selected,
            milestones=milestones,
            activation_report=activation_report,
        )
        json_path = self.output_dir / "opportunity_roadmap.json"
        markdown_path = self.output_dir / "OPPORTUNITY_ROADMAP.md"
        json_path.write_text(json.dumps(roadmap, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path.write_text(_to_markdown(roadmap), encoding="utf-8")
        return [json_path, markdown_path]


def _activation_blockers(report: dict | None) -> list[str]:
    if not report or report.get("ready"):
        return []
    return [str(action) for action in report.get("next_actions", []) if str(action).strip()]


def _channel_summary(ranked: list[RevenueOpportunity]) -> list[dict[str, Any]]:
    by_channel: dict[str, list[RevenueOpportunity]] = defaultdict(list)
    for opportunity in ranked:
        by_channel[opportunity.channel].append(opportunity)

    rows: list[dict[str, Any]] = []
    for channel, opportunities in by_channel.items():
        expected_value = round(sum(opportunity.expected_value_usd for opportunity in opportunities), 2)
        build_minutes = round(sum(opportunity.build_minutes for opportunity in opportunities) / len(opportunities))
        top = max(opportunities, key=lambda opportunity: opportunity.expected_value_usd)
        rows.append(
            {
                "channel": channel,
                "count": len(opportunities),
                "total_expected_value_usd": expected_value,
                "average_build_minutes": build_minutes,
                "top_external_id": top.external_id,
                "top_title": top.title,
            }
        )
    rows.sort(key=lambda row: (row["total_expected_value_usd"], -row["average_build_minutes"]), reverse=True)
    return rows


def _milestone_plan(
    milestones: list[float],
    top_opportunity: RevenueOpportunity | None,
    recommended_channel: str,
) -> list[dict[str, Any]]:
    if not top_opportunity:
        return []
    unit_value = max(top_opportunity.payout_estimate_usd, 1.0)
    return [
        {
            "milestone_usd": float(milestone),
            "recommended_channel": recommended_channel,
            "anchor_opportunity": top_opportunity.external_id,
            "required_units_estimate": max(1, math.ceil(float(milestone) / unit_value)),
            "note": f"Use {recommended_channel} as the first compounding lane, then reinvest winners into more assets.",
        }
        for milestone in sorted(milestones)
    ]


def _recommended_next_actions(
    blockers: list[str],
    top_opportunity: RevenueOpportunity | None,
    recommended_channel: str,
) -> list[str]:
    actions: list[str] = []
    if blockers:
        actions.append("Fix activation blockers before expecting live revenue: " + "; ".join(blockers[:3]))
    if top_opportunity:
        actions.append(f"Start with {top_opportunity.title} in {recommended_channel}.")
        actions.append("Publish one owned page, connect one payment CTA, then measure clicks and confirmed revenue.")
    else:
        actions.append("Add more opportunity sources or catalog ideas before generating assets.")
    return actions


def _opportunity_row(opportunity: RevenueOpportunity, selected_ids: set[str]) -> dict[str, Any]:
    return {
        "source": opportunity.source,
        "external_id": opportunity.external_id,
        "title": opportunity.title,
        "channel": opportunity.channel,
        "expected_value_usd": opportunity.expected_value_usd,
        "payout_estimate_usd": opportunity.payout_estimate_usd,
        "conversion_probability": opportunity.conversion_probability,
        "build_minutes": opportunity.build_minutes,
        "selected_this_run": opportunity.external_id in selected_ids,
        "url": opportunity.url,
    }


def _to_markdown(roadmap: dict[str, Any]) -> str:
    lines = [
        "# Opportunity Roadmap",
        "",
        f"- Total discovered: {roadmap['total_discovered']}",
        f"- Total ranked: {roadmap['total_ranked']}",
        f"- Recommended channel: {roadmap['recommended_channel']}",
        "",
    ]
    blockers = roadmap.get("activation_blockers") or []
    if blockers:
        lines.extend(["## Activation Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in blockers)
        lines.append("")

    lines.extend(["## Recommended Next Actions", ""])
    lines.extend(f"- {action}" for action in roadmap.get("recommended_next_actions") or [])
    lines.append("")

    lines.extend(["## Channel Summary", "", "| Channel | Ideas | Expected value | Avg build | Top idea |", "| --- | ---: | ---: | ---: | --- |"])
    for row in roadmap.get("channel_summary") or []:
        lines.append(
            f"| {row['channel']} | {row['count']} | {_money(row['total_expected_value_usd'])} | "
            f"{row['average_build_minutes']} min | {row['top_title']} |"
        )
    lines.append("")

    lines.extend(["## Milestone Plan", "", "| Milestone | Channel | Anchor | Units estimate |", "| ---: | --- | --- | ---: |"])
    for row in roadmap.get("milestone_plan") or []:
        lines.append(
            f"| {_money(row['milestone_usd'])} | {row['recommended_channel']} | "
            f"{row['anchor_opportunity']} | {row['required_units_estimate']} |"
        )
    lines.append("")

    lines.extend(
        [
            "## All Ranked Ideas",
            "",
            "| Rank | Selected | Channel | Expected value | Payout | Build | Title |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for index, row in enumerate(roadmap.get("backlog") or [], start=1):
        selected = "yes" if row["selected_this_run"] else "no"
        lines.append(
            f"| {index} | {selected} | {row['channel']} | {_money(row['expected_value_usd'])} | "
            f"{_money(row['payout_estimate_usd'])} | {row['build_minutes']} min | {row['title']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _money(value: float) -> str:
    amount = float(value)
    if amount.is_integer():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"
