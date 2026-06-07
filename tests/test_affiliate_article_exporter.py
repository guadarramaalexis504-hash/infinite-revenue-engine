import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.affiliate_article_exporter import AffiliateArticleExporter, build_affiliate_article_rows
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(channel="article_affiliate"):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id="article-fastapi-deployment-comparison",
        title="FastAPI deployment comparison",
        url="https://example.com/idea",
        problem="FastAPI builders need a practical deployment comparison before choosing hosting.",
        tags=["fastapi", "deployment", "affiliate"],
        channel=channel,
        payout_estimate_usd=180,
        conversion_probability=0.05,
        estimated_cost_usd=4,
        risk_penalty_usd=1,
        build_minutes=35,
        expected_value_usd=4.0,
    )


class AffiliateArticleExporterTests(unittest.TestCase):
    def test_build_rows_filters_articles_and_adds_disclosed_tracked_affiliate_links(self):
        rows = build_affiliate_article_rows(
            [make_opportunity(), make_opportunity(channel="microtool_seo")],
            affiliate_urls={"fastapi": "https://affiliate.example/fastapi"},
            click_redirect_url="https://track.example.com/click",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["slug"], "article-fastapi-deployment-comparison")
        self.assertIn("affiliate", rows[0]["disclosure"].lower())
        self.assertEqual(rows[0]["affiliate_links"][0]["key"], "fastapi")
        self.assertIn("target=https%3A%2F%2Faffiliate.example%2Ffastapi", rows[0]["affiliate_links"][0]["url"])
        self.assertGreaterEqual(len(rows[0]["outline_sections"]), 6)

    def test_exporter_writes_catalog_article_disclosure_and_landing_page(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = AffiliateArticleExporter(
                Path(directory) / "affiliate-articles",
                affiliate_urls={"fastapi": "https://affiliate.example/fastapi"},
                click_redirect_url="https://track.example.com/click",
            )

            paths = exporter.export([make_opportunity()])

            output_dir = Path(directory) / "affiliate-articles"
            manifest = json.loads((output_dir / "affiliate_articles.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "AFFILIATE_ARTICLES.md").read_text(encoding="utf-8")
            article_dir = output_dir / "article-fastapi-deployment-comparison"
            article = (article_dir / "ARTICLE.md").read_text(encoding="utf-8")
            disclosure = (article_dir / "DISCLOSURE.md").read_text(encoding="utf-8")
            landing = (article_dir / "index.html").read_text(encoding="utf-8")

        self.assertIn("affiliate_articles.json", [path.name for path in paths])
        self.assertEqual(manifest[0]["title"], "FastAPI deployment comparison")
        self.assertIn("# Affiliate Articles", markdown)
        self.assertIn("# FastAPI deployment comparison", article)
        self.assertIn("Disclosure", disclosure)
        self.assertIn("FastAPI deployment comparison", landing)
        self.assertIn("affiliate.example", landing)


if __name__ == "__main__":
    unittest.main()
