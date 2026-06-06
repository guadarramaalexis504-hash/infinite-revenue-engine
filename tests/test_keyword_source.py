import tempfile
import unittest
from pathlib import Path

from farm_loop.sources_keywords import KeywordCSVSource


class KeywordCSVSourceTests(unittest.TestCase):
    def test_loads_manual_keyword_opportunities_from_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "keywords.csv"
            csv_path.write_text(
                "id,title,problem,tags,channel,payout_estimate_usd,conversion_probability,estimated_cost_usd,risk_penalty_usd,build_minutes\n"
                "kw-1,Supabase RLS checker,Developers need to validate policies,\"supabase;rls\",microtool_seo,199,0.06,4,1,40\n",
                encoding="utf-8",
            )

            opportunities = KeywordCSVSource(csv_path).load()

        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].external_id, "kw-1")
        self.assertEqual(opportunities[0].channel, "microtool_seo")
        self.assertEqual(opportunities[0].payout_estimate_usd, 199)


if __name__ == "__main__":
    unittest.main()
