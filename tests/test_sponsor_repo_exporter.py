import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.revenue_scoring import RevenueOpportunity
from farm_loop.sponsor_repo_exporter import SponsorRepoExporter, build_sponsor_repo_rows


def make_opportunity(channel="open_source_sponsorship"):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id="template-github-sponsors-readme",
        title="GitHub Sponsors README and Funding Kit",
        url="https://example.com/idea",
        problem="Open-source maintainers need a clear sponsor pitch, tiers, and funding file setup.",
        tags=["github-sponsors", "open-source", "readme"],
        channel=channel,
        payout_estimate_usd=150,
        conversion_probability=0.05,
        estimated_cost_usd=3,
        risk_penalty_usd=1,
        build_minutes=30,
        expected_value_usd=7.0,
    )


class SponsorRepoExporterTests(unittest.TestCase):
    def test_build_rows_filters_sponsorships_and_tracks_sponsor_cta(self):
        rows = build_sponsor_repo_rows(
            [make_opportunity(), make_opportunity(channel="digital_product")],
            sponsor_urls={"github": "https://github.com/sponsors/example"},
            click_redirect_url="https://track.example.com/click",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["slug"], "template-github-sponsors-readme")
        self.assertEqual(rows[0]["repo_name"], "template-github-sponsors-readme")
        self.assertEqual(rows[0]["sponsor_url"], "https://github.com/sponsors/example")
        self.assertIn("target=https%3A%2F%2Fgithub.com%2Fsponsors%2Fexample", rows[0]["tracked_sponsor_url"])
        self.assertEqual(rows[0]["funding_custom_urls"], ["https://github.com/sponsors/example"])
        self.assertIn("No automated outreach", rows[0]["safety_notes"][0])

    def test_exporter_writes_repo_kit_files_for_manual_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = SponsorRepoExporter(
                Path(directory) / "sponsor-repos",
                sponsor_urls={"github": "https://github.com/sponsors/example"},
                click_redirect_url="https://track.example.com/click",
            )

            paths = exporter.export([make_opportunity()])

            output_dir = Path(directory) / "sponsor-repos"
            manifest = json.loads((output_dir / "sponsor_repos.json").read_text(encoding="utf-8"))
            catalog = (output_dir / "SPONSOR_REPOS.md").read_text(encoding="utf-8")
            repo_dir = output_dir / "template-github-sponsors-readme"
            readme = (repo_dir / "README.md").read_text(encoding="utf-8")
            funding = (repo_dir / ".github" / "FUNDING.yml").read_text(encoding="utf-8")
            support = (repo_dir / ".github" / "ISSUE_TEMPLATE" / "support.yml").read_text(encoding="utf-8")
            contributing = (repo_dir / "CONTRIBUTING.md").read_text(encoding="utf-8")
            roadmap = (repo_dir / "ROADMAP.md").read_text(encoding="utf-8")
            usage = (repo_dir / "examples" / "usage.md").read_text(encoding="utf-8")
            page = (repo_dir / "index.html").read_text(encoding="utf-8")

        written_names = [path.name for path in paths]
        self.assertIn("sponsor_repos.json", written_names)
        self.assertIn("SPONSOR_REPOS.md", written_names)
        self.assertEqual(manifest[0]["title"], "GitHub Sponsors README and Funding Kit")
        self.assertIn("# Sponsor Repo Kits", catalog)
        self.assertIn("GitHub Sponsors", readme)
        self.assertIn("No automated outreach", readme)
        self.assertIn("custom:", funding)
        self.assertIn("https://github.com/sponsors/example", funding)
        self.assertIn("paid support request", support)
        self.assertIn("manual review", contributing)
        self.assertIn("Sponsor tiers", roadmap)
        self.assertIn("Usage Example", usage)
        self.assertIn("https://track.example.com/click", page)


if __name__ == "__main__":
    unittest.main()
