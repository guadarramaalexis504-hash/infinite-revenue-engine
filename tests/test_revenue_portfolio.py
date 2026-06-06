import unittest

from farm_loop.revenue_engine import run_revenue_portfolio_once
from farm_loop.revenue_scoring import RevenueOpportunity


class FakeSource:
    def discover(self):
        return [
            RevenueOpportunity(
                source="manual_keywords",
                external_id="kw-portfolio",
                title="Supabase policy checker",
                url="file://keywords.csv#kw-portfolio",
                problem="Developers need RLS feedback.",
                tags=["supabase", "rls"],
                channel="microtool_seo",
                payout_estimate_usd=300,
                conversion_probability=0.08,
                estimated_cost_usd=5,
                risk_penalty_usd=1,
                build_minutes=45,
            )
        ]


class FakeSupabase:
    def __init__(self):
        self.opportunities = []
        self.assets = []
        self.experiments = []
        self.events = []

    def upsert_revenue_opportunity(self, payload):
        self.opportunities.append(payload)
        return [{"id": "opp-portfolio"}]

    def insert_asset(self, payload):
        self.assets.append(payload)
        return [{"id": f"asset-{len(self.assets)}"}]

    def insert_experiment(self, payload):
        self.experiments.append(payload)
        return [{"id": "experiment-1"}]

    def insert_event(self, run_id, event_type, payload):
        self.events.append((event_type, payload))


class FakeAssetExporter:
    def __init__(self):
        self.exports = []

    def export_opportunity(self, opportunity, assets):
        self.exports.append((opportunity, assets))
        return [f"{opportunity.external_id}/{asset.asset_type}.md" for asset in assets]


class FakeSiteExporter:
    def __init__(self):
        self.portfolios = []

    def export_portfolio(self, opportunities_with_assets):
        self.portfolios.append(opportunities_with_assets)
        return ["index.html", "kw-portfolio/index.html"]


class RevenuePortfolioTests(unittest.TestCase):
    def test_run_revenue_portfolio_once_scores_generates_assets_and_continues_past_milestones(self):
        supabase = FakeSupabase()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=supabase,
            max_opportunities=3,
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(summary.discovered, 1)
        self.assertEqual(summary.assets_created, 6)
        self.assertEqual(summary.status, "success")
        self.assertEqual(supabase.opportunities[0]["external_id"], "kw-portfolio")
        self.assertEqual(supabase.experiments[0]["status"], "planned")

    def test_run_revenue_portfolio_once_can_export_local_review_assets(self):
        exporter = FakeAssetExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            asset_exporter=exporter,
        )

        self.assertEqual(summary.assets_created, 6)
        self.assertEqual(summary.assets_exported, 6)
        self.assertEqual(len(exporter.exports), 1)
        self.assertEqual(exporter.exports[0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_can_export_owned_static_site(self):
        site_exporter = FakeSiteExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            site_exporter=site_exporter,
        )

        self.assertEqual(summary.site_pages_exported, 2)
        self.assertEqual(len(site_exporter.portfolios), 1)
        self.assertEqual(site_exporter.portfolios[0][0][0].external_id, "kw-portfolio")
        self.assertEqual(len(site_exporter.portfolios[0][0][1]), 6)


if __name__ == "__main__":
    unittest.main()
