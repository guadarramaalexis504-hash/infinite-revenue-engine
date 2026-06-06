import unittest
from datetime import datetime, timezone

from farm_loop.revenue_pruning import build_prune_plan


class RevenuePruningTests(unittest.TestCase):
    def test_prune_plan_promotes_winners_revises_clicks_without_sales_and_pauses_stale_zero_signal(self):
        plan = build_prune_plan(
            experiments=[
                {
                    "id": "exp-won",
                    "opportunity_id": "opp-won",
                    "name": "microtool:won",
                    "status": "running",
                    "created_at": "2026-05-01T00:00:00+00:00",
                },
                {
                    "id": "exp-clicks",
                    "opportunity_id": "opp-clicks",
                    "name": "microtool:clicks",
                    "status": "running",
                    "created_at": "2026-05-01T00:00:00+00:00",
                },
                {
                    "id": "exp-stale",
                    "opportunity_id": "opp-stale",
                    "name": "microtool:stale",
                    "status": "running",
                    "created_at": "2026-05-01T00:00:00+00:00",
                },
            ],
            offers=[
                {"id": "offer-won", "opportunity_id": "opp-won", "title": "Won offer"},
                {"id": "offer-clicks", "opportunity_id": "opp-clicks", "title": "Clicky offer"},
            ],
            clicks=[
                {"offer_id": "offer-clicks"},
                {"offer_id": "offer-clicks"},
                {"offer_id": "offer-clicks"},
                {"offer_id": "offer-clicks"},
            ],
            conversions=[{"offer_id": "offer-won", "amount_usd": 49}],
            now=datetime(2026, 6, 6, tzinfo=timezone.utc),
            stale_days=14,
            click_threshold=3,
        )

        actions = {decision.experiment_id: decision.action for decision in plan}

        self.assertEqual(actions["exp-won"], "mark_won")
        self.assertEqual(actions["exp-clicks"], "revise_offer")
        self.assertEqual(actions["exp-stale"], "pause")
        self.assertEqual(plan[1].launch_task["category"], "monetize")
        self.assertIn("clicks but no confirmed revenue", plan[1].reason)
        self.assertIn("No clicks or revenue", plan[2].reason)

    def test_prune_plan_ignores_already_closed_experiments(self):
        plan = build_prune_plan(
            experiments=[
                {"id": "exp-paused", "opportunity_id": "opp-1", "status": "paused"},
                {"id": "exp-lost", "opportunity_id": "opp-2", "status": "lost"},
                {"id": "exp-won", "opportunity_id": "opp-3", "status": "won"},
            ],
            offers=[],
            clicks=[],
            conversions=[],
            now=datetime(2026, 6, 6, tzinfo=timezone.utc),
        )

        self.assertEqual(plan, [])


if __name__ == "__main__":
    unittest.main()
