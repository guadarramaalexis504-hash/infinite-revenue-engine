import json
import tempfile
import unittest
from pathlib import Path
from collections import Counter

from farm_loop.sources_idea_catalog import IdeaCatalogSource


CATALOG_PATH = Path("data/revenue_ideas.json")
REQUIRED_CHANNELS = {
    "microtool_seo",
    "paid_setup_kit",
    "digital_product",
    "github_issue_helper",
    "article_affiliate",
    "open_source_sponsorship",
    "lead_magnet",
    "bounty_scanner",
    "niche_report",
}


class IdeaCatalogSourceTests(unittest.TestCase):
    def test_loads_catalog_ideas_as_revenue_opportunities(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ideas.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "microtool-json-schema-diff",
                            "title": "JSON Schema Diff Tool",
                            "problem": "Developers need to compare schema changes safely.",
                            "tags": ["json", "schema", "api"],
                            "channel": "microtool_seo",
                            "payout_estimate_usd": 220,
                            "conversion_probability": 0.07,
                            "estimated_cost_usd": 4,
                            "risk_penalty_usd": 1,
                            "build_minutes": 35,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            opportunities = IdeaCatalogSource(path).discover()

        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].source, "idea_catalog")
        self.assertEqual(opportunities[0].external_id, "microtool-json-schema-diff")
        self.assertEqual(opportunities[0].channel, "microtool_seo")
        self.assertEqual(opportunities[0].payout_estimate_usd, 220)

    def test_missing_catalog_returns_empty_list(self):
        opportunities = IdeaCatalogSource("missing-catalog.json").discover()

        self.assertEqual(opportunities, [])

    def test_default_catalog_is_large_and_actionable_for_long_running_revenue(self):
        ideas = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        channels = Counter(idea.get("channel") for idea in ideas)
        ids = [idea.get("id") for idea in ideas]

        self.assertGreaterEqual(len(ideas), 50)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(REQUIRED_CHANNELS.issubset(channels.keys()))
        for idea in ideas:
            self.assertTrue(idea["title"])
            self.assertTrue(idea["problem"])
            self.assertGreater(float(idea["payout_estimate_usd"]), 0)
            self.assertGreater(float(idea["conversion_probability"]), 0)
            self.assertGreater(int(idea["build_minutes"]), 0)


if __name__ == "__main__":
    unittest.main()
