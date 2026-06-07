import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.checkout_setup import CheckoutSetupExporter, build_checkout_setup_rows
from farm_loop.offers import generate_offers
from farm_loop.revenue_scoring import RevenueOpportunity, score_opportunity


def opportunity(channel="paid_setup_kit", title="Webhook Setup Service", external_id="offer-webhook-setup"):
    return score_opportunity(
        RevenueOpportunity(
            source="idea_catalog",
            external_id=external_id,
            title=title,
            url=f"file://ideas#{external_id}",
            problem=f"Builders need {title}.",
            tags=["stripe", "webhook", "supabase"],
            channel=channel,
            payout_estimate_usd=249,
            conversion_probability=0.08,
            estimated_cost_usd=5,
            risk_penalty_usd=1,
            build_minutes=45,
        )
    )


class CheckoutSetupTests(unittest.TestCase):
    def test_build_checkout_setup_rows_include_provider_metadata_and_webhook_urls(self):
        offer = generate_offers(
            opportunity(),
            payment_urls={"fixed_scope_service": "https://buy.stripe.com/setup"},
        )[0]

        rows = build_checkout_setup_rows(
            [offer],
            conversion_webhook_base_url="https://revenue.example/webhooks/conversion",
            click_redirect_url="https://revenue.example/click",
        )

        self.assertEqual(rows[0]["offer_key"], "idea_catalog:offer-webhook-setup:fixed_scope_service")
        self.assertEqual(rows[0]["payment_url"], "https://buy.stripe.com/setup")
        self.assertEqual(rows[0]["checkout_metadata"]["offer_key"], "idea_catalog:offer-webhook-setup:fixed_scope_service")
        self.assertEqual(rows[0]["checkout_metadata"]["source"], "paid_setup_kit")
        self.assertEqual(rows[0]["provider_webhooks"]["stripe"], "https://revenue.example/webhooks/conversion/stripe")
        self.assertEqual(rows[0]["provider_webhooks"]["manual"], "https://revenue.example/webhooks/conversion/manual")
        self.assertEqual(rows[0]["click_redirect_url"], "https://revenue.example/click")

    def test_checkout_setup_exporter_writes_json_and_markdown(self):
        offers = generate_offers(
            opportunity(),
            payment_urls={"fixed_scope_service": "https://buy.stripe.com/setup"},
        )

        with tempfile.TemporaryDirectory() as directory:
            written = CheckoutSetupExporter(
                directory,
                conversion_webhook_base_url="https://revenue.example/webhooks/conversion",
                click_redirect_url="https://revenue.example/click",
            ).export(offers)
            root = Path(directory)
            rows = json.loads((root / "checkout_setup.json").read_text(encoding="utf-8"))
            markdown = (root / "CHECKOUT_SETUP.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["CHECKOUT_SETUP.md", "checkout_setup.json"])
        self.assertEqual(rows[0]["checkout_metadata"]["ire_offer_key"], "idea_catalog:offer-webhook-setup:fixed_scope_service")
        self.assertIn("# Checkout Setup", markdown)
        self.assertIn("Webhook Setup Service", markdown)
        self.assertIn("offer_key", markdown)
        self.assertIn("https://revenue.example/webhooks/conversion/stripe", markdown)


if __name__ == "__main__":
    unittest.main()
