import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.all_ideas_catalog import AllIdeasCatalogExporter, build_all_ideas_catalog
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(
    *,
    external_id="microtool-supabase-rls",
    title="Supabase RLS Policy Checker",
    channel="microtool_seo",
    payout=300,
    probability=0.08,
    build_minutes=45,
):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id=external_id,
        title=title,
        url=f"file://revenue_ideas.json#{external_id}",
        problem="Builders need a practical revenue asset.",
        tags=["supabase", "automation"],
        channel=channel,
        payout_estimate_usd=payout,
        conversion_probability=probability,
        estimated_cost_usd=5,
        risk_penalty_usd=1,
        build_minutes=build_minutes,
    )


class AllIdeasCatalogTests(unittest.TestCase):
    def test_build_all_ideas_catalog_ranks_every_idea_and_groups_channels(self):
        catalog = build_all_ideas_catalog(
            ideas=[
                make_opportunity(),
                make_opportunity(
                    external_id="setup-kit",
                    title="Supabase + GitHub Actions Setup Kit",
                    channel="paid_setup_kit",
                    payout=299,
                    probability=0.15,
                    build_minutes=90,
                ),
                make_opportunity(
                    external_id="affiliate-article",
                    title="FastAPI hosting comparison",
                    channel="article_affiliate",
                    payout=120,
                    probability=0.05,
                    build_minutes=50,
                ),
            ],
            selected_external_ids={"microtool-supabase-rls"},
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(catalog["total_ideas"], 3)
        self.assertEqual(catalog["milestones"], [15.0, 200.0, 1000.0, 20000.0])
        self.assertEqual(catalog["ideas"][0]["external_id"], "setup-kit")
        self.assertTrue(catalog["ideas"][1]["selected_this_run"])
        self.assertEqual(catalog["channel_summary"][0]["channel"], "paid_setup_kit")
        self.assertIn("fixed-scope service", catalog["ideas"][0]["monetization_path"])
        self.assertTrue(any("No third-party autoposting" in guardrail for guardrail in catalog["guardrails"]))

    def test_exporter_writes_json_and_markdown_for_all_revenue_ideas(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "all-ideas"
            exporter = AllIdeasCatalogExporter(output_dir)

            written = exporter.export(
                ideas=[make_opportunity()],
                selected_external_ids={"microtool-supabase-rls"},
                milestones=[15, 200, 1000, 20000],
            )
            catalog = json.loads((output_dir / "all_revenue_ideas.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "ALL_REVENUE_IDEAS.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["ALL_REVENUE_IDEAS.md", "all_revenue_ideas.json"])
        self.assertEqual(catalog["total_ideas"], 1)
        self.assertIn("# All Revenue Ideas", markdown)
        self.assertIn("Supabase RLS Policy Checker", markdown)
        self.assertIn("$20,000", markdown)
        self.assertIn("No third-party autoposting", markdown)


if __name__ == "__main__":
    unittest.main()
