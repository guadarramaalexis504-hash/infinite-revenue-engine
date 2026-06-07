from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .offers import OfferDraft
from .revenue_scoring import RevenueOpportunity


def build_traffic_plan(
    *,
    opportunities: list[RevenueOpportunity],
    offers: list[OfferDraft],
    site_base_url: str = "",
    click_redirect_url: str = "",
    lead_capture_url: str = "",
) -> dict[str, Any]:
    required_setup = _required_setup(site_base_url=site_base_url, offers=offers)
    tracks = [_track(opportunity, offers) for opportunity in opportunities]
    tracks.sort(key=_track_priority)
    return {
        "traffic_ready": not required_setup,
        "summary": {
            "tracks": len(tracks),
            "site_base_url_configured": bool(site_base_url),
            "click_redirect_configured": bool(click_redirect_url),
            "lead_capture_configured": bool(lead_capture_url),
            "payment_configured_tracks": sum(1 for track in tracks if track["payment_configured"]),
        },
        "required_setup": required_setup,
        "metrics": [
            "click_events by source, external_id, offer_key, and surface",
            "conversion_events revenue by offer_key and source channel",
            "portfolio_snapshots milestone progress",
            "experiments that receive clicks but no confirmed revenue",
        ],
        "guardrails": [
            "No third-party autoposting, no mass outreach, and no payment links injected into communities.",
            "Use Stack Exchange, GitHub issues, and forums as signal sources unless their rules explicitly permit posting.",
            "Publish public assets only on owned channels or channels where the user has reviewed the rules.",
            "Add affiliate disclosure before publishing comparison or recommendation content.",
            "Stop scaling any channel that gets clicks without confirmed revenue until the offer is revised.",
        ],
        "tracks": tracks,
        "weekly_cadence": _weekly_cadence(),
    }


class TrafficPlanExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(
        self,
        *,
        opportunities: list[RevenueOpportunity],
        offers: list[OfferDraft],
        site_base_url: str = "",
        click_redirect_url: str = "",
        lead_capture_url: str = "",
    ) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        plan = build_traffic_plan(
            opportunities=opportunities,
            offers=offers,
            site_base_url=site_base_url,
            click_redirect_url=click_redirect_url,
            lead_capture_url=lead_capture_url,
        )
        json_path = self.output_dir / "traffic_plan.json"
        markdown_path = self.output_dir / "TRAFFIC_PLAN.md"
        json_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(_to_markdown(plan), encoding="utf-8")
        return [json_path, markdown_path]


def _required_setup(*, site_base_url: str, offers: list[OfferDraft]) -> list[str]:
    setup: list[str] = []
    if not site_base_url:
        setup.append("Set SITE_BASE_URL")
    if not any(offer.payment_url for offer in offers):
        setup.append("Connect OFFER_PAYMENT_URLS")
    return setup


def _track(opportunity: RevenueOpportunity, offers: list[OfferDraft]) -> dict[str, Any]:
    matching_offers = [
        offer for offer in offers
        if offer.source == opportunity.source and offer.external_id == opportunity.external_id
    ]
    best_offer = _best_offer(matching_offers)
    surface = _surface_for_channel(opportunity.channel)
    return {
        "source": opportunity.source,
        "external_id": opportunity.external_id,
        "title": opportunity.title,
        "channel": opportunity.channel,
        "expected_value_usd": round(float(opportunity.expected_value_usd), 2),
        "primary_surface": surface["primary_surface"],
        "allowed_surfaces": surface["allowed_surfaces"],
        "distribution_steps": surface["distribution_steps"],
        "payment_configured": bool(best_offer and best_offer["payment_url"]),
        "best_offer": best_offer,
        "measure_after_days": 14,
        "prune_rule": "Revise if it earns clicks but no confirmed revenue after 14 days; pause if it has no clicks.",
    }


def _best_offer(offers: list[OfferDraft]) -> dict[str, Any] | None:
    if not offers:
        return None
    best = max(offers, key=lambda offer: (bool(offer.payment_url), float(offer.price_usd)))
    return {
        "offer_key": best.offer_key,
        "offer_type": best.offer_type,
        "price_usd": float(best.price_usd),
        "payment_url": best.payment_url,
    }


def _track_priority(track: dict[str, Any]) -> tuple[int, float, float, str]:
    payment_penalty = 0 if track["payment_configured"] else 1
    best_offer = track.get("best_offer") or {}
    price = float(best_offer.get("price_usd") or 0.0)
    return (payment_penalty, -price, -float(track["expected_value_usd"]), str(track["title"]))


