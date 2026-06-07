from __future__ import annotations

from collections import Counter
from typing import Any


def _amount(row: dict) -> float:
    try:
        return float(row.get("amount_usd") or 0)
    except (TypeError, ValueError):
        return 0.0


def _payload(row: dict) -> dict:
    payload = row.get("payload") or {}
    return payload if isinstance(payload, dict) else {}


def _offer_id(row: dict) -> str | None:
    value = row.get("offer_id")
    if value:
        return str(value)
    payload = _payload(row)
    value = payload.get("offer_key")
    return str(value) if value else None


def _catalog_offer_id(row: dict) -> str | None:
    value = row.get("id")
    if value:
        return str(value)
    payload = _payload(row)
    value = payload.get("offer_key")
    return str(value) if value else None


def _best_offer(conversions: list[dict], offers: list[dict]) -> dict[str, Any] | None:
    offer_totals: Counter[str] = Counter()
    for row in conversions:
        offer_id = _offer_id(row)
        if offer_id:
            offer_totals[offer_id] += _amount(row)
    if not offer_totals:
        return None
    best_id, revenue = offer_totals.most_common(1)[0]
    titles = {
        offer_id: str(offer.get("title") or offer_id)
        for offer in offers
        if (offer_id := _catalog_offer_id(offer))
    }
    return {"id": best_id, "title": titles.get(best_id, best_id), "revenue_usd": round(revenue, 2)}


def _clicks_by_content(clicks: list[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in clicks:
        payload = _payload(row)
        content = payload.get("utm_content") or payload.get("content") or "unknown"
        counter[str(content)] += 1
    return dict(counter)


def _failed_experiments(assets: list[dict], experiments: list[dict]) -> int:
    if experiments:
        return sum(1 for experiment in experiments if experiment.get("status") in {"lost", "failed"})
    return sum(1 for asset in assets if asset.get("status") == "failed")


def _recommended_actions(
    *,
    total: float,
    best_source: str | None,
    clicks: list[dict],
    conversions: list[dict],
    pending_assets: int,
    remaining: float,
) -> list[str]:
    if total <= 0:
        return [
            "Publish one owned asset with a configured payment CTA before generating more drafts.",
            f"Push the first conversion toward the ${remaining:.2f} milestone.",
        ]
    actions: list[str] = []
    if best_source:
        actions.append(f"Double down on {best_source}: create two more assets and one higher-ticket offer.")
    if clicks and not conversions:
        actions.append("Clicks exist without conversions: tighten the offer, price, and landing page CTA.")
    if pending_assets:
        actions.append(f"Review and publish {pending_assets} pending draft asset(s) before adding more backlog.")
    if not actions:
        actions.append("Keep discovery running and compare the next revenue snapshot against this baseline.")
    return actions


def build_dashboard_snapshot(
    *,
    conversions: list[dict],
    tips: list[dict],
    assets: list[dict],
    milestones: list[float],
    clicks: list[dict] | None = None,
    offers: list[dict] | None = None,
    experiments: list[dict] | None = None,
) -> dict:
    clicks = clicks or []
    offers = offers or []
    experiments = experiments or []
    total = round(sum(_amount(row) for row in conversions) + sum(_amount(row) for row in tips), 2)
    sorted_milestones = sorted(milestones)
    next_milestone = next((milestone for milestone in sorted_milestones if milestone > total), sorted_milestones[-1])
    source_totals: Counter[str] = Counter()
    for row in conversions:
        source_totals[str(row.get("source") or "unknown")] += _amount(row)
    best_source = source_totals.most_common(1)[0][0] if source_totals else None
    pending_assets = sum(1 for asset in assets if asset.get("status") == "draft")
    failed_experiments = _failed_experiments(assets, experiments)
    progress = 100.0 if next_milestone == 0 else round((total / next_milestone) * 100, 2)
    remaining = max(round(next_milestone - total, 2), 0.0)
    conversion_rate = 0.0 if not clicks else round((len(conversions) / len(clicks)) * 100, 2)
    return {
        "total_revenue_usd": total,
        "next_milestone_usd": next_milestone,
        "remaining_to_next_milestone_usd": remaining,
        "milestone_progress_percent": progress,
        "reached_milestones_usd": [milestone for milestone in sorted_milestones if milestone <= total],
        "best_source": best_source,
        "best_offer": _best_offer(conversions, offers),
        "conversion_rate_percent": conversion_rate,
        "clicks_count": len(clicks),
        "conversions_count": len(conversions),
        "clicks_by_content": _clicks_by_content(clicks),
        "pending_assets": pending_assets,
        "failed_experiments": failed_experiments,
        "experiments_by_status": dict(Counter(str(row.get("status") or "unknown") for row in experiments)),
        "recommended_next_actions": _recommended_actions(
            total=total,
            best_source=best_source,
            clicks=clicks,
            conversions=conversions,
            pending_assets=pending_assets,
            remaining=remaining,
        ),
    }
