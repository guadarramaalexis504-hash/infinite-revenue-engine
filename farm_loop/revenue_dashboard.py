from __future__ import annotations

from collections import Counter


def _amount(row: dict) -> float:
    try:
        return float(row.get("amount_usd") or 0)
    except (TypeError, ValueError):
        return 0.0


def build_dashboard_snapshot(
    *,
    conversions: list[dict],
    tips: list[dict],
    assets: list[dict],
    milestones: list[float],
) -> dict:
    total = round(sum(_amount(row) for row in conversions) + sum(_amount(row) for row in tips), 2)
    sorted_milestones = sorted(milestones)
    next_milestone = next((milestone for milestone in sorted_milestones if milestone > total), sorted_milestones[-1])
    source_totals: Counter[str] = Counter()
    for row in conversions:
        source_totals[str(row.get("source") or "unknown")] += _amount(row)
    best_source = source_totals.most_common(1)[0][0] if source_totals else None
    pending_assets = sum(1 for asset in assets if asset.get("status") == "draft")
    failed_experiments = sum(1 for asset in assets if asset.get("status") == "failed")
    progress = 100.0 if next_milestone == 0 else round((total / next_milestone) * 100, 2)
    return {
        "total_revenue_usd": total,
        "next_milestone_usd": next_milestone,
        "milestone_progress_percent": progress,
        "best_source": best_source,
        "pending_assets": pending_assets,
        "failed_experiments": failed_experiments,
    }
