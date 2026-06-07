import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.niche_report_exporter import NicheReportExporter, build_niche_report_rows
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(channel="niche_report"):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id="niche-report-local-ai-tools",
        title="Local AI Tools Niche Report",
        url="https://example.com/idea",
        problem="Builders and affiliate marketers need a report on emerging local AI tool keywords.",
        tags=["seo", "ai", "niche-report"],
        channel=channel,
        payout_estimate_usd=220,
        conversion_probability=0.05,
        estimated_cost_usd=4,
        risk_penalty_usd=1,
        build_minutes=45,
        expected_value_usd=6.0,
    )


class NicheReportExporterTests(unittest.TestCase):
    def test_build_rows_filters_niche_reports_and_tracks_checkout(self):
        rows = build_niche_report_rows(
            [make_opportunity(), make_opportunity(channel="article_affiliate")],
            payment_urls={"paid_report": "https://gumroad.com/l/report"},
            click_redirect_url="https://track.example.com/click",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["slug"], "niche-report-local-ai-tools")
        self.assertEqual(rows[0]["offer_key"], "idea_catalog:niche-report-local-ai-tools:paid_report")
        self.assertEqual(rows[0]["price_usd"], 19.0)
        self.assertIn("target=https%3A%2F%2Fgumroad.com%2Fl%2Freport", rows[0]["checkout_url"])
        self.assertIn("keyword clusters", rows[0]["report_sections"][0].lower())
        self.assertIn("Do not claim market size", rows[0]["review_gate"])

    def test_exporter_writes_report_catalog_report_and_landing_page(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = NicheReportExporter(
                Path(directory) / "niche-reports",
                payment_urls={"paid_report": "https://gumroad.com/l/report"},
                click_redirect_url="https://track.example.com/click",
            )

            paths = exporter.export([make_opportunity()])

            output_dir = Path(directory) / "niche-reports"
            manifest = json.loads((output_dir / "niche_reports.json").read_text(encoding="utf-8"))
            catalog = (output_dir / "NICHE_REPORTS.md").read_text(encoding="utf-8")
            report_dir = output_dir / "niche-report-local-ai-tools"
            report = (report_dir / "REPORT.md").read_text(encoding="utf-8")
            listing = (report_dir / "STORE_LISTING.md").read_text(encoding="utf-8")
            validation = (report_dir / "VALIDATION_PLAN.md").read_text(encoding="utf-8")
            page = (report_dir / "index.html").read_text(encoding="utf-8")

        self.assertIn("niche_reports.json", [path.name for path in paths])
        self.assertEqual(manifest[0]["title"], "Local AI Tools Niche Report")
        self.assertIn("# Niche Reports", catalog)
        self.assertIn("Keyword clusters", report)
        self.assertIn("Store Listing", listing)
        self.assertIn("Validation Plan", validation)
        self.assertIn("https://track.example.com/click", page)


if __name__ == "__main__":
    unittest.main()
