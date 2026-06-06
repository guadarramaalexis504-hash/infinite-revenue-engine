import unittest

from farm_loop.revenue_dashboard import build_dashboard_snapshot


class RevenueDashboardTests(unittest.TestCase):
    def test_dashboard_calculates_milestone_progress_and_best_source(self):
        snapshot = build_dashboard_snapshot(
            conversions=[
                {"source": "microtool_seo", "offer_id": "offer-1", "amount_usd": 12},
                {"source": "github_issue_helper", "offer_id": "offer-2", "amount_usd": 38},
            ],
            tips=[{"amount_usd": 5}],
            assets=[
                {"status": "draft"},
                {"status": "published"},
                {"status": "failed"},
            ],
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(snapshot["total_revenue_usd"], 55)
        self.assertEqual(snapshot["next_milestone_usd"], 200)
        self.assertEqual(snapshot["milestone_progress_percent"], 27.5)
        self.assertEqual(snapshot["best_source"], "github_issue_helper")
        self.assertEqual(snapshot["pending_assets"], 1)
        self.assertEqual(snapshot["failed_experiments"], 1)


if __name__ == "__main__":
    unittest.main()
