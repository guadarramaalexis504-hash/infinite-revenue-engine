import unittest

from farm_loop.conversions import build_manual_conversion_payload, parse_confirmed_conversion_event


class ConversionTests(unittest.TestCase):
    def test_parse_stripe_checkout_conversion_uses_attribution_metadata(self):
        payload = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_123",
                    "amount_total": 4900,
                    "currency": "usd",
                    "metadata": {
                        "offer_id": "offer-1",
                        "offer_key": "idea_catalog:setup-kit:fixed_scope_service",
                        "source": "paid_setup_kit",
                        "ire_external_id": "setup-kit",
                    },
                }
            },
        }

        parsed = parse_confirmed_conversion_event(payload, provider="stripe")

        self.assertEqual(parsed["offer_id"], "offer-1")
        self.assertEqual(parsed["source"], "paid_setup_kit")
        self.assertEqual(parsed["external_id"], "stripe:evt_123")
        self.assertEqual(parsed["amount_usd"], 49.0)
        self.assertEqual(parsed["payload"]["provider"], "stripe")
        self.assertEqual(parsed["payload"]["provider_external_id"], "evt_123")
        self.assertEqual(parsed["payload"]["offer_key"], "idea_catalog:setup-kit:fixed_scope_service")

    def test_parse_conversion_rejects_non_usd_payloads(self):
        payload = {
            "id": "evt_123",
            "data": {"object": {"amount_total": 4900, "currency": "eur"}},
        }

        with self.assertRaisesRegex(ValueError, "Unsupported conversion currency"):
            parse_confirmed_conversion_event(payload, provider="stripe")

    def test_parse_conversion_without_offer_id_uses_null_offer(self):
        parsed = parse_confirmed_conversion_event(
            {"id": "manual-1", "amount_usd": 12, "source": "manual"},
            provider="manual",
        )

        self.assertIsNone(parsed["offer_id"])

    def test_build_manual_conversion_payload_records_provider_prefixed_external_id(self):
        parsed = build_manual_conversion_payload(
            provider="gumroad",
            external_id="sale-123",
            amount_usd=29,
            source="digital_product",
            offer_id="offer-product",
            offer_key="idea_catalog:offer-product:digital_product",
            payload={"product": "Template pack"},
        )

        self.assertEqual(parsed["offer_id"], "offer-product")
        self.assertEqual(parsed["source"], "digital_product")
        self.assertEqual(parsed["external_id"], "gumroad:sale-123")
        self.assertEqual(parsed["amount_usd"], 29.0)
        self.assertEqual(parsed["payload"]["provider"], "gumroad")
        self.assertEqual(parsed["payload"]["offer_key"], "idea_catalog:offer-product:digital_product")

    def test_build_manual_conversion_payload_rejects_missing_external_id(self):
        with self.assertRaisesRegex(ValueError, "external_id is required"):
            build_manual_conversion_payload(
                provider="manual",
                external_id="",
                amount_usd=10,
                source="manual",
            )


if __name__ == "__main__":
    unittest.main()
