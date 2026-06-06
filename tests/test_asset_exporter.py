import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.assets import AssetGenerator
from farm_loop.asset_exporter import LocalAssetExporter, slugify
from farm_loop.revenue_scoring import RevenueOpportunity, score_opportunity


class LocalAssetExporterTests(unittest.TestCase):
    def setUp(self):
        self.opportunity = score_opportunity(
            RevenueOpportunity(
                source="idea_catalog",
                external_id="microtool-github-actions-yaml-validator",
                title="GitHub Actions YAML Validator",
                url="file://revenue_ideas.json#microtool-github-actions-yaml-validator",
                problem="Developers break workflow files and want a fast preflight check.",
                tags=["github-actions", "yaml", "ci"],
                channel="microtool_seo",
                payout_estimate_usd=250,
                conversion_probability=0.08,
                estimated_cost_usd=4,
                risk_penalty_usd=1,
                build_minutes=30,
            )
        )

    def test_slugify_creates_stable_safe_names(self):
        self.assertEqual(slugify("GitHub Actions: YAML Validator!"), "github-actions-yaml-validator")
        self.assertEqual(slugify(""), "asset")

    def test_exports_manifest_and_markdown_files_for_manual_review(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        with tempfile.TemporaryDirectory() as directory:
            exported = LocalAssetExporter(directory).export_opportunity(self.opportunity, assets)
            root = Path(directory) / "idea-catalog-microtool-github-actions-yaml-validator"

            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            first_asset = (root / "01-microtool-spec.md").read_text(encoding="utf-8")

        self.assertEqual(len(exported), 7)
        self.assertEqual(manifest["opportunity"]["external_id"], "microtool-github-actions-yaml-validator")
        self.assertEqual(manifest["opportunity"]["expected_value_usd"], 18.5)
        self.assertEqual(manifest["publication_mode"], "manual_review")
        self.assertIn("01-microtool-spec.md", manifest["asset_files"])
        self.assertIn("Next manual step", first_asset)


if __name__ == "__main__":
    unittest.main()
