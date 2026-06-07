import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.offer_ladder import OfferLadderExporter, build_offer_ladder
from farm_loop.offers import OfferDraft


def make_offer(
    *,
    offer_type="setup_service",
    channel="microtool_seo",
    price_usd=49,
):
    return OfferDraft(
        source="manual_keywords",
        external_id="microtool-supabase-rls",
        channel=channel,
        offer_type=offer_type,
        offer_key=f"manual_keywords:microtool-supabase-rls:{offer_type}",
        title="Supabase RLS policy checker setup help",
        description="Apply the checker to a real Supabase project.",
        price_usd=price_usd,
        cta_label="Get setup help",
        payment_url="",
    )


class OfferLadderTests(unittest.TestCase):
    def test_build_offer_ladder_adds_high_ticket_tiers_and_unit_targets(self):
        ladder = build_offer_ladder(
            offers=[
                make_offer(offer_type="support", price_usd=5),
                make_offer(offer_type="setup_service", price_usd=49),
            ],
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(ladder["milestones"], [15.0, 200.0, 1000.0, 20000.0])
        self.assertEqual(ladder["totals"]["ladders"], 1)
        self.assertEqual(ladder["best_path"]["tier_price_usd"], 999.0)
        self.assertEqual(ladder["best_path"]["units_to_top_milestone"], 21)
        tiers = ladder["ladders"][0]["tiers"]
        self.assertEqual([tier["tier_type"] for tier in tiers], ["support_signal", "starter_setup", "fixed_scope_service", "premium_sprint"])
        self.assertEqual(tiers[-1]["unit_targets"]["20000"], 21)
        self.assertIn("delivery capacity", tiers[-1]["activation_notes"][0])
        top_mix = ladder["ladders"][0]["mix_plans"][-1]
        self.assertEqual(top_mix["milestone_usd"], 20000.0)
        self.assertEqual(top_mix["strategy"], "premium_then_fixed")
        self.assertEqual(top_mix["tiers"][0]["tier_type"], "premium_sprint")
        self.assertEqual(top_mix["tiers"][0]["units"], 5)
        self.assertEqual(top_mix["tiers"][1]["tier_type"], "fixed_scope_service")
        self.assertEqual(top_mix["tiers"][1]["units"], 51)
        self.assertGreaterEqual(top_mix["total_revenue_usd"], 20000)

    def test_exporter_writes_json_and_markdown_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "offer-ladder"
            exporter = OfferLadderExporter(output_dir)

            written = exporter.export(
                offers=[make_offer(offer_type="setup_service", price_usd=49)],
                milestones=[15, 200, 1000, 20000],
            )
            ladder = json.loads((output_dir / "offer_ladder.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "OFFER_LADDER.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["OFFER_LADDER.md", "offer_ladder.json"])
        self.assertEqual(ladder["best_path"]["units_to_top_milestone"], 21)
        self.assertIn("$999", markdown)
        self.assertIn("$20,000", markdown)
        self.assertIn("Premium + fixed service mix", markdown)
        self.assertIn("5 x premium_sprint", markdown)
        self.assertIn("Supabase RLS policy checker setup help", markdown)


if __name__ == "__main__":
    unittest.main()
