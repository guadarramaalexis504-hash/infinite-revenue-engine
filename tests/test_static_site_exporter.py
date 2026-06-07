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
            written = StaticSiteExporter(
                directory,
                tip_url="https://buymeacoffee.com/example",
                site_base_url="https://revenue.example",
            ).export_portfolio([(self.opportunity, assets)])
            root = Path(directory)
            index = (root / "index.html").read_text(encoding="utf-8")
            page = (root / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")
            offer_catalog = (root / "offers" / "index.html").read_text(encoding="utf-8")
            intake = (root / "intake" / "index.html").read_text(encoding="utf-8")
            sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
            robots = (root / "robots.txt").read_text(encoding="utf-8")

        self.assertEqual(len(written), 6)
        self.assertIn("Infinite Revenue Engine", index)
        self.assertIn("Webhook Setup Service", index)
        self.assertIn("offer-webhook-setup-service/", index)
        self.assertIn('href="offers/"', index)
        self.assertIn('href="intake/"', index)
        self.assertIn('href="../offers/"', page)
        self.assertIn('href="../intake/"', page)
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
        self.assertIn("Offer Catalog", offer_catalog)
        self.assertIn("Webhook Setup Service", offer_catalog)
        self.assertIn("$199.00", offer_catalog)
        self.assertIn("Book fixed setup", offer_catalog)
        self.assertIn("utm_content=fixed_scope_service", offer_catalog)
        self.assertIn('href="../offer-webhook-setup-service/"', offer_catalog)
        self.assertIn("Setup Intake", intake)
        self.assertIn("Webhook Setup Service", intake)
        self.assertIn("Scope", intake)
        self.assertIn("Configure SERVICE_INTAKE_URL before publishing intake CTAs", intake)
        self.assertIn("<loc>https://revenue.example/</loc>", sitemap)
        self.assertIn("<loc>https://revenue.example/offers/</loc>", sitemap)
        self.assertIn("<loc>https://revenue.example/intake/</loc>", sitemap)
        self.assertIn("<loc>https://revenue.example/offer-webhook-setup-service/</loc>", sitemap)
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertIn("Sitemap: https://revenue.example/sitemap.xml", robots)

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

    def test_service_offers_use_intake_url_when_configured(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            StaticSiteExporter(
                directory,
                intake_url="https://forms.example.com/setup",
            ).export_portfolio([(self.opportunity, assets)])
            root = Path(directory)
            page = (root / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")
            offer_catalog = (root / "offers" / "index.html").read_text(encoding="utf-8")
            intake = (root / "intake" / "index.html").read_text(encoding="utf-8")

        self.assertIn("https://forms.example.com/setup?", page)
        self.assertIn("utm_content=fixed_scope_service_intake", page)
        self.assertIn("https://forms.example.com/setup?", offer_catalog)
        self.assertIn("utm_content=fixed_scope_service_intake", offer_catalog)
        self.assertIn("https://forms.example.com/setup?", intake)
        self.assertIn("utm_content=intake", intake)

    def test_offer_payment_urls_override_tip_and_intake_with_click_tracking(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            StaticSiteExporter(
                directory,
                tip_url="https://buymeacoffee.com/example",
                intake_url="https://forms.example.com/setup",
                click_redirect_url="https://revenue.example/click",
                offer_payment_urls={"fixed_scope_service": "https://buy.stripe.com/webhook-setup"},
            ).export_portfolio([(self.opportunity, assets)])
            root = Path(directory)
            page = (root / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")
            offer_catalog = (root / "offers" / "index.html").read_text(encoding="utf-8")

        self.assertIn("https://revenue.example/click?", page)
        self.assertIn("target=https%3A%2F%2Fbuy.stripe.com%2Fwebhook-setup", page)
        self.assertIn("utm_content%3Dfixed_scope_service", page)
        self.assertIn("ire_offer_key%3Didea_catalog%253Aoffer-webhook-setup-service%253Afixed_scope_service", page)
        self.assertIn("offer_key=idea_catalog%3Aoffer-webhook-setup-service%3Afixed_scope_service", page)
        self.assertIn("target=https%3A%2F%2Fbuy.stripe.com%2Fwebhook-setup", offer_catalog)
        self.assertNotIn("fixed_scope_service_intake", page)

    def test_offer_cards_show_payment_setup_notice_without_tip_url(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            StaticSiteExporter(directory).export_portfolio([(self.opportunity, assets)])
            page = (Path(directory) / "offer-webhook-setup-service" / "index.html").read_text(encoding="utf-8")
            offer_catalog = (Path(directory) / "offers" / "index.html").read_text(encoding="utf-8")

        self.assertIn("Ways to work with this", page)
        self.assertIn("$199.00", page)
        self.assertIn("Configure TIP_URL or OFFER_PAYMENT_URLS before publishing offer CTAs", page)
        self.assertIn("Offer Catalog", offer_catalog)
        self.assertIn("Configure TIP_URL or OFFER_PAYMENT_URLS before publishing offer CTAs", offer_catalog)


if __name__ == "__main__":
    unittest.main()
