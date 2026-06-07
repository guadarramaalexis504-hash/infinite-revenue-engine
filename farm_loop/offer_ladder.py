from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from .offers import OfferDraft


def build_offer_ladder(*, offers: list[OfferDraft], milestones: list[float]) -> dict[str, Any]:
    normalized_milestones = sorted(float(milestone) for milestone in milestones)
    ladders = [
        _ladder_row(grouped_offers, normalized_milestones)
        for grouped_offers in _group_offers(offers).values()
    ]
    ladders.sort(key=lambda row: (row["best_tier"]["unit_targets"][_milestone_key(max(normalized_milestones))], row["title"]))
    return {
        "milestones": normalized_milestones,
        "totals": {
            "ladders": len(ladders),
            "tiers": sum(len(row["tiers"]) for row in ladders),
        },
        "best_path": _best_path(ladders, normalized_milestones),
        "ladders": ladders,
        "notes": [
            "Offer ladders are planning targets, not guaranteed revenue.",
            "Use owned channels and manual review before publishing or connecting checkout.",
            "Higher-ticket service tiers reduce required volume but require real delivery capacity.",
        ],
    }


class OfferLadderExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(self, *, offers: list[OfferDraft], milestones: list[float]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ladder = build_offer_ladder(offers=offers, milestones=milestones)
        json_path = self.output_dir / "offer_ladder.json"
        markdown_path = self.output_dir / "OFFER_LADDER.md"
        json_path.write_text(json.dumps(ladder, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(_to_markdown(ladder), encoding="utf-8")
        return [json_path, markdown_path]


def _group_offers(offers: list[OfferDraft]) -> dict[tuple[str, str], list[OfferDraft]]:
    grouped: dict[tuple[str, str], list[OfferDraft]] = defaultdict(list)
    for offer in offers:
        grouped[(offer.source, offer.external_id)].append(offer)
    return grouped


def _ladder_row(offers: list[OfferDraft], milestones: list[float]) -> dict[str, Any]:
    anchor = max(offers, key=lambda offer: offer.price_usd)
    tiers = _tier_rows(anchor, offers, milestones)
    best_tier = min(
        tiers,
        key=lambda tier: (
            tier["unit_targets"][_milestone_key(max(milestones))],
            0 if tier["payment_configured"] else 1,
            -tier["tier_price_usd"],
        ),
    )
    return {
        "source": anchor.source,
        "external_id": anchor.external_id,
        "channel": anchor.channel,
        "title": anchor.title,
        "existing_offer_keys": [offer.offer_key for offer in offers],
        "best_tier": best_tier,
        "tiers": tiers,
    }


def _tier_rows(anchor: OfferDraft, offers: list[OfferDraft], milestones: list[float]) -> list[dict[str, Any]]:
    existing_by_type = {offer.offer_type: offer for offer in offers}
    specs = [
        ("support_signal", 5.0, "Validate demand with low-friction support signals."),
        ("starter_setup", max(49.0, _existing_price(existing_by_type, "setup_service", 49.0)), "Small setup help with a tight checklist."),
        ("fixed_scope_service", max(299.0, _existing_price(existing_by_type, "fixed_scope_service", 299.0)), "Done-for-you setup with bounded deliverables."),
        ("premium_sprint", 999.0, "Premium implementation sprint with delivery capacity limits."),
    ]
    return [
        _tier_row(anchor, tier_type=tier_type, price_usd=price, description=description, milestones=milestones)
        for tier_type, price, description in specs
    ]


def _tier_row(
    anchor: OfferDraft,
    *,
    tier_type: str,
    price_usd: float,
    description: str,
    milestones: list[float],
) -> dict[str, Any]:
    return {
        "tier_key": f"{anchor.source}:{anchor.external_id}:{tier_type}",
        "tier_type": tier_type,
        "title": f"{anchor.title} - {tier_type.replace('_', ' ')}",
        "description": description,
        "tier_price_usd": price_usd,
        "payment_configured": bool(anchor.payment_url),
        "unit_targets": {
            _milestone_key(milestone): max(1, math.ceil(float(milestone) / price_usd))
            for milestone in milestones
        },
        "activation_notes": _activation_notes(tier_type),
    }


def _existing_price(existing_by_type: dict[str, OfferDraft], offer_type: str, fallback: float) -> float:
    offer = existing_by_type.get(offer_type)
    if not offer:
        return fallback
    return float(offer.price_usd)


def _best_path(ladders: list[dict[str, Any]], milestones: list[float]) -> dict[str, Any] | None:
    if not ladders:
        return None
    top_key = _milestone_key(max(milestones))
    best = min(
        (ladder["best_tier"] for ladder in ladders),
        key=lambda tier: (tier["unit_targets"][top_key], -tier["tier_price_usd"]),
    )
    return {
        "tier_key": best["tier_key"],
        "tier_type": best["tier_type"],
        "tier_price_usd": best["tier_price_usd"],
        "units_to_top_milestone": best["unit_targets"][top_key],
    }


def _activation_notes(tier_type: str) -> list[str]:
    if tier_type == "support_signal":
        return ["Use for validation only; this tier needs too much volume for $20k."]
    if tier_type == "premium_sprint":
        return ["Check delivery capacity before selling; cap simultaneous premium work."]
    if tier_type == "fixed_scope_service":
        return ["Write scope, acceptance criteria, and refund boundaries before checkout goes live."]
    return ["Connect checkout, intake, and webhook tracking before publishing."]


def _to_markdown(ladder: dict[str, Any]) -> str:
    lines = [
        "# Offer Ladder",
        "",
        "Offer ladders show how to turn one opportunity into higher-ticket paths toward each milestone.",
        "",
        f"- Ladders: {ladder['totals']['ladders']}",
        f"- Tiers: {ladder['totals']['tiers']}",
        "",
    ]
    best = ladder.get("best_path")
    if best:
        lines.extend(
            [
                "## Fastest Ladder Path",
                "",
                f"- Tier: `{best['tier_key']}`",
                f"- Price: {_money(best['tier_price_usd'])}",
                f"- Units to top milestone: {best['units_to_top_milestone']}",
                "",
            ]
        )
    milestone_headers = [f"Units to {_money(milestone)}" for milestone in ladder["milestones"]]
    for row in ladder["ladders"]:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Channel: {row['channel']}",
                f"- Existing offers: {', '.join(f'`{key}`' for key in row['existing_offer_keys'])}",
                "",
                "| Tier | Price | " + " | ".join(milestone_headers) + " |",
                "| --- | ---: | " + " | ".join("---:" for _ in milestone_headers) + " |",
            ]
        )
        for tier in row["tiers"]:
            units = [str(tier["unit_targets"][_milestone_key(milestone)]) for milestone in ladder["milestones"]]
            lines.append(
                f"| {tier['tier_type']} | {_money(tier['tier_price_usd'])} | "
                + " | ".join(units)
                + " |"
            )
        lines.extend(["", "Activation notes:"])
        for tier in row["tiers"]:
            for note in tier["activation_notes"]:
                lines.append(f"- `{tier['tier_key']}`: {note}")
        lines.append("")
    return "\n".join(lines)


def _milestone_key(value: float) -> str:
    amount = float(value)
    if amount.is_integer():
        return str(int(amount))
    return str(amount)


def _money(value: float) -> str:
    amount = float(value)
    if amount.is_integer():
        return f"${amount:,.0f}"
    return f"${amount:,.2f}"
