from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .assets import AssetDraft
from .revenue_scoring import RevenueOpportunity


@dataclass(frozen=True)
class LaunchTask:
    priority: int
    category: str
    title: str
    detail: str
    status: str = "pending"
    blocking: bool = False
    source: str | None = None
    external_id: str | None = None
    channel: str | None = None
    expected_value_usd: float = 0.0

    def to_payload(self, opportunity_id: str | None = None) -> dict:
        payload = asdict(self)
        payload["opportunity_id"] = opportunity_id
        payload["payload"] = {
            "source": self.source,
            "external_id": self.external_id,
            "channel": self.channel,
            "expected_value_usd": self.expected_value_usd,
        }
        return payload


def build_launch_queue(
    opportunities_with_assets: list[tuple[RevenueOpportunity, list[AssetDraft]]],
    *,
    activation_report: dict | None = None,
) -> list[LaunchTask]:
    tasks: list[LaunchTask] = []
    for index, action in enumerate(_activation_actions(activation_report), start=1):
        tasks.append(
            LaunchTask(
                priority=10 + index,
                category="activation",
                title=action,
                detail="This blocks live automation or tracking. Fix it before expecting real revenue.",
                status="blocked",
                blocking=True,
            )
        )

    for index, (opportunity, assets) in enumerate(opportunities_with_assets, start=1):
        base_priority = 40 + (index * 10)
        tasks.extend(_opportunity_tasks(opportunity, assets, base_priority))

    return sorted(tasks, key=lambda task: (task.priority, task.category, task.title))


class LaunchQueueExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(self, tasks: list[LaunchTask]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / "launch_queue.json"
        markdown_path = self.output_dir / "LAUNCH_QUEUE.md"
        json_path.write_text(
            json.dumps([asdict(task) for task in tasks], indent=2, sort_keys=True),
            encoding="utf-8",
        )
        markdown_path.write_text(_to_markdown(tasks), encoding="utf-8")
        return [json_path, markdown_path]


def _activation_actions(report: dict | None) -> list[str]:
    if not report or report.get("ready"):
        return []
    return [str(action) for action in report.get("next_actions", []) if str(action).strip()]


def _opportunity_tasks(
    opportunity: RevenueOpportunity,
    assets: list[AssetDraft],
    base_priority: int,
) -> list[LaunchTask]:
    asset_types = ", ".join(asset.asset_type for asset in assets) or "generated assets"
    publish_detail = _publish_detail(opportunity)
    common = {
        "source": opportunity.source,
        "external_id": opportunity.external_id,
        "channel": opportunity.channel,
        "expected_value_usd": round(opportunity.expected_value_usd, 2),
    }
    return [
        LaunchTask(
            priority=base_priority,
            category="review",
            title=f"Review assets for {opportunity.title}",
            detail=f"Check accuracy, usefulness, and safety for: {asset_types}.",
            **common,
        ),
        LaunchTask(
            priority=base_priority + 1,
            category="publish",
            title=f"Publish owned page for {opportunity.title}",
            detail=publish_detail,
            **common,
        ),
        LaunchTask(
            priority=base_priority + 2,
            category="monetize",
            title=f"Connect payment/support CTA for {opportunity.title}",
            detail="Use TIP_URL, Stripe, Gumroad, Lemon Squeezy, or GitHub Sponsors. Keep the CTA on owned or explicitly permitted channels.",
            **common,
        ),
        LaunchTask(
            priority=base_priority + 3,
            category="measure",
            title=f"Measure clicks and conversions for {opportunity.title}",
            detail="Verify UTM tags, click_events, conversion_events, and confirmed revenue attribution before scaling this loop.",
            **common,
        ),
    ]


def _publish_detail(opportunity: RevenueOpportunity) -> str:
    if opportunity.source.lower() in {"stackexchange", "stackoverflow"} or opportunity.channel.lower() in {
        "stackexchange",
        "stackoverflow",
    }:
        return (
            "Publish only on an owned page, owned repo, newsletter, or store. "
            "Do not publish AI-generated answers back to Stack Overflow or Stack Exchange."
        )
    if opportunity.channel == "github_issue_helper":
        return "Prepare a human-reviewed patch, docs update, or repo example. Do not spam maintainers or add payment links to issues."
    if opportunity.channel == "microtool_seo":
        return "Ship a small owned SEO page or repo demo with a useful working tool and clear support CTA."
    if opportunity.channel == "paid_setup_kit":
        return "Create a fixed-scope service page with deliverables, price, payment link, and intake form."
    return "Publish on an owned or explicitly permitted channel with manual review and attribution tracking."


def _to_markdown(tasks: list[LaunchTask]) -> str:
    lines = ["# Launch Queue", ""]
    for task in tasks:
        marker = "BLOCKED" if task.blocking else task.status.upper()
        lines.extend(
            [
                f"## P{task.priority} - {task.title}",
                "",
                f"- Status: {marker}",
                f"- Category: {task.category}",
                f"- Channel: {task.channel or 'global'}",
                f"- External ID: {task.external_id or 'n/a'}",
                f"- Expected value: ${task.expected_value_usd:.2f}",
                f"- Detail: {task.detail}",
                "",
            ]
        )
    return "\n".join(lines)
