import json
import unittest

from farm_loop.offers import OfferDraft
from farm_loop.stripe_links import StripeLinkBuilder, build_offer_payment_urls_string


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def offer(offer_key, price, offer_type="setup_service", channel="microtool_seo"):
    return OfferDraft(
        source="idea_catalog",
        external_id="x",
        channel=channel,
        title=f"Offer {offer_key}",
        price_usd=price,
        offer_type=offer_type,
        offer_key=offer_key,
        description="desc",
        cta_label="Buy",
    )


class StripeLinkBuilderTests(unittest.TestCase):
    def test_disabled_without_secret_key(self):
        calls = []
        b = StripeLinkBuilder(secret_key=None, opener=lambda req, timeout: calls.append(req))
        self.assertFalse(b.enabled)
        self.assertEqual(b.create_for_offers([offer("a:b:setup_service", 49)]), {})
        self.assertEqual(calls, [])

    def test_disabled_for_placeholder_key(self):
        b = StripeLinkBuilder(secret_key="sk_test_your-key-here")
        self.assertFalse(b.enabled)

    def test_skips_free_and_support_offers(self):
        calls = []
        b = StripeLinkBuilder(secret_key="sk_live_realkey123456", opener=lambda req, timeout: calls.append(req))
        result = b.create_for_offers([
            offer("a:b:support", 0, offer_type="support"),
            offer("a:b:sponsorship", 0, offer_type="sponsorship"),
        ])
        self.assertEqual(result, {})
        self.assertEqual(calls, [])

    def test_creates_product_price_and_payment_link_with_metadata(self):
        seq = [
            FakeResp({"id": "prod_1"}),
            FakeResp({"id": "price_1"}),
            FakeResp({"id": "plink_1", "url": "https://buy.stripe.com/test_123"}),
        ]
        captured = []

        def opener(req, timeout):
            captured.append((req.full_url, req.data.decode("utf-8"), dict(req.header_items())))
            return seq.pop(0)

        b = StripeLinkBuilder(secret_key="sk_live_realkey123456", opener=opener)
        result = b.create_for_offers([offer("kw:tool:setup_service", 199)])

        self.assertEqual(result, {"kw:tool:setup_service": "https://buy.stripe.com/test_123"})
        # product, price, payment_link = 3 calls
        self.assertEqual(len(captured), 3)
        # Auth header carries the secret as bearer
        self.assertIn("Bearer sk_live_realkey123456", captured[0][2].get("Authorization", ""))
        # price is in cents
        self.assertIn("unit_amount=19900", captured[1][1])
        # payment link carries offer_key in metadata for webhook attribution
        self.assertIn("metadata%5Boffer_key%5D=kw%3Atool%3Asetup_service", captured[2][1])

    def test_one_offer_failure_does_not_kill_the_batch(self):
        # First offer: product call raises; second offer succeeds.
        state = {"calls": 0}

        def opener(req, timeout):
            state["calls"] += 1
            if "/products" in req.full_url and state["calls"] == 1:
                raise OSError("stripe down")
            if "/products" in req.full_url:
                return FakeResp({"id": "prod_2"})
            if "/prices" in req.full_url:
                return FakeResp({"id": "price_2"})
            return FakeResp({"id": "plink_2", "url": "https://buy.stripe.com/ok"})

        b = StripeLinkBuilder(secret_key="sk_live_realkey123456", opener=opener)
        result = b.create_for_offers([offer("a:1:setup_service", 49), offer("b:2:digital_product", 19, offer_type="digital_product")])
        self.assertEqual(result, {"b:2:digital_product": "https://buy.stripe.com/ok"})

    def test_build_offer_payment_urls_string_round_trips(self):
        mapping = {
            "kw:tool:setup_service": "https://buy.stripe.com/a",
            "kw:tool:digital_product": "https://buy.stripe.com/b",
        }
        s = build_offer_payment_urls_string(mapping)
        self.assertIn("setup_service=https://buy.stripe.com/a", s)
        self.assertIn("digital_product=https://buy.stripe.com/b", s)


if __name__ == "__main__":
    unittest.main()
