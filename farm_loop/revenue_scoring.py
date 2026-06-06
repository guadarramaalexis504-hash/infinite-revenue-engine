from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class RevenueOpportunity:
    source: str
    external_id: str
    title: str
    url: str
    problem: str
    tags: list[str]
    channel: str
    payout_estimate_usd: float
    conversion_probability: float
    estimated_cost_usd: float
    risk_penalty_usd: float
    build_minutes: int
    expected_value_usd: float = 0.0

    def to_payload(self) -> dict:
        return {
            "source": self.source,
            "external_id": self.external_id,
            "title": self.title,
            "url": self.url,
            "problem": self.problem,
            "tags": self.tags,
            "channel": self.channel,
            "payout_estimate_usd": self.payout_estimate_usd,
            "conversion_probability": self.conversion_probability,
            "estimated_cost_usd": self.estimated_cost_usd,
            "risk_penalty_usd": self.risk_penalty_usd,
            "build_minutes": self.build_minutes,
            "expected_value_usd": self.expected_value_usd,
            "status": "new",
        }


def compute_expected_value(opportunity: RevenueOpportunity) -> float:
    value = (
        opportunity.payout_estimate_usd * opportunity.conversion_probability
        - opportunity.estimated_cost_usd
        - opportunity.risk_penalty_usd
    )
    return round(value, 2)


def score_opportunity(opportunity: RevenueOpportunity) -> RevenueOpportunity:
    base = compute_expected_value(opportunity)
    reusable_bonus = 2.0 if opportunity.channel in {"microtool_seo", "digital_product", "open_source_sponsorship"} else 0.0
    speed_bonus = 1.5 if opportunity.build_minutes <= 45 else 0.0
    scored_value = round(base + reusable_bonus + speed_bonus, 2)
    return replace(opportunity, expected_value_usd=scored_value)


def rank_revenue_opportunities(
    opportunities: list[RevenueOpportunity],
    *,
    max_items: int = 10,
    min_expected_value_usd: float = 0.0,
) -> list[RevenueOpportunity]:
    seen: set[tuple[str, str]] = set()
    best_by_topic: dict[tuple[str, str], RevenueOpportunity] = {}
    for opportunity in opportunities:
        key = (opportunity.source, opportunity.external_id)
        if key in seen:
            continue
        seen.add(key)
        candidate = score_opportunity(opportunity)
        if candidate.expected_value_usd >= min_expected_value_usd:
            topic_key = (candidate.channel, _normalize_title(candidate.title))
            existing = best_by_topic.get(topic_key)
            if existing is None or _ranking_key(candidate) > _ranking_key(existing):
                best_by_topic[topic_key] = candidate
    scored = list(best_by_topic.values())
    scored.sort(key=lambda item: (item.expected_value_usd, -item.build_minutes), reverse=True)
    return scored[:max_items]


def _normalize_title(title: str) -> str:
    return "".join(character.lower() for character in title if character.isalnum())


def _ranking_key(opportunity: RevenueOpportunity) -> tuple[float, int]:
    return (opportunity.expected_value_usd, -opportunity.build_minutes)
