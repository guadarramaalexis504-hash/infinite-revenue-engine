import tempfile
import unittest
from pathlib import Path

from farm_loop.assets import AssetGenerator
from farm_loop.revenue_scoring import RevenueOpportunity, score_opportunity
from farm_loop.static_site_exporter import StaticSiteExporter


class StaticSiteExporterTests(unittest.TestCase):
    def setUp(self):
        self.opportunity = score_opportunity(
            RevenueOpportunity(
                source="idea_catalog",
                external_id="offer-webhook-setup-service",
                title="Webhook Setup Service",
                url="file://revenue_ideas.json#offer-webhook-setup-service",
                problem="Creators need payment webhooks saved into a database.",
                tags=["webhooks", "stripe", "supabase"],
                channel="paid_setup_kit",
                payout_estimate_usd=199,
                conversion_probability=0.06,
                estimated_cost_usd=5,
                risk_penalty_usd=2,
                build_minutes=50,
            )
        )

    def test_exports_owned_static_site_with_index_opportunity_page_and_support_cta(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            written = StaticSiteExporter(directory, tip_url="https://buymeacoffee.com/example").export_portfolio(
                [(self.opportunity, assets)]
            )
            root = Path(directory)
            index = (root / "index.html").read_text(encoding="utf-8")
            page = (root / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")

        self.assertEqual(len(written), 2)
        self.assertIn("Infinite Revenue Engine", index)
        self.assertIn("Webhook Setup Service", index)
        self.assertIn("offer-webhook-setup-service/", index)
        self.assertIn("payment webhooks saved into a database", page)
        self.assertIn("https://buymeacoffee.com/example?", page)
        self.assertIn("utm_campaign=offer-webhook-setup-service", page)
        self.assertIn("ire_external_id=offer-webhook-setup-service", page)
        self.assertIn("Ways to work with this", page)
        self.assertIn("$199.00", page)
        self.assertIn("Book fixed setup", page)
        self.assertIn("utm_content=fixed_scope_service", page)
        self.assertIn("manual review", page.lower())
        self.assertNotIn("stackoverflow.com", page.lower())

    def test_support_cta_uses_click_redirect_endpoint_when_configured(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            StaticSiteExporter(
                directory,
                tip_url="https://buymeacoffee.com/example",
                click_redirect_url="https://example.com/click",
            ).export_portfolio([(self.opportunity, assets)])
            page = (Path(directory) / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")

        self.assertIn("https://example.com/click?", page)
        self.assertIn("target=https%3A%2F%2Fbuymeacoffee.com%2Fexample", page)
        self.assertIn("opportunity_external_id=offer-webhook-setup-service", page)

    def test_links_to_interactive_tools_when_tools_path_is_configured(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            StaticSiteExporter(directory, tools_path="tools/").export_portfolio([(self.opportunity, assets)])
            root = Path(directory)
            index = (root / "index.html").read_text(encoding="utf-8")
            page = (root / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")

        self.assertIn('href="tools/"', index)
        self.assertIn("Interactive tools", index)
        self.assertIn('href="../tools/"', page)

    def test_offer_cards_show_payment_setup_notice_without_tip_url(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            StaticSiteExporter(directory).export_portfolio([(self.opportunity, assets)])
            page = (Path(directory) / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")

        self.assertIn("Ways to work with this", page)
        self.assertIn("$199.00", page)
        self.assertIn("Configure TIP_URL before publishing offer CTAs", page)


if __name__ == "__main__":
    unittest.main()
