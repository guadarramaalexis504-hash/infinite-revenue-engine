import unittest

from farm_loop.revenue_dashboard import build_dashboard_snapshot


class RevenueDashboardTests(unittest.TestCase):
    def test_dashboard_calculates_milestone_progress_and_best_source(self):
        snapshot = build_dashboard_snapshot(
            conversions=[
                {"source": "microtool_seo", "offer_id": "offer-1", "amount_usd": 12},
                {"source": "github_issue_helper", "offer_id": "offer-2", "amount_usd": 38},
                {"source": "github_issue_helper", "offer_id": "offer-2", "amount_usd": 5},
            ],
            tips=[{"amount_usd": 5}],
            assets=[
                {"status": "draft"},
                {"status": "published"},
                {"status": "failed"},
            ],
            clicks=[
                {"payload": {"utm_content": "support"}},
                {"payload": {"content": "setup_service"}},
                {"payload": {"utm_content": "setup_service"}},
                {"payload": {"utm_content": "setup_service"}},
            ],
            offers=[
                {"id": "offer-1", "title": "Support the tool"},
                {"id": "offer-2", "title": "Fixed setup"},
            ],
            experiments=[
                {"status": "planned"},
                {"status": "lost"},
            ],
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(snapshot["total_revenue_usd"], 60)
        self.assertEqual(snapshot["next_milestone_usd"], 200)
        self.assertEqual(snapshot["milestone_progress_percent"], 30.0)
        self.assertEqual(snapshot["best_source"], "github_issue_helper")
        self.assertEqual(snapshot["best_offer"], {"id": "offer-2", "title": "Fixed setup", "revenue_usd": 43.0})
        self.assertEqual(snapshot["conversion_rate_percent"], 75.0)
        self.assertEqual(snapshot["clicks_by_content"]["setup_service"], 3)
        self.assertEqual(snapshot["pending_assets"], 1)
        self.assertEqual(snapshot["failed_experiments"], 1)
        self.assertIn("Double down on github_issue_helper", snapshot["recommended_next_actions"][0])

    def test_dashboard_recommends_payment_activation_when_no_revenue(self):
        snapshot = build_dashboard_snapshot(
            conversions=[],
            tips=[],
            assets=[{"status": "draft"}],
            milestones=[15, 200, 1000, 20000],
            clicks=[],
            offers=[],
            experiments=[],
        )

        self.assertEqual(snapshot["total_revenue_usd"], 0)
        self.assertEqual(snapshot["remaining_to_next_milestone_usd"], 15)
        self.assertIn("Publish one owned asset", snapshot["recommended_next_actions"][0])

    def test_dashboard_can_rank_best_offer_by_stable_offer_key(self):
        snapshot = build_dashboard_snapshot(
            conversions=[
                {
                    "source": "paid_setup_kit",
                    "amount_usd": 199,
                    "payload": {"offer_key": "idea_catalog:setup-kit:fixed_scope_service"},
                }
            ],
            tips=[],
            assets=[],
            milestones=[15, 200, 1000, 20000],
            clicks=[],
            offers=[
                {
                    "title": "Webhook setup",
                    "payload": {"offer_key": "idea_catalog:setup-kit:fixed_scope_service"},
                }
            ],
            experiments=[],
        )

        self.assertEqual(
            snapshot["best_offer"],
            {
                "id": "idea_catalog:setup-kit:fixed_scope_service",
                "title": "Webhook setup",
                "revenue_usd": 199.0,
            },
        )


if __name__ == "__main__":
    unittest.main()
