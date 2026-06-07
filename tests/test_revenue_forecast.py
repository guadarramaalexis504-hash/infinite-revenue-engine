import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.offers import OfferDraft
from farm_loop.revenue_forecast import RevenueForecastExporter, build_revenue_forecast


def make_offer(
    *,
    offer_type="fixed_scope_service",
    channel="paid_setup_kit",
    price_usd=299,
    payment_url="https://buy.stripe.com/setup",
):
    return OfferDraft(
        source="idea_catalog",
        external_id=f"{channel}-{offer_type}",
        channel=channel,
        offer_type=offer_type,
        offer_key=f"idea_catalog:{channel}-{offer_type}:{offer_type}",
        title="Supabase setup service",
        description="Fixed-scope setup service.",
        price_usd=price_usd,
        cta_label="Book setup",
        payment_url=payment_url,
    )


class RevenueForecastTests(unittest.TestCase):
    def test_build_revenue_forecast_counts_units_needed_by_offer_and_milestone(self):
        forecast = build_revenue_forecast(
            offers=[
                make_offer(price_usd=299),
                make_offer(offer_type="support", channel="microtool_seo", price_usd=5, payment_url=""),
            ],
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(forecast["milestones"], [15.0, 200.0, 1000.0, 20000.0])
        self.assertEqual(forecast["best_offer"]["price_usd"], 299.0)
        self.assertEqual(forecast["best_offer"]["units_to_top_milestone"], 67)
        self.assertEqual(forecast["totals"]["payment_configured_offers"], 1)
        self.assertEqual(forecast["totals"]["unconfigured_offers"], 1)
        self.assertEqual(forecast["offers"][0]["milestone_units"]["20000"], 67)
        self.assertEqual(forecast["offers"][1]["milestone_units"]["20000"], 4000)
        self.assertIn("Connect payment URL", forecast["offers"][1]["activation_notes"][0])

    def test_exporter_writes_json_and_markdown_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "forecast"
            exporter = RevenueForecastExporter(output_dir)

            written = exporter.export(
                offers=[make_offer(price_usd=299)],
                milestones=[15, 200, 1000, 20000],
            )
            forecast = json.loads((output_dir / "revenue_forecast.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "REVENUE_FORECAST.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["REVENUE_FORECAST.md", "revenue_forecast.json"])
        self.assertEqual(forecast["offers"][0]["milestone_units"]["20000"], 67)
        self.assertIn("67", markdown)
        self.assertIn("$20,000", markdown)
        self.assertIn("Supabase setup service", markdown)


if __name__ == "__main__":
    unittest.main()
