import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.offers import OfferCatalogExporter, generate_offers
from farm_loop.revenue_scoring import RevenueOpportunity, score_opportunity


def opportunity(channel, title="Supabase RLS checker", external_id="opp-1"):
    return score_opportunity(
        RevenueOpportunity(
            source="idea_catalog",
            external_id=external_id,
            title=title,
            url=f"file://ideas#{external_id}",
            problem=f"Builders need {title}.",
            tags=["supabase", "rls"],
            channel=channel,
            payout_estimate_usd=299,
            conversion_probability=0.08,
            estimated_cost_usd=5,
            risk_penalty_usd=1,
            build_minutes=45,
        )
    )


class OfferTests(unittest.TestCase):
    def test_generate_offers_prices_microtool_support_and_service(self):
        offers = generate_offers(opportunity("microtool_seo"))

        self.assertEqual([offer.offer_type for offer in offers], ["support", "setup_service"])
        self.assertEqual(offers[0].price_usd, 5)
        self.assertEqual(offers[1].price_usd, 49)
        self.assertIn("owned channel", offers[0].description)
        self.assertNotIn("Stack Overflow", offers[0].description)

    def test_generate_offers_prices_paid_setup_higher_than_template(self):
        setup = generate_offers(opportunity("paid_setup_kit", "Webhook Setup Service"))[0]
        product = generate_offers(opportunity("digital_product", "OpenAI SaaS Starter Kit"))[0]

        self.assertEqual(setup.offer_type, "fixed_scope_service")
        self.assertGreaterEqual(setup.price_usd, 199)
        self.assertEqual(product.offer_type, "digital_product")
        self.assertLess(product.price_usd, setup.price_usd)

    def test_offer_payload_matches_supabase_shape(self):
        opp = opportunity("microtool_seo", external_id="tool-1")
        offer = generate_offers(opp)[0]

        payload = offer.to_payload(opportunity_id="opp-row-1")

        self.assertEqual(payload["opportunity_id"], "opp-row-1")
        self.assertEqual(payload["channel"], "microtool_seo")
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["payload"]["external_id"], "tool-1")

    def test_offer_catalog_exporter_writes_json_and_markdown(self):
        offers = generate_offers(opportunity("paid_setup_kit", "Webhook Setup Service"))

        with tempfile.TemporaryDirectory() as directory:
            written = OfferCatalogExporter(directory).export(offers)
            root = Path(directory)
            rows = json.loads((root / "offers.json").read_text(encoding="utf-8"))
            markdown = (root / "OFFERS.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["OFFERS.md", "offers.json"])
        self.assertEqual(rows[0]["title"], "Webhook Setup Service")
        self.assertIn("# Offer Catalog", markdown)
        self.assertIn("Webhook Setup Service", markdown)


if __name__ == "__main__":
    unittest.main()
