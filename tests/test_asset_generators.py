import unittest

from farm_loop.assets import AssetGenerator, is_publication_allowed
from farm_loop.revenue_scoring import RevenueOpportunity


class AssetGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.opportunity = RevenueOpportunity(
            source="manual_keywords",
            external_id="kw-asset",
            title="GitHub Actions YAML checker",
            url="file://keywords.csv#kw-asset",
            problem="Developers need to catch workflow syntax mistakes before pushing.",
            tags=["github-actions", "yaml"],
            channel="microtool_seo",
            payout_estimate_usd=250,
            conversion_probability=0.08,
            estimated_cost_usd=4,
            risk_penalty_usd=1,
            build_minutes=30,
        )

    def test_generates_all_reviewable_asset_types_without_public_posting(self):
        assets = AssetGenerator().generate_all(self.opportunity)

        self.assertEqual(
            [asset.asset_type for asset in assets],
            [
                "microtool_spec",
                "article_outline",
                "github_patch_plan",
                "product_listing",
                "landing_page_copy",
                "support_offer",
            ],
        )
        self.assertTrue(all(asset.status == "draft" for asset in assets))
        self.assertTrue(all(asset.publication_mode == "manual_review" for asset in assets))

    def test_safety_rules_disallow_stackoverflow_publication(self):
        self.assertFalse(is_publication_allowed("stackoverflow", "ai_generated_answer"))
        self.assertTrue(is_publication_allowed("owned_site", "article_outline"))


if __name__ == "__main__":
    unittest.main()
