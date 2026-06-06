import unittest

from farm_loop.webhook_handler import handle_buymeacoffee_webhook


class FakeSupabase:
    def __init__(self):
        self.tip_events = []
        self.events = []

    def insert_tip_event(self, payload):
        self.tip_events.append(payload)
        return [{"id": "tip-1", **payload}]

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


if __name__ == "__main__":
    unittest.main()
