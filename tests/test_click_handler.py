import unittest

from farm_loop.click_handler import handle_click_redirect


class FakeSupabase:
    def __init__(self):
        self.clicks = []
        self.events = []

    def insert_click_event(self, payload):
        self.clicks.append(payload)
        return [{"id": "click-1"}]

    def insert_event(self, run_id, event_type, payload):
        self.events.append((run_id, event_type, payload))


class ClickHandlerTests(unittest.TestCase):
    def test_handle_click_redirect_records_click_and_returns_safe_location(self):
        supabase = FakeSupabase()

        result = handle_click_redirect(
            query={
                "target": "https://buymeacoffee.com/example?utm_campaign=offer-webhook",
                "opportunity_source": "idea_catalog",
                "opportunity_external_id": "offer-webhook",
                "channel": "paid_setup_kit",
                "content": "support_cta",
                "offer_key": "idea_catalog:offer-webhook:support_cta",
            },
            supabase=supabase,
            allowed_target_hosts={"buymeacoffee.com"},
        )

        self.assertEqual(result["status"], "redirect")
        self.assertEqual(result["location"], "https://buymeacoffee.com/example?utm_campaign=offer-webhook")
        self.assertEqual(supabase.clicks[0]["source"], "revenue_site")
        self.assertEqual(supabase.clicks[0]["payload"]["opportunity_external_id"], "offer-webhook")
        self.assertEqual(supabase.clicks[0]["payload"]["offer_key"], "idea_catalog:offer-webhook:support_cta")
        self.assertEqual(supabase.events[0][1], "click_recorded")
        self.assertEqual(supabase.events[0][2]["offer_key"], "idea_catalog:offer-webhook:support_cta")

    def test_handle_click_redirect_rejects_disallowed_target_host(self):
        with self.assertRaises(PermissionError):
            handle_click_redirect(
                query={
                    "target": "https://evil.example/pay",
                    "opportunity_source": "idea_catalog",
                    "opportunity_external_id": "offer-webhook",
                    "channel": "paid_setup_kit",
                    "content": "support_cta",
                },
                supabase=FakeSupabase(),
                allowed_target_hosts={"buymeacoffee.com"},
            )

    def test_handle_click_redirect_requires_https_target(self):
        with self.assertRaises(ValueError):
            handle_click_redirect(
                query={
                    "target": "http://buymeacoffee.com/example",
                    "opportunity_source": "idea_catalog",
                    "opportunity_external_id": "offer-webhook",
                    "channel": "paid_setup_kit",
                    "content": "support_cta",
                },
                supabase=FakeSupabase(),
                allowed_target_hosts={"buymeacoffee.com"},
            )


if __name__ == "__main__":
    unittest.main()
