from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


ACTIVE_STATUSES = {"planned", "running"}


@dataclass(frozen=True)
class PruneDecision:
    experiment_id: str
    action: str
    reason: str
    new_status: str | None = None
    launch_task: dict[str, Any] | None = None


def build_prune_plan(
    *,
    experiments: list[dict],
    offers: list[dict],
    clicks: list[dict],
    conversions: list[dict],
    now: datetime | None = None,
    stale_days: int = 14,
    click_threshold: int = 3,
) -> list[PruneDecision]:
    now = now or datetime.now(timezone.utc)
    offer_ids_by_opportunity = _offer_ids_by_opportunity(offers)
    clicks_by_offer = _event_counts_by_offer(clicks)
    revenue_by_offer = _revenue_by_offer(conversions)

    decisions: list[PruneDecision] = []
    for experiment in experiments:
        status = str(experiment.get("status") or "").lower()
        if status not in ACTIVE_STATUSES:
            continue

        experiment_id = str(experiment.get("id") or "")
        if not experiment_id:
            continue

        opportunity_id = str(experiment.get("opportunity_id") or "")
        offer_ids = offer_ids_by_opportunity.get(opportunity_id, [])
        click_count = sum(clicks_by_offer[offer_id] for offer_id in offer_ids)
        revenue = round(sum(revenue_by_offer[offer_id] for offer_id in offer_ids), 2)
        name = str(experiment.get("name") or experiment_id)

        if revenue > 0:
            decisions.append(
                PruneDecision(
                    experiment_id=experiment_id,
                    action="mark_won",
                    new_status="won",
                    reason=f"Confirmed ${revenue:.2f} revenue for {name}. Keep scaling this loop.",
                )
            )
            continue

        if click_count >= click_threshold:
            decisions.append(
                PruneDecision(
                    experiment_id=experiment_id,
                    action="revise_offer",
                    reason=f"{click_count} clicks but no confirmed revenue for {name}. Revise CTA, offer, or price.",
                    launch_task=_revision_task(experiment, click_count),
                )
            )
            continue

        if _is_stale(experiment.get("created_at"), now=now, stale_days=stale_days):
            decisions.append(
                PruneDecision(
                    experiment_id=experiment_id,
                    action="pause",
                    new_status="paused",
                    reason=f"No clicks or revenue for {name} after {stale_days}+ days. Pause until a stronger angle exists.",
                )
            )

    return decisions


def _offer_ids_by_opportunity(offers: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for offer in offers:
        opportunity_id = offer.get("opportunity_id")
        offer_id = _catalog_offer_id(offer)
        if opportunity_id and offer_id:
            grouped[str(opportunity_id)].append(str(offer_id))
    return grouped


def _event_counts_by_offer(rows: list[dict]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        offer_id = _offer_id(row)
        if offer_id:
            counts[offer_id] += 1
    return counts


def _revenue_by_offer(rows: list[dict]) -> Counter[str]:
    revenue: Counter[str] = Counter()
    for row in rows:
        offer_id = _offer_id(row)
        if offer_id:
            revenue[offer_id] += _amount(row)
    return revenue


def _offer_id(row: dict) -> str | None:
    value = row.get("offer_id")
    if value:
        return str(value)
    payload = row.get("payload") or {}
    if isinstance(payload, dict) and payload.get("offer_id"):
        return str(payload["offer_id"])
    if isinstance(payload, dict) and payload.get("offer_key"):
        return str(payload["offer_key"])
    return None


def _catalog_offer_id(row: dict) -> str | None:
    value = row.get("id")
    if value:
        return str(value)
    payload = row.get("payload") or {}
    if isinstance(payload, dict) and payload.get("offer_key"):
        return str(payload["offer_key"])
    return None


def _amount(row: dict) -> float:
    try:
        return float(row.get("amount_usd") or 0)
    except (TypeError, ValueError):
        return 0.0


def _is_stale(value: Any, *, now: datetime, stale_days: int) -> bool:
    if not value:
        return False
    try:
        created_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return (now - created_at).days >= stale_days


def _revision_task(experiment: dict, click_count: int) -> dict[str, Any]:
    name = str(experiment.get("name") or experiment.get("id") or "experiment")
    return {
        "opportunity_id": experiment.get("opportunity_id"),
        "priority": 35,
        "category": "monetize",
        "title": f"Revise offer for {name}",
        "detail": (
            f"{click_count} tracked clicks produced no confirmed revenue. "
            "Improve the landing CTA, tighten the offer, or test a lower-friction payment path."
        ),
        "status": "pending",
        "blocking": False,
        "payload": {
            "experiment_id": experiment.get("id"),
            "action": "revise_offer",
            "clicks_count": click_count,
        },
    }
