import hashlib
import hmac
import unittest

from farm_loop.webhook_handler import handle_conversion_webhook
from farm_loop.webhooks import verify_stripe_signature


SECRET = "whsec_test_secret_123"


def sign(raw_body: str, timestamp: int, secret: str = SECRET) -> str:
    mac = hmac.new(secret.encode(), f"{timestamp}.{raw_body}".encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={mac}"


class FakeSupabase:
    def __init__(self):
        self.conversions = []

    def insert_conversion_event(self, payload):
        self.conversions.append(payload)
        return [payload]

    def insert_event(self, *a, **k):
        return None


class StripeSignatureTests(unittest.TestCase):
    def test_valid_signature_passes(self):
        body = '{"id":"evt_1","type":"checkout.session.completed"}'
        header = sign(body, 1000)
        self.assertTrue(verify_stripe_signature(body, header, SECRET, now=1000))

    def test_tampered_body_fails(self):
        header = sign('{"amount":1}', 1000)
        self.assertFalse(verify_stripe_signature('{"amount":999}', header, SECRET, now=1000))

    def test_wrong_secret_fails(self):
        body = '{"id":"evt_1"}'
        header = sign(body, 1000, secret="whsec_other")
        self.assertFalse(verify_stripe_signature(body, header, SECRET, now=1000))

    def test_expired_timestamp_fails(self):
        body = '{"id":"evt_1"}'
        header = sign(body, 1000)
        self.assertFalse(verify_stripe_signature(body, header, SECRET, now=1000 + 9999, tolerance=300))

    def test_missing_or_malformed_header_fails(self):
        self.assertFalse(verify_stripe_signature("{}", "", SECRET, now=1000))
        self.assertFalse(verify_stripe_signature("{}", "garbage", SECRET, now=1000))

    def test_empty_secret_fails(self):
        body = '{"id":"evt_1"}'
        header = sign(body, 1000)
        self.assertFalse(verify_stripe_signature(body, header, "", now=1000))


class ConversionWebhookStripeTests(unittest.TestCase):
    def test_stripe_provider_requires_valid_signature_when_secret_set(self):
        supa = FakeSupabase()
        body = '{"id":"evt_1","data":{"object":{"amount_total":4900,"metadata":{"offer_key":"kw:t:setup_service"}}}}'
        good_header = sign(body, 1000)
        result = handle_conversion_webhook(
            headers={"Stripe-Signature": good_header},
            payload={"id": "evt_1", "data": {"object": {"amount_total": 4900, "metadata": {"offer_key": "kw:t:setup_service"}}}},
            expected_token="",
            provider="stripe",
            supabase=supa,
            raw_body=body,
            stripe_webhook_secret=SECRET,
            now=1000,
        )
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(len(supa.conversions), 1)

    def test_stripe_provider_rejects_bad_signature(self):
        supa = FakeSupabase()
        body = '{"id":"evt_1"}'
        with self.assertRaises(PermissionError):
            handle_conversion_webhook(
                headers={"Stripe-Signature": "t=1000,v1=deadbeef"},
                payload={"id": "evt_1"},
                expected_token="",
                provider="stripe",
                supabase=supa,
                raw_body=body,
                stripe_webhook_secret=SECRET,
                now=1000,
            )
        self.assertEqual(supa.conversions, [])

    def test_non_stripe_provider_still_uses_token(self):
        supa = FakeSupabase()
        result = handle_conversion_webhook(
            headers={"X-Revenue-Webhook-Token": "tok"},
            payload={"external_id": "m1", "amount_usd": 49, "source": "manual"},
            expected_token="tok",
            provider="manual",
            supabase=supa,
            stripe_webhook_secret=SECRET,
        )
        self.assertEqual(result["status"], "recorded")


if __name__ == "__main__":
    unittest.main()
