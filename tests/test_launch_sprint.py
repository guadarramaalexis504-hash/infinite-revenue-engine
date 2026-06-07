import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.launch_sprint import LaunchSprintExporter, build_launch_sprint
from farm_loop.offers import OfferDraft
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(
    *,
    channel="microtool_seo",
    external_id="supabase-rls-checker",
    title="Supabase RLS policy checker",
):
    return RevenueOpportunity(
        source="manual_keywords",
        external_id=external_id,
        title=title,
        url=f"file://keywords.csv#{external_id}",
        problem="Developers need a quick way to review RLS mistakes before launch.",
        tags=["supabase", "rls"],
        channel=channel,
        payout_estimate_usd=300,
        conversion_probability=0.08,
        estimated_cost_usd=5,
        risk_penalty_usd=1,
        build_minutes=45,
        expected_value_usd=20.5,
    )


def make_offer(
    *,
    offer_type="setup_service",
    price_usd=49,
    payment_url="",
):
    return OfferDraft(
        source="manual_keywords",
        external_id="supabase-rls-checker",
        channel="microtool_seo",
        offer_type=offer_type,
        offer_key=f"manual_keywords:supabase-rls-checker:{offer_type}",
        title="Supabase RLS policy checker setup help",
        description="Apply the checker to a real Supabase project.",
        price_usd=price_usd,
        cta_label="Get setup help",
        payment_url=payment_url,
    )


class LaunchSprintTests(unittest.TestCase):
    def test_build_launch_sprint_turns_blockers_and_offers_into_30_day_plan(self):
        sprint = build_launch_sprint(
            opportunities=[make_opportunity()],
            offers=[
                make_offer(offer_type="support", price_usd=5),
                make_offer(offer_type="setup_service", price_usd=49),
            ],
            milestones=[15, 200, 1000, 20000],
            activation_report={
                "ready": False,
                "next_actions": [
                    "Replace placeholder .env values: SUPABASE_KEY",
                    "Run gh auth login",
                ],
            },
        )

        self.assertFalse(sprint["automation_ready"])
        self.assertEqual(sprint["milestones"], [15.0, 200.0, 1000.0, 20000.0])
        self.assertEqual(sprint["top_milestone_usd"], 20000.0)
        self.assertIn("Replace placeholder .env values", sprint["activation_blockers"][0])
        self.assertEqual(sprint["launch_tracks"][0]["external_id"], "supabase-rls-checker")
        self.assertEqual(sprint["launch_tracks"][0]["best_offer"]["offer_type"], "setup_service")
        self.assertEqual(sprint["launch_tracks"][0]["best_offer"]["units_to_top_milestone"], 409)
        self.assertEqual(
            [phase["phase"] for phase in sprint["plan"]],
            ["activate", "publish", "first_sales", "measure", "scale_or_prune"],
        )
        self.assertTrue(any("checkout" in action.lower() for action in sprint["plan"][0]["actions"]))
        self.assertTrue(any("owned" in guardrail.lower() for guardrail in sprint["guardrails"]))
        self.assertIn("does not guarantee income", sprint["automation_answer"].lower())

    def test_exporter_writes_json_and_markdown_for_claude_or_manual_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "launch-sprint"
            exporter = LaunchSprintExporter(output_dir)

            written = exporter.export(
                opportunities=[make_opportunity()],
                offers=[make_offer(payment_url="https://buy.stripe.com/test")],
                milestones=[15, 200, 1000, 20000],
                activation_report={"ready": True, "next_actions": []},
            )
            sprint = json.loads((output_dir / "launch_sprint.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "30_DAY_LAUNCH_PLAN.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["30_DAY_LAUNCH_PLAN.md", "launch_sprint.json"])
        self.assertTrue(sprint["automation_ready"])
        self.assertIn("# 30 Day Launch Plan", markdown)
        self.assertIn("$20,000", markdown)
        self.assertIn("Supabase RLS policy checker", markdown)
        self.assertIn("No third-party autoposting", markdown)

    def test_build_launch_sprint_prioritizes_lower_volume_revenue_paths(self):
        low_ticket = make_opportunity(
            channel="open_source_sponsorship",
            external_id="repo-sponsor",
            title="Sponsor-only repo helper",
        )
        high_ticket = make_opportunity(
            channel="microtool_seo",
            external_id="supabase-rls-checker",
            title="Supabase RLS policy checker",
        )

        sprint = build_launch_sprint(
            opportunities=[low_ticket, high_ticket],
            offers=[
                OfferDraft(
                    source="manual_keywords",
                    external_id="repo-sponsor",
                    channel="open_source_sponsorship",
                    offer_type="sponsorship",
                    offer_key="manual_keywords:repo-sponsor:sponsorship",
                    title="Sponsor repo helper",
                    description="Small sponsorship CTA.",
                    price_usd=5,
                    cta_label="Sponsor",
                ),
                make_offer(offer_type="setup_service", price_usd=49),
            ],
            milestones=[20000],
            activation_report={"ready": True, "next_actions": []},
        )

        self.assertEqual(sprint["launch_tracks"][0]["external_id"], "supabase-rls-checker")
        self.assertEqual(sprint["launch_tracks"][0]["best_offer"]["units_to_top_milestone"], 409)
        self.assertEqual(sprint["launch_tracks"][1]["best_offer"]["units_to_top_milestone"], 4000)


if __name__ == "__main__":
    unittest.main()
