import unittest

from farm_loop.webhook_handler import handle_buymeacoffee_webhook, handle_conversion_webhook


class FakeSupabase:
    def __init__(self):
        self.tip_events = []
        self.conversion_events = []
        self.events = []

    def insert_tip_event(self, payload):
        self.tip_events.append(payload)
        return [{"id": "tip-1", **payload}]

    def insert_conversion_event(self, payload):
        self.conversion_events.append(payload)
        return [{"id": "conversion-1", **payload}]

    def insert_event(self, run_id, event_type, payload):
        self.events.append((run_id, event_type, payload))


class WebhookHandlerTests(unittest.TestCase):
    def test_handle_buymeacoffee_webhook_validates_and_records_tip(self):
        supabase = FakeSupabase()
        payload = {"data": {"id": "support-123", "amount": "4.00", "currency": "USD"}}

        result = handle_buymeacoffee_webhook(
            headers={"X-BuyMeACoffee-Token": "expected-token"},
            payload=payload,
            expected_token="expected-token",
            supabase=supabase,
        )

        self.assertEqual(result["status"], "recorded")
        self.assertEqual(supabase.tip_events[0]["external_id"], "support-123")
        self.assertEqual(supabase.tip_events[0]["amount_usd"], 4.0)

    def test_handle_buymeacoffee_webhook_rejects_invalid_token(self):
        supabase = FakeSupabase()

        with self.assertRaisesRegex(PermissionError, "Invalid Buy Me a Coffee webhook token"):
            handle_buymeacoffee_webhook(
                headers={"X-BuyMeACoffee-Token": "bad-token"},
                payload={"data": {"id": "support-123", "amount": "4.00", "currency": "USD"}},
                expected_token="expected-token",
                supabase=supabase,
            )

        self.assertEqual(supabase.tip_events, [])

    def test_handle_conversion_webhook_validates_and_records_confirmed_conversion(self):
        supabase = FakeSupabase()
        payload = {
            "id": "evt_123",
            "data": {
                "object": {
                    "amount_total": 9900,
                    "currency": "usd",
                    "metadata": {"offer_id": "offer-1", "source": "paid_setup_kit"},
                }
            },
        }

        result = handle_conversion_webhook(
            headers={"X-Revenue-Webhook-Token": "expected-token"},
            payload=payload,
            expected_token="expected-token",
            provider="stripe",
            supabase=supabase,
        )

        self.assertEqual(result["status"], "recorded")
        self.assertEqual(supabase.conversion_events[0]["external_id"], "stripe:evt_123")
        self.assertEqual(supabase.conversion_events[0]["amount_usd"], 99.0)
        self.assertEqual(supabase.events[-1][1], "conversion_recorded")

    def test_handle_conversion_webhook_rejects_invalid_token(self):
        supabase = FakeSupabase()

        with self.assertRaisesRegex(PermissionError, "Invalid conversion webhook token"):
            handle_conversion_webhook(
                headers={"X-Revenue-Webhook-Token": "bad-token"},
                payload={"id": "evt_123", "amount_usd": 10},
                expected_token="expected-token",
                provider="manual",
                supabase=supabase,
            )

        self.assertEqual(supabase.conversion_events, [])


if __name__ == "__main__":
    unittest.main()
