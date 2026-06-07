import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.digital_product_exporter import DigitalProductExporter, build_digital_product_rows
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(channel="digital_product"):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id="template-fastapi-supabase-auth",
        title="FastAPI Supabase Auth Template",
        url="https://example.com/idea",
        problem="Python developers need a clean auth template using Supabase without leaking service keys.",
        tags=["fastapi", "supabase", "auth", "template"],
        channel=channel,
        payout_estimate_usd=99,
        conversion_probability=0.07,
        estimated_cost_usd=5,
        risk_penalty_usd=1,
        build_minutes=50,
        expected_value_usd=2.43,
    )


class DigitalProductExporterTests(unittest.TestCase):
    def test_build_rows_filters_products_and_tracks_checkout_url(self):
        rows = build_digital_product_rows(
            [make_opportunity(), make_opportunity(channel="microtool_seo")],
            payment_urls={"digital_product": "https://gumroad.com/l/template"},
            click_redirect_url="https://track.example.com/click",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["offer_key"], "idea_catalog:template-fastapi-supabase-auth:digital_product")
        self.assertEqual(rows[0]["price_usd"], 29.0)
        self.assertIn("target=https%3A%2F%2Fgumroad.com%2Fl%2Ftemplate", rows[0]["checkout_url"])
        self.assertEqual(rows[0]["status"], "review")
        self.assertGreaterEqual(len(rows[0]["included_files"]), 4)

    def test_exporter_writes_catalog_and_product_pack_files(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = DigitalProductExporter(
                Path(directory) / "digital-products",
                payment_urls={"digital_product": "https://gumroad.com/l/template"},
                click_redirect_url="https://track.example.com/click",
            )

            paths = exporter.export([make_opportunity()])

            output_dir = Path(directory) / "digital-products"
            manifest = json.loads((output_dir / "digital_products.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "DIGITAL_PRODUCTS.md").read_text(encoding="utf-8")
            product_dir = output_dir / "template-fastapi-supabase-auth"
            readme = (product_dir / "README.md").read_text(encoding="utf-8")
            listing = (product_dir / "STORE_LISTING.md").read_text(encoding="utf-8")
            checklist = (product_dir / "LAUNCH_CHECKLIST.md").read_text(encoding="utf-8")
            package_json = json.loads((product_dir / "product.json").read_text(encoding="utf-8"))

        self.assertIn("digital_products.json", [path.name for path in paths])
        self.assertEqual(manifest[0]["title"], "FastAPI Supabase Auth Template")
        self.assertIn("# Digital Products", markdown)
        self.assertIn("# FastAPI Supabase Auth Template", readme)
        self.assertIn("## Store Listing", listing)
        self.assertIn("Set checkout metadata", checklist)
        self.assertEqual(package_json["offer_key"], "idea_catalog:template-fastapi-supabase-auth:digital_product")


if __name__ == "__main__":
    unittest.main()
