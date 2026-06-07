from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .offers import OfferDraft


def build_revenue_forecast(*, offers: list[OfferDraft], milestones: list[float]) -> dict[str, Any]:
    normalized_milestones = sorted(float(milestone) for milestone in milestones)
    rows = [_offer_forecast_row(offer, normalized_milestones) for offer in offers]
    configured = [row for row in rows if row["payment_configured"]]
    best_offer = _best_offer(rows)
    return {
        "milestones": normalized_milestones,
        "totals": {
            "offers": len(rows),
            "payment_configured_offers": len(configured),
            "unconfigured_offers": len(rows) - len(configured),
        },
        "best_offer": best_offer,
        "offers": rows,
        "notes": [
            "Forecasts are unit-count targets, not income guarantees.",
            "Revenue requires live checkout links, webhooks, owned publishing, traffic, and delivery.",
            "Prioritize higher-price offers first because low-price support requires much more volume.",
        ],
    }


class RevenueForecastExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(self, *, offers: list[OfferDraft], milestones: list[float]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        forecast = build_revenue_forecast(offers=offers, milestones=milestones)
        json_path = self.output_dir / "revenue_forecast.json"
        markdown_path = self.output_dir / "REVENUE_FORECAST.md"
        json_path.write_text(json.dumps(forecast, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(_to_markdown(forecast), encoding="utf-8")
        return [json_path, markdown_path]


def _offer_forecast_row(offer: OfferDraft, milestones: list[float]) -> dict[str, Any]:
    price = max(float(offer.price_usd), 0.0)
    milestone_units = {
        _milestone_key(milestone): _units_needed(milestone, price)
        for milestone in milestones
    }
    return {
        **asdict(offer),
        "price_usd": price,
        "payment_configured": bool(offer.payment_url),
        "milestone_units": milestone_units,
        "activation_notes": _activation_notes(offer),
    }


def _best_offer(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    top_milestone = max((float(key) for row in rows for key in row["milestone_units"]), default=0.0)
    best = min(
        rows,
        key=lambda row: (
            row["milestone_units"].get(_milestone_key(top_milestone), math.inf),
            0 if row["payment_configured"] else 1,
            -row["price_usd"],
        ),
    )
    return {
        "offer_key": best["offer_key"],
        "title": best["title"],
        "channel": best["channel"],
        "offer_type": best["offer_type"],
        "price_usd": best["price_usd"],
        "payment_configured": best["payment_configured"],
        "units_to_top_milestone": best["milestone_units"].get(_milestone_key(top_milestone), 0),
    }


def _units_needed(milestone: float, price_usd: float) -> int:
    if price_usd <= 0:
        return 0
    return max(1, math.ceil(float(milestone) / price_usd))


def _activation_notes(offer: OfferDraft) -> list[str]:
    notes: list[str] = []
    if not offer.payment_url:
        notes.append(f"Connect payment URL for `{offer.offer_key}` before expecting revenue.")
    if offer.price_usd <= 5:
        notes.append("Low-ticket offer: use for support signals, not the main path to $20k.")
    if offer.offer_type in {"fixed_scope_service", "setup_service"}:
        notes.append("Service offer: keep scope bounded and track delivery capacity before scaling.")
    return notes or ["Ready for owned-channel launch after manual review."]


def _to_markdown(forecast: dict[str, Any]) -> str:
    lines = [
        "# Revenue Forecast",
        "",
        "Forecasts are conversion-count targets, not guaranteed income.",
        "",
        f"- Offers: {forecast['totals']['offers']}",
        f"- Payment configured: {forecast['totals']['payment_configured_offers']}",
        f"- Missing payment URLs: {forecast['totals']['unconfigured_offers']}",
        "",
    ]
    best = forecast.get("best_offer")
    if best:
        lines.extend(
            [
                "## Fastest Listed Path",
                "",
                f"- Offer: `{best['offer_key']}`",
                f"- Price: {_money(best['price_usd'])}",
                f"- Units to top milestone: {best['units_to_top_milestone']}",
                f"- Payment configured: {'yes' if best['payment_configured'] else 'no'}",
                "",
            ]
        )

    milestone_headers = [f"Units to {_money(milestone)}" for milestone in forecast["milestones"]]
    lines.extend(
        [
            "## Offer Unit Targets",
            "",
            "| Offer | Type | Channel | Price | Payment | " + " | ".join(milestone_headers) + " |",
            "| --- | --- | --- | ---: | --- | " + " | ".join("---:" for _ in milestone_headers) + " |",
        ]
    )
    for row in forecast["offers"]:
        units = [str(row["milestone_units"][_milestone_key(milestone)]) for milestone in forecast["milestones"]]
        payment = "yes" if row["payment_configured"] else "no"
        lines.append(
            f"| {row['title']} | {row['offer_type']} | {row['channel']} | {_money(row['price_usd'])} | "
            f"{payment} | " + " | ".join(units) + " |"
        )
    lines.append("")

    lines.extend(["## Activation Notes", ""])
    for row in forecast["offers"]:
        for note in row["activation_notes"]:
            lines.append(f"- `{row['offer_key']}`: {note}")
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
