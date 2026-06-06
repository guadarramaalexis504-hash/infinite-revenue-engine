import unittest

from farm_loop.webhooks import parse_buymeacoffee_event, verify_webhook_token


class WebhookTests(unittest.TestCase):
    def test_verify_webhook_token_accepts_configured_header_value(self):
        headers = {"X-BuyMeACoffee-Token": "expected-token"}

        self.assertTrue(verify_webhook_token(headers, "expected-token"))
        self.assertFalse(verify_webhook_token(headers, "wrong-token"))

    def test_parse_buymeacoffee_event_extracts_tip_payload(self):
        payload = {
            "type": "support.created",
            "data": {
                "id": "support-123",
                "amount": "5.00",
                "currency": "USD",
                "supporter_name": "Ada",
            },
        }

        parsed = parse_buymeacoffee_event(payload)

        self.assertEqual(parsed["provider"], "buymeacoffee")
        self.assertEqual(parsed["external_id"], "support-123")
        self.assertEqual(parsed["amount_usd"], 5.0)
        self.assertEqual(parsed["payload"], payload)


if __name__ == "__main__":
    unittest.main()
