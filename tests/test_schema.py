import unittest
from pathlib import Path


class SchemaTests(unittest.TestCase):
    def test_schema_contains_revenue_portfolio_tables_with_rls(self):
        schema = Path("supabase/schema.sql").read_text(encoding="utf-8")

        for table in [
            "revenue_milestones",
            "channels",
            "assets",
            "offers",
            "click_events",
            "conversion_events",
            "experiments",
            "launch_tasks",
            "portfolio_snapshots",
        ]:
            self.assertIn(f"create table if not exists public.{table}", schema)
            self.assertIn(f"alter table public.{table} enable row level security", schema)

    def test_schema_extends_opportunities_for_revenue_scoring(self):
        schema = Path("supabase/schema.sql").read_text(encoding="utf-8")

        for column in [
            "problem",
            "channel",
            "payout_estimate_usd",
            "conversion_probability",
            "estimated_cost_usd",
            "risk_penalty_usd",
            "build_minutes",
            "expected_value_usd",
        ]:
            self.assertIn(f"add column if not exists {column}", schema)

    def test_schema_links_offers_to_opportunities(self):
        schema = Path("supabase/schema.sql").read_text(encoding="utf-8")

        self.assertIn("opportunity_id uuid references public.opportunities(id)", schema)


if __name__ == "__main__":
    unittest.main()
