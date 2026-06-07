from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .offers import OfferDraft
from .revenue_scoring import RevenueOpportunity


def build_launch_sprint(
    *,
    opportunities: list[RevenueOpportunity],
    offers: list[OfferDraft],
    milestones: list[float],
    activation_report: dict | None = None,
) -> dict[str, Any]:
    normalized_milestones = sorted(float(milestone) for milestone in milestones)
    top_milestone = max(normalized_milestones) if normalized_milestones else 0.0
    blockers = _activation_blockers(activation_report)
    launch_tracks = [
        _launch_track(opportunity, offers, top_milestone)
        for opportunity in opportunities
    ]
    launch_tracks.sort(key=_launch_track_priority)
    payment_ready = bool(launch_tracks) and all(track["payment_configured"] for track in launch_tracks)
    activation_ready = bool(activation_report.get("ready")) if activation_report else not blockers
    automation_ready = activation_ready and payment_ready

    return {
        "automation_ready": automation_ready,
        "automation_answer": _automation_answer(automation_ready),
        "milestones": normalized_milestones,
        "top_milestone_usd": top_milestone,
        "activation_blockers": blockers,
        "launch_tracks": launch_tracks,
        "plan": _plan(blockers=blockers, launch_tracks=launch_tracks, top_milestone=top_milestone),
        "guardrails": [
            "No third-party autoposting, no mass outreach, and no payment links injected into other communities.",
            "Publish only on owned channels or places whose rules explicitly allow the post.",
            "Use manual review before public claims, checkout activation, or service delivery promises.",
            "Keep running after each milestone; $15, $200, $1,000, and $20,000 are checkpoints, not stop conditions.",
            "Revenue requires checkout, webhooks, owned publishing, traffic, and delivery; automation does not guarantee income.",
        ],
    }


class LaunchSprintExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(
        self,
        *,
        opportunities: list[RevenueOpportunity],
        offers: list[OfferDraft],
        milestones: list[float],
        activation_report: dict | None = None,
    ) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sprint = build_launch_sprint(
            opportunities=opportunities,
            offers=offers,
            milestones=milestones,
            activation_report=activation_report,
        )
        json_path = self.output_dir / "launch_sprint.json"
        markdown_path = self.output_dir / "30_DAY_LAUNCH_PLAN.md"
        json_path.write_text(json.dumps(sprint, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(_to_markdown(sprint), encoding="utf-8")
        return [json_path, markdown_path]


def _activation_blockers(report: dict | None) -> list[str]:
    if not report or report.get("ready"):
        return []
    return [str(action) for action in report.get("next_actions", []) if str(action).strip()]


def _launch_track(opportunity: RevenueOpportunity, offers: list[OfferDraft], top_milestone: float) -> dict[str, Any]:
    matching_offers = [
        offer for offer in offers
        if offer.source == opportunity.source and offer.external_id == opportunity.external_id
    ]
    best_offer = _best_offer(matching_offers, top_milestone)
    return {
        "source": opportunity.source,
        "external_id": opportunity.external_id,
        "title": opportunity.title,
        "channel": opportunity.channel,
        "expected_value_usd": round(float(opportunity.expected_value_usd), 2),
        "build_minutes": opportunity.build_minutes,
        "payment_configured": bool(best_offer and best_offer["payment_url"]),
        "best_offer": best_offer,
        "first_revenue_push": _first_revenue_push(opportunity.channel),
    }


def _launch_track_priority(track: dict[str, Any]) -> tuple[float, int, float, str]:
    best_offer = track.get("best_offer") or {}
    units = best_offer.get("units_to_top_milestone") or math.inf
    payment_penalty = 0 if track.get("payment_configured") else 1
    expected_value = float(track.get("expected_value_usd") or 0.0)
    return (float(units), payment_penalty, -expected_value, str(track.get("title") or ""))


def _best_offer(offers: list[OfferDraft], top_milestone: float) -> dict[str, Any] | None:
    if not offers:
        return None
    best = max(offers, key=lambda offer: (float(offer.price_usd), bool(offer.payment_url)))
    units = 0 if best.price_usd <= 0 else max(1, math.ceil(float(top_milestone) / float(best.price_usd)))
    return {
        "offer_key": best.offer_key,
        "offer_type": best.offer_type,
        "title": best.title,
        "price_usd": float(best.price_usd),
        "payment_url": best.payment_url,
        "payment_configured": bool(best.payment_url),
        "units_to_top_milestone": units,
    }


def _first_revenue_push(channel: str) -> list[str]:
    if channel == "microtool_seo":
        return [
            "Publish the owned microtool page with a support CTA and setup-service CTA.",
            "Add one practical example, one limitations section, and one intake path.",
        ]
    if channel == "paid_setup_kit":
        return [
            "Publish the fixed-scope service page with clear deliverables and acceptance criteria.",
            "Route checkout buyers to intake before work starts.",
        ]
    if channel == "digital_product":
        return [
            "Package the template files, publish the owned listing, and connect checkout metadata.",
            "Offer a small setup upsell for buyers who need implementation help.",
        ]
    if channel == "article_affiliate":
        return [
            "Publish the reviewed article on an owned site with affiliate disclosure.",
            "Verify pricing, screenshots, and terms before adding links.",
        ]
    if channel in {"github_issue_helper", "open_source_sponsorship"}:
        return [
            "Publish the useful owned repo or PR draft without payment links in third-party issues.",
            "Put sponsorship CTAs only in owned README, docs, or funding files.",
        ]
    return [
        "Publish the reviewed asset on an owned channel.",
        "Connect the matching checkout or support CTA before measuring conversions.",
    ]


def _plan(*, blockers: list[str], launch_tracks: list[dict[str, Any]], top_milestone: float) -> list[dict[str, Any]]:
    top_titles = [track["title"] for track in launch_tracks[:3]]
    first_title = top_titles[0] if top_titles else "the top selected opportunity"
    activation_actions = [
        "Run `python -m farm_loop.automation --json` and clear every activation blocker.",
        "Connect checkout URLs, conversion webhooks, click tracking, and the owned publishing URL.",
    ]
    activation_actions.extend(blockers[:5])

    return [
        {
            "phase": "activate",
            "window": "Days 1-2",
            "goal": "Make the engine capable of collecting and attributing real revenue.",
            "actions": activation_actions,
        },
        {
            "phase": "publish",
            "window": "Days 3-7",
            "goal": "Ship the first owned-channel assets instead of waiting on drafts.",
            "actions": [
                f"Publish `{first_title}` first, then the next highest expected-value tracks.",
                "Use the generated site, microtool, service package, product pack, or repo kit depending on the channel.",
                "Keep Stack Exchange and third-party communities as signal sources only unless their rules explicitly allow the post.",
            ],
        },
        {
            "phase": "first_sales",
            "window": "Week 2",
            "goal": "Push toward the first paid milestone while keeping offers deliverable.",
            "actions": [
                "Prioritize fixed-scope setup and premium service ladders over tiny tips.",
                "Record every confirmed payment in `conversion_events` or `tip_events` with the stable `offer_key`.",
                "Use the first conversion to improve the landing copy, pricing, and intake questions.",
            ],
        },
        {
            "phase": "measure",
            "window": "Week 3",
            "goal": "Find which loop has signal before scaling.",
            "actions": [
                "Review clicks, conversions, offer type, source, and revenue by channel in Supabase.",
                "Run the summarize phase daily and compare progress against every milestone.",
                "Revise high-click zero-sale offers before creating more similar assets.",
            ],
        },
        {
            "phase": "scale_or_prune",
            "window": "Week 4",
            "goal": f"Double down on paths that can plausibly compound toward {_money(top_milestone)}.",
            "actions": [
                "Run weekly pruning so stale loops pause and winners get cloned into more assets.",
                "Cap service delivery capacity before promoting high-ticket offers heavily.",
                "Keep generating new opportunities after each milestone instead of stopping at $15.",
            ],
        },
    ]


def _automation_answer(automation_ready: bool) -> str:
    if automation_ready:
        return (
            "Yes: discovery, scoring, asset generation, owned-site publishing artifacts, checkout CTAs, "
            "tracking, conversion logging, summaries, and pruning can run automatically. It still does not "
            "guarantee income; real revenue needs traffic, payment links, webhooks, and delivered value."
        )
    return (
        "Mostly yes, but not yet hands-off: discovery, scoring, asset generation, tracking, summaries, "
        "and pruning can run automatically after activation. It does not guarantee income until checkout, "
        "webhooks, owned publishing, traffic, and delivery are live."
    )


def _to_markdown(sprint: dict[str, Any]) -> str:
    lines = [
        "# 30 Day Launch Plan",
        "",
        sprint["automation_answer"],
        "",
        f"- Automation ready: {'yes' if sprint['automation_ready'] else 'no'}",
        f"- Top milestone: {_money(sprint['top_milestone_usd'])}",
        "",
    ]
    blockers = sprint.get("activation_blockers", [])
    if blockers:
        lines.extend(["## Activation Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in blockers)
        lines.append("")

    lines.extend(["## Launch Tracks", ""])
    for track in sprint["launch_tracks"]:
        best = track.get("best_offer") or {}
        lines.extend(
            [
                f"### {track['title']}",
                "",
                f"- Channel: {track['channel']}",
                f"- Expected value: {_money(track['expected_value_usd'])}",
                f"- Best offer: `{best.get('offer_type', 'none')}` at {_money(best.get('price_usd', 0))}",
                f"- Units to {_money(sprint['top_milestone_usd'])}: {best.get('units_to_top_milestone', 0)}",
                f"- Payment configured: {'yes' if track['payment_configured'] else 'no'}",
                "",
            ]
        )
        for action in track["first_revenue_push"]:
            lines.append(f"- {action}")
        lines.append("")

    lines.extend(["## Plan", ""])
    for phase in sprint["plan"]:
        lines.extend(
            [
                f"### {phase['window']}: {phase['phase']}",
                "",
                phase["goal"],
                "",
            ]
        )
        lines.extend(f"- {action}" for action in phase["actions"])
        lines.append("")

    lines.extend(["## Guardrails", ""])
    for guardrail in sprint["guardrails"]:
        lines.append(f"- {guardrail}")
    lines.append("")
    return "\n".join(lines)


def _money(value: float | int) -> str:
    amount = float(value)
    if amount.is_integer():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"
