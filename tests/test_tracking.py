import unittest

from farm_loop.revenue_scoring import RevenueOpportunity
from farm_loop.tracking import build_click_event_payload, build_tracking_url


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.opportunity = RevenueOpportunity(
            source="idea_catalog",
            external_id="offer-webhook-setup-service",
            title="Webhook Setup Service",
            url="file://revenue_ideas.json#offer-webhook-setup-service",
            problem="Creators need payment webhooks saved into a database.",
            tags=["webhooks", "stripe"],
            channel="paid_setup_kit",
            payout_estimate_usd=199,
            conversion_probability=0.06,
            estimated_cost_usd=5,
            risk_penalty_usd=2,
            build_minutes=50,
            expected_value_usd=4.94,
        )

    def test_build_tracking_url_preserves_existing_query_and_adds_stable_attribution(self):
        url = build_tracking_url(
            "https://buymeacoffee.com/example?existing=1",
            self.opportunity,
            content="support_cta",
        )

        self.assertIn("existing=1", url)
        self.assertIn("utm_source=revenue_site", url)
        self.assertIn("utm_medium=paid_setup_kit", url)
        self.assertIn("utm_campaign=offer-webhook-setup-service", url)
        self.assertIn("utm_content=support_cta", url)
        self.assertIn("ire_source=idea_catalog", url)
        self.assertIn("ire_external_id=offer-webhook-setup-service", url)

    def test_build_click_event_payload_matches_supabase_click_events_shape(self):
        payload = build_click_event_payload(
            self.opportunity,
            target_url="https://buymeacoffee.com/example",
            content="support_cta",
        )

        self.assertEqual(payload["source"], "revenue_site")
        self.assertIsNone(payload["offer_id"])
        self.assertEqual(payload["payload"]["opportunity_source"], "idea_catalog")
        self.assertEqual(payload["payload"]["opportunity_external_id"], "offer-webhook-setup-service")
        self.assertEqual(payload["payload"]["channel"], "paid_setup_kit")
        self.assertEqual(payload["payload"]["target_url"], "https://buymeacoffee.com/example")
        self.assertEqual(payload["payload"]["content"], "support_cta")


if __name__ == "__main__":
    unittest.main()
