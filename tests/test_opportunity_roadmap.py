import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.opportunity_roadmap import OpportunityRoadmapExporter, build_opportunity_roadmap
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(
    external_id: str,
    *,
    title: str,
    channel: str,
    payout: float,
    probability: float,
    build_minutes: int = 45,
) -> RevenueOpportunity:
    return RevenueOpportunity(
        source="idea_catalog",
        external_id=external_id,
        title=title,
        url=f"file://ideas#{external_id}",
        problem=f"{title} solves a recurring paid problem.",
        tags=[channel, "revenue"],
        channel=channel,
        payout_estimate_usd=payout,
        conversion_probability=probability,
        estimated_cost_usd=5,
        risk_penalty_usd=1,
        build_minutes=build_minutes,
    )


class OpportunityRoadmapTests(unittest.TestCase):
    def test_build_opportunity_roadmap_ranks_all_ideas_and_groups_channels(self):
        opportunities = [
            make_opportunity(
                "setup-kit",
                title="Supabase setup kit",
                channel="paid_setup_kit",
                payout=299,
                probability=0.06,
            ),
            make_opportunity(
                "rls-tool",
                title="Supabase RLS checker",
                channel="microtool_seo",
                payout=300,
                probability=0.08,
            ),
            make_opportunity(
                "template-pack",
                title="FastAPI template pack",
                channel="digital_product",
                payout=99,
                probability=0.08,
                build_minutes=30,
            ),
        ]

        roadmap = build_opportunity_roadmap(
            discovered=opportunities,
            selected=opportunities[:2],
            milestones=[15, 200, 1000, 20000],
            activation_report={"ready": False, "next_actions": ["Add git remote origin"]},
        )

        self.assertEqual(roadmap["total_discovered"], 3)
        self.assertEqual(roadmap["total_ranked"], 3)
        self.assertEqual(roadmap["activation_blockers"], ["Add git remote origin"])
        self.assertEqual(roadmap["backlog"][0]["external_id"], "rls-tool")
        self.assertEqual(roadmap["backlog"][0]["channel"], "microtool_seo")
        self.assertEqual(roadmap["channel_summary"][0]["channel"], "microtool_seo")
        self.assertEqual(roadmap["milestone_plan"][-1]["milestone_usd"], 20000)
        self.assertGreaterEqual(roadmap["milestone_plan"][-1]["required_units_estimate"], 1)
        self.assertIn("Fix activation blockers", roadmap["recommended_next_actions"][0])

    def test_opportunity_roadmap_exporter_writes_json_and_markdown_for_all_ideas(self):
        opportunities = [
            make_opportunity("rls-tool", title="Supabase RLS checker", channel="microtool_seo", payout=300, probability=0.08),
            make_opportunity("setup-kit", title="Supabase setup kit", channel="paid_setup_kit", payout=299, probability=0.06),
        ]

        with tempfile.TemporaryDirectory() as directory:
            written = OpportunityRoadmapExporter(directory).export(
                discovered=opportunities,
                selected=opportunities[:1],
                milestones=[15, 200, 1000, 20000],
                activation_report={"ready": False, "next_actions": ["Run gh auth login"]},
            )
            root = Path(directory)
            data = json.loads((root / "opportunity_roadmap.json").read_text(encoding="utf-8"))
            markdown = (root / "OPPORTUNITY_ROADMAP.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["OPPORTUNITY_ROADMAP.md", "opportunity_roadmap.json"])
        self.assertEqual(data["total_discovered"], 2)
        self.assertIn("Supabase RLS checker", markdown)
        self.assertIn("Supabase setup kit", markdown)
        self.assertIn("Activation Blockers", markdown)
        self.assertIn("$20,000", markdown)
        self.assertIn("All Ranked Ideas", markdown)


if __name__ == "__main__":
    unittest.main()
