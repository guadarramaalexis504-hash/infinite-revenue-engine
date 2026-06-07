import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.lead_magnet_exporter import LeadMagnetExporter, build_lead_magnet_rows
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(channel="lead_magnet"):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id="leadmagnet-supabase-production-checklist",
        title="Supabase production checklist",
        url="https://example.com/idea",
        problem="Supabase users need a pre-launch checklist for RLS, backups, auth, and keys.",
        tags=["supabase", "checklist", "launch"],
        channel=channel,
        payout_estimate_usd=120,
        conversion_probability=0.08,
        estimated_cost_usd=3,
        risk_penalty_usd=1,
        build_minutes=35,
        expected_value_usd=5.6,
    )


class LeadMagnetExporterTests(unittest.TestCase):
    def test_build_rows_filters_lead_magnets_and_adds_tracked_opt_in_url(self):
        rows = build_lead_magnet_rows(
            [make_opportunity(), make_opportunity(channel="microtool_seo")],
            lead_capture_url="https://forms.example.com/signup",
            click_redirect_url="https://track.example.com/click",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["external_id"], "leadmagnet-supabase-production-checklist")
        self.assertEqual(rows[0]["slug"], "leadmagnet-supabase-production-checklist")
        self.assertIn("target=https%3A%2F%2Fforms.example.com%2Fsignup", rows[0]["opt_in_url"])
        self.assertEqual(rows[0]["status"], "review")
        self.assertGreaterEqual(len(rows[0]["checklist_items"]), 8)

    def test_exporter_writes_index_json_markdown_and_download_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = LeadMagnetExporter(
                Path(directory) / "lead-magnets",
                lead_capture_url="https://forms.example.com/signup",
                click_redirect_url="https://track.example.com/click",
            )

            paths = exporter.export([make_opportunity()])

            output_dir = Path(directory) / "lead-magnets"
            manifest = json.loads((output_dir / "lead_magnets.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "LEAD_MAGNETS.md").read_text(encoding="utf-8")
            landing = (output_dir / "leadmagnet-supabase-production-checklist" / "index.html").read_text(encoding="utf-8")
            checklist = (output_dir / "leadmagnet-supabase-production-checklist" / "checklist.md").read_text(encoding="utf-8")

        self.assertIn("lead_magnets.json", [path.name for path in paths])
        self.assertEqual(manifest[0]["title"], "Supabase production checklist")
        self.assertIn("# Lead Magnets", markdown)
        self.assertIn("Supabase production checklist", landing)
        self.assertIn("Get the checklist", landing)
        self.assertIn("# Supabase production checklist", checklist)
        self.assertIn("Review RLS policies", checklist)


if __name__ == "__main__":
    unittest.main()