def _surface_for_channel(channel: str) -> dict[str, Any]:
    if channel == "microtool_seo":
        return {
            "primary_surface": "owned_site_seo",
            "allowed_surfaces": ["owned_site", "owned_microtool", "search_index", "newsletter", "github_owned_repo"],
            "distribution_steps": [
                "Publish the owned microtool page with one concrete example and one setup-service CTA.",
                "Add the tool to the owned site index and sitemap for SEO discovery.",
                "Share a short changelog or case study only from owned channels or explicitly permitted communities.",
            ],
        }
    if channel == "article_affiliate":
        return {
            "primary_surface": "owned_article_seo",
            "allowed_surfaces": ["owned_site", "search_index", "newsletter", "affiliate_program"],
            "distribution_steps": [
                "Publish the reviewed article on the owned site with affiliate disclosure.",
                "Verify prices, screenshots, claims, and affiliate terms before adding links.",
                "Repurpose the article into one newsletter note after the page is indexed.",
            ],
        }
    if channel == "digital_product":
        return {
            "primary_surface": "owned_product_listing",
            "allowed_surfaces": ["owned_site", "owned_store", "newsletter", "lead_magnet"],
            "distribution_steps": [
                "Publish the owned product listing and connect checkout metadata.",
                "Offer a free lead magnet that points to the paid template or setup upsell.",
                "Send one opt-in newsletter launch after the product files are reviewed.",
            ],
        }
    if channel == "paid_setup_kit":
        return {
            "primary_surface": "owned_service_page",
            "allowed_surfaces": ["owned_site", "intake_form", "newsletter", "case_study"],
            "distribution_steps": [
                "Publish the owned service page with fixed scope, acceptance criteria, and intake form.",
                "Add one case-study style page after each successful delivery.",
                "Cap active slots before promoting the offer broadly.",
            ],
        }
    if channel in {"github_issue_helper", "open_source_sponsorship"}:
        return {
            "primary_surface": "owned_github_repo",
            "allowed_surfaces": ["owned_repo_readme", "github_sponsors", "owned_docs", "newsletter"],
            "distribution_steps": [
                "Publish the useful repo or patch draft in an owned repository.",
                "Put sponsorship CTAs only in owned README, docs, or funding files.",
                "Do not add payment links to third-party issues or pull requests.",
            ],
        }
    return {
        "primary_surface": "owned_asset_page",
        "allowed_surfaces": ["owned_site", "newsletter", "owned_docs"],
        "distribution_steps": [
            "Publish the reviewed asset on an owned page before sharing it elsewhere.",
            "Route all CTAs through configured checkout or support links.",
            "Use third-party sites only when their rules explicitly permit the post.",
        ],
    }


def _weekly_cadence() -> list[dict[str, Any]]:
    return [
        {
            "window": "daily",
            "actions": [
                "Publish or refresh one owned asset from the top launch track.",
                "Review click_events and conversion_events for yesterday's traffic.",
            ],
        },
        {
            "window": "weekly",
            "actions": [
                "Clone the best converting topic into one related asset.",
                "Pause or revise tracks with clicks but no revenue.",
            ],
        },
        {
            "window": "monthly",
            "actions": [
                "Compare revenue by channel and move effort toward the best paid path.",
                "Raise prices or add higher-ticket service tiers when delivery evidence exists.",
            ],
        },
    ]


def _to_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Traffic Plan",
        "",
        f"- Traffic ready: {'yes' if plan['traffic_ready'] else 'no'}",
        f"- Tracks: {plan['summary']['tracks']}",
        f"- Payment configured tracks: {plan['summary']['payment_configured_tracks']}",
        "",
    ]
    if plan["required_setup"]:
        lines.extend(["## Required Setup", ""])
        lines.extend(f"- {item}" for item in plan["required_setup"])
        lines.append("")

    lines.extend(["## Tracks", ""])
    for track in plan["tracks"]:
        best_offer = track.get("best_offer") or {}
        lines.extend(
            [
                f"### {track['title']}",
                "",
                f"- Channel: {track['channel']}",
                f"- Primary surface: {track['primary_surface']}",
                f"- Allowed surfaces: {', '.join(track['allowed_surfaces'])}",
                f"- Best offer: `{best_offer.get('offer_key', 'none')}` at {_money(best_offer.get('price_usd', 0))}",
                f"- Payment configured: {'yes' if track['payment_configured'] else 'no'}",
                "",
            ]
        )
        lines.extend(f"- {step}" for step in track["distribution_steps"])
        lines.append("")

    lines.extend(["## Metrics", ""])
    lines.extend(f"- {metric}" for metric in plan["metrics"])
    lines.append("")
    lines.extend(["## Weekly Cadence", ""])
    for cadence in plan["weekly_cadence"]:
        lines.append(f"### {cadence['window']}")
        lines.extend(f"- {action}" for action in cadence["actions"])
        lines.append("")
    lines.extend(["## Guardrails", ""])
    lines.extend(f"- {guardrail}" for guardrail in plan["guardrails"])
    lines.append("")
    return "\n".join(lines)


def _money(value: float | int) -> str:
    amount = float(value)
    if amount.is_integer():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"
