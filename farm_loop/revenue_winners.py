"""Winners system: double down on what actually converts.

The pruning module pauses losers and flags engaged-but-unpaid offers. This
closes the other half of the loop: when an offer earns real revenue, clone it
into fresh `winner_variant` opportunities with new angles so the engine builds
more assets around the proven winner. Revenue compounds toward what works.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OfferPerformance:
    offer_key: str
    title: str
    channel: str
    price_usd: float
    clicks: int
    conversions: int
    revenue: float

    @property
    def conversion_rate(self) -> float:
        return round(self.conversions / self.clicks, 4) if self.clicks else 0.0


@dataclass(frozen=True)
class WinnerPlan:
    winners: list[OfferPerformance] = field(default_factory=list)
    variant_opportunities: list[dict] = field(default_factory=list)


# Angle templates used to clone a winning offer into new opportunities.
_VARIANT_ANGLES = [
    ("Pro", 1.6, "Premium tier of the proven winner with deeper scope."),
    ("for Teams", 2.2, "Team/seat-based version of the winning offer."),
    ("Quick Start", 0.6, "Lower-priced, faster-scope entry version of the winner."),
    ("Audit", 1.3, "One-off audit spin on the winning offer."),
    ("Annual", 5.0, "Yearly bundle of the winning recurring offer."),
]


def _offer_key(row: dict) -> str | None:
    payload = row.get("payload") or {}
    if isinstance(payload, dict) and payload.get("offer_key"):
        return str(payload["offer_key"])
    if row.get("offer_id"):
        return str(row["offer_id"])
    return None


def _amount(row: dict) -> float:
    try:
        return float(row.get("amount_usd") or 0)
    except (TypeError, ValueError):
        return 0.0


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].rstrip("-")


def summarize_offer_performance(offers: list[dict], clicks: list[dict], conversions: list[dict]) -> list[OfferPerformance]:
    clicks_by_key: Counter[str] = Counter()
    for row in clicks:
        key = _offer_key(row)
        if key:
            clicks_by_key[key] += 1

    conv_by_key: Counter[str] = Counter()
    rev_by_key: defaultdict[str, float] = defaultdict(float)
    for row in conversions:
        key = _offer_key(row)
        if key:
            conv_by_key[key] += 1
            rev_by_key[key] += _amount(row)

    meta: dict[str, dict] = {}
    for offer in offers:
        key = _offer_key(offer)
        if key and key not in meta:
            meta[key] = offer

    keys = set(clicks_by_key) | set(conv_by_key) | set(meta)
    performance = [
        OfferPerformance(
            offer_key=key,
            title=str((meta.get(key) or {}).get("title") or key),
            channel=str((meta.get(key) or {}).get("channel") or "microtool_seo"),
            price_usd=float((meta.get(key) or {}).get("price_usd") or 0),
            clicks=clicks_by_key[key],
            conversions=conv_by_key[key],
            revenue=round(rev_by_key[key], 2),
        )
        for key in keys
    ]
    performance.sort(key=lambda p: (p.revenue, p.clicks, p.conversions), reverse=True)
    return performance


def generate_variant_opportunities(winner: OfferPerformance, *, count: int = 3) -> list[dict]:
    base_price = winner.price_usd if winner.price_usd > 0 else max(winner.revenue, 19.0)
    base_slug = _slug(winner.title) or _slug(winner.offer_key)
    variants: list[dict] = []
    for index, (suffix, multiplier, note) in enumerate(_VARIANT_ANGLES[: max(0, count)]):
        payout = round(max(9.0, base_price * multiplier), 2)
        variants.append(
            {
                "source": "winner_variant",
                "external_id": f"{base_slug}-variant-{index + 1}",
                "title": f"{winner.title} {suffix}"[:80],
                "url": f"winner-variant://{base_slug}#{index + 1}",
                "problem": f"{note} Cloned from a winning offer that earned ${winner.revenue:.2f}.",
                "tags": [winner.channel, "winner-variant"],
                "channel": winner.channel,
                "payout_estimate_usd": payout,
                # Proven demand: bump conversion probability above a cold idea.
                "conversion_probability": 0.1,
                "estimated_cost_usd": 4.0,
                "risk_penalty_usd": 1.0,
                "build_minutes": 45,
            }
        )
    return variants


def build_winner_plan(
    *,
    offers: list[dict],
    clicks: list[dict],
    conversions: list[dict],
    min_revenue: float = 0.01,
    max_variants_per_winner: int = 3,
) -> WinnerPlan:
    performance = summarize_offer_performance(offers, clicks, conversions)
    winners = [p for p in performance if p.revenue >= min_revenue]
    variant_opportunities: list[dict] = []
    for winner in winners:
        variant_opportunities.extend(generate_variant_opportunities(winner, count=max_variants_per_winner))
    return WinnerPlan(winners=winners, variant_opportunities=variant_opportunities)
