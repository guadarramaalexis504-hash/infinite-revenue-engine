import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.offers import OfferCatalogExporter, generate_offers, parse_offer_payment_urls
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

    def test_generate_offers_creates_sponsorship_for_open_source_repo(self):
        sponsor = generate_offers(
            opportunity("open_source_sponsorship", "GitHub Sponsors README Kit"),
            payment_urls={"sponsorship": "https://github.com/sponsors/example"},
        )[0]

        self.assertEqual(sponsor.offer_type, "sponsorship")
        self.assertEqual(sponsor.payment_url, "https://github.com/sponsors/example")
        self.assertIn("Sponsor", sponsor.title)

    def test_offer_payload_matches_supabase_shape(self):
        opp = opportunity("microtool_seo", external_id="tool-1")
        offer = generate_offers(
            opp,
            payment_urls={"support": "https://buymeacoffee.com/example", "setup_service": "https://buy.stripe.com/setup"},
        )[0]

        payload = offer.to_payload(opportunity_id="opp-row-1")

        self.assertEqual(offer.offer_key, "idea_catalog:tool-1:support")
        self.assertEqual(payload["opportunity_id"], "opp-row-1")
        self.assertEqual(payload["channel"], "microtool_seo")
        self.assertEqual(payload["payment_url"], "https://buymeacoffee.com/example")
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["payload"]["offer_key"], "idea_catalog:tool-1:support")
        self.assertEqual(payload["payload"]["external_id"], "tool-1")

    def test_parse_offer_payment_urls_accepts_offer_types_channels_and_default(self):
        payment_urls = parse_offer_payment_urls(
            "support=https://buymeacoffee.com/example,"
            "fixed_scope_service=https://buy.stripe.com/setup,"
            "digital_product=https://gumroad.com/l/template,"
            "github_issue_helper=https://github.com/sponsors/example,"
            "*=https://example.com/pay"
        )

        self.assertEqual(payment_urls["support"], "https://buymeacoffee.com/example")
        self.assertEqual(payment_urls["fixed_scope_service"], "https://buy.stripe.com/setup")
        self.assertEqual(payment_urls["digital_product"], "https://gumroad.com/l/template")
        self.assertEqual(payment_urls["github_issue_helper"], "https://github.com/sponsors/example")
        self.assertEqual(payment_urls["*"], "https://example.com/pay")

    def test_generate_offers_applies_payment_url_by_offer_type_then_channel_default(self):
        support, setup = generate_offers(
            opportunity("microtool_seo"),
            payment_urls={
                "support": "https://buymeacoffee.com/example",
                "microtool_seo": "https://stripe.example.com/microtool",
                "*": "https://example.com/pay",
            },
        )
        product = generate_offers(
            opportunity("digital_product", "Template Pack"),
            payment_urls={"*": "https://example.com/pay"},
        )[0]

        self.assertEqual(support.payment_url, "https://buymeacoffee.com/example")
        self.assertEqual(setup.payment_url, "https://stripe.example.com/microtool")
        self.assertEqual(product.payment_url, "https://example.com/pay")

    def test_offer_catalog_exporter_writes_json_and_markdown(self):
        offers = generate_offers(
            opportunity("paid_setup_kit", "Webhook Setup Service"),
            payment_urls={"fixed_scope_service": "https://buy.stripe.com/webhook-setup"},
        )

        with tempfile.TemporaryDirectory() as directory:
            written = OfferCatalogExporter(directory).export(offers)
            root = Path(directory)
            rows = json.loads((root / "offers.json").read_text(encoding="utf-8"))
            markdown = (root / "OFFERS.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["OFFERS.md", "offers.json"])
        self.assertEqual(rows[0]["title"], "Webhook Setup Service")
        self.assertEqual(rows[0]["offer_key"], "idea_catalog:opp-1:fixed_scope_service")
        self.assertEqual(rows[0]["payment_url"], "https://buy.stripe.com/webhook-setup")
        self.assertIn("# Offer Catalog", markdown)
        self.assertIn("Webhook Setup Service", markdown)
        self.assertIn("idea_catalog:opp-1:fixed_scope_service", markdown)
        self.assertIn("https://buy.stripe.com/webhook-setup", markdown)


if __name__ == "__main__":
    unittest.main()
