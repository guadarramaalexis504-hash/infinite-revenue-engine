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
        self.launch_tasks = []
        self.offers = []
        self.portfolio_snapshots = []
        self.conversion_events = []
        self.tip_events = []
        self.click_events = []
        self.experiment_updates = []

    def upsert_revenue_opportunity(self, payload):
        self.opportunities.append(payload)
        return [{"id": "opp-portfolio"}]

    def insert_asset(self, payload):
        self.assets.append(payload)
        return [{"id": f"asset-{len(self.assets)}"}]

    def insert_experiment(self, payload):
        self.experiments.append(payload)
        return [{"id": "experiment-1"}]

    def insert_launch_task(self, payload):
        self.launch_tasks.append(payload)
        return [{"id": f"launch-task-{len(self.launch_tasks)}"}]

    def insert_offer(self, payload):
        self.offers.append(payload)
        return [{"id": f"offer-{len(self.offers)}"}]

    def insert_event(self, run_id, event_type, payload):
        self.events.append((event_type, payload))

    def list_conversion_events(self):
        return self.conversion_events

    def list_tip_events(self):
        return self.tip_events

    def list_assets(self):
        return self.assets

    def list_click_events(self):
        return self.click_events

    def list_offers(self):
        return self.offers

    def list_experiments(self):
        return self.experiments

    def insert_portfolio_snapshot(self, payload):
        self.portfolio_snapshots.append(payload)
        return [{"id": f"snapshot-{len(self.portfolio_snapshots)}"}]

    def update_experiment_status(self, experiment_id, status, payload):
        self.experiment_updates.append((experiment_id, status, payload))
        return [{"id": experiment_id, "status": status}]


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


class FakeLaunchQueueExporter:
    def __init__(self):
        self.exports = []

    def export(self, tasks):
        self.exports.append(tasks)
        return ["launch_queue.json", "LAUNCH_QUEUE.md"]


class FakeMicrotoolExporter:
    def __init__(self):
        self.exports = []

    def export_portfolio(self, opportunities_with_assets):
        self.exports.append(opportunities_with_assets)
        return ["index.html", "kw-portfolio/index.html"]


class FakeOfferExporter:
    def __init__(self):
        self.exports = []

    def export(self, offers):
        self.exports.append(offers)
        return ["offers.json", "OFFERS.md"]


class FakeCheckoutSetupExporter:
    def __init__(self):
        self.exports = []

    def export(self, offers):
        self.exports.append(offers)
        return ["checkout_setup.json", "CHECKOUT_SETUP.md"]


class FakeTrackingDeployExporter:
    def __init__(self):
        self.exports = 0

    def export(self):
        self.exports += 1
        return ["Dockerfile", ".env.tracking.example", "tracking_deploy.json", "DEPLOY_TRACKING_APP.md"]


class FakeLeadMagnetExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities):
        self.exports.append(opportunities)
        return ["lead_magnets.json", "LEAD_MAGNETS.md", "index.html", "checklist.md"]


class FakeDigitalProductExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities):
        self.exports.append(opportunities)
        return ["digital_products.json", "DIGITAL_PRODUCTS.md", "README.md", "STORE_LISTING.md"]


class FakeAffiliateArticleExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities):
        self.exports.append(opportunities)
        return ["affiliate_articles.json", "AFFILIATE_ARTICLES.md", "index.html", "ARTICLE.md"]


class FakeRoadmapExporter:
    def __init__(self):
        self.exports = []

    def export(self, *, discovered, selected, milestones, activation_report):
        self.exports.append(
            {
                "discovered": discovered,
                "selected": selected,
                "milestones": milestones,
                "activation_report": activation_report,
            }
        )
        return ["opportunity_roadmap.json", "OPPORTUNITY_ROADMAP.md"]


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
        self.assertEqual(summary.launch_tasks_created, 4)
        self.assertEqual(len(supabase.launch_tasks), 4)
        self.assertEqual(supabase.launch_tasks[0]["external_id"], "kw-portfolio")
        self.assertEqual(summary.offers_created, 2)
        self.assertEqual(len(supabase.offers), 2)
        self.assertEqual(supabase.offers[0]["opportunity_id"], "opp-portfolio")

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

    def test_run_revenue_portfolio_once_can_export_launch_queue(self):
        queue_exporter = FakeLaunchQueueExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            launch_queue_exporter=queue_exporter,
        )

        self.assertEqual(summary.launch_tasks_created, 4)
        self.assertEqual(summary.launch_tasks_exported, 2)
        self.assertEqual(len(queue_exporter.exports), 1)
        self.assertEqual(queue_exporter.exports[0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_includes_activation_blockers_in_launch_queue(self):
        queue_exporter = FakeLaunchQueueExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            launch_queue_exporter=queue_exporter,
            activation_report={
                "ready": False,
                "next_actions": [
                    "Replace placeholder .env values: SUPABASE_KEY",
                    "Add git remote origin",
                ],
            },
        )

        self.assertEqual(summary.launch_tasks_created, 6)
        self.assertTrue(queue_exporter.exports[0][0].blocking)
        self.assertEqual(queue_exporter.exports[0][0].category, "activation")
        self.assertIn("Replace placeholder", queue_exporter.exports[0][0].title)

    def test_run_revenue_portfolio_once_can_export_microtools(self):
        microtool_exporter = FakeMicrotoolExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            microtool_exporter=microtool_exporter,
        )

        self.assertEqual(summary.microtools_exported, 2)
        self.assertEqual(len(microtool_exporter.exports), 1)
        self.assertEqual(microtool_exporter.exports[0][0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_can_export_offer_catalog(self):
        offer_exporter = FakeOfferExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            offer_exporter=offer_exporter,
        )

        self.assertEqual(summary.offers_created, 2)
        self.assertEqual(summary.offers_exported, 2)
        self.assertEqual(len(offer_exporter.exports), 1)
        self.assertEqual(offer_exporter.exports[0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_can_export_checkout_setup(self):
        checkout_exporter = FakeCheckoutSetupExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            checkout_setup_exporter=checkout_exporter,
        )

        self.assertEqual(summary.offers_created, 2)
        self.assertEqual(summary.checkout_setup_exported, 2)
        self.assertEqual(len(checkout_exporter.exports), 1)
        self.assertEqual(checkout_exporter.exports[0][0].offer_key, "manual_keywords:kw-portfolio:support")

    def test_run_revenue_portfolio_once_can_export_tracking_deploy_bundle(self):
        tracking_exporter = FakeTrackingDeployExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            tracking_deploy_exporter=tracking_exporter,
        )

        self.assertEqual(summary.tracking_deploy_exported, 4)
        self.assertEqual(tracking_exporter.exports, 1)

    def test_run_revenue_portfolio_once_can_export_lead_magnets(self):
        lead_exporter = FakeLeadMagnetExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            lead_magnet_exporter=lead_exporter,
        )

        self.assertEqual(summary.lead_magnets_exported, 4)
        self.assertEqual(len(lead_exporter.exports), 1)
        self.assertEqual(lead_exporter.exports[0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_can_export_digital_products(self):
        product_exporter = FakeDigitalProductExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            digital_product_exporter=product_exporter,
        )

        self.assertEqual(summary.digital_products_exported, 4)
        self.assertEqual(len(product_exporter.exports), 1)
        self.assertEqual(product_exporter.exports[0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_can_export_affiliate_articles(self):
        article_exporter = FakeAffiliateArticleExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            affiliate_article_exporter=article_exporter,
        )

        self.assertEqual(summary.affiliate_articles_exported, 4)
        self.assertEqual(len(article_exporter.exports), 1)
        self.assertEqual(article_exporter.exports[0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_can_export_opportunity_roadmap(self):
        roadmap_exporter = FakeRoadmapExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            roadmap_exporter=roadmap_exporter,
            activation_report={"ready": False, "next_actions": ["Run gh auth login"]},
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(summary.roadmap_exported, 2)
        self.assertEqual(len(roadmap_exporter.exports), 1)
        self.assertEqual(roadmap_exporter.exports[0]["discovered"][0].external_id, "kw-portfolio")
        self.assertEqual(roadmap_exporter.exports[0]["selected"][0].external_id, "kw-portfolio")
        self.assertEqual(roadmap_exporter.exports[0]["activation_report"]["ready"], False)

    def test_summarize_phase_persists_dashboard_snapshot(self):
        supabase = FakeSupabase()
        supabase.conversion_events = [
            {"source": "microtool_seo", "offer_id": "offer-1", "amount_usd": 20},
        ]
        supabase.tip_events = [{"amount_usd": 5}]
        supabase.assets = [{"status": "draft"}, {"status": "published"}]
        supabase.offers = [{"id": "offer-1", "title": "Supabase setup"}]
        supabase.click_events = [{"payload": {"utm_content": "setup_service"}}]

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=supabase,
            phase="summarize",
            milestones=[15, 200, 1000, 20000],
        )

        self.assertEqual(summary.status, "success")
        self.assertEqual(summary.dashboard_snapshots_created, 1)
        self.assertEqual(supabase.portfolio_snapshots[0]["total_revenue_usd"], 25)
        self.assertEqual(supabase.portfolio_snapshots[0]["best_offer"]["title"], "Supabase setup")
        self.assertEqual(supabase.events[-1][0], "revenue_portfolio_summarized")

    def test_prune_phase_marks_winners_pauses_stale_experiments_and_creates_revision_tasks(self):
        supabase = FakeSupabase()
        supabase.experiments = [
            {
                "id": "exp-won",
                "opportunity_id": "opp-won",
                "name": "microtool:won",
                "status": "running",
                "created_at": "2026-05-01T00:00:00+00:00",
            },
            {
                "id": "exp-clicks",
                "opportunity_id": "opp-clicks",
                "name": "microtool:clicks",
                "status": "running",
                "created_at": "2026-05-01T00:00:00+00:00",
            },
            {
                "id": "exp-stale",
                "opportunity_id": "opp-stale",
                "name": "microtool:stale",
                "status": "running",
                "created_at": "2026-05-01T00:00:00+00:00",
            },
        ]
        supabase.offers = [
            {"id": "offer-won", "opportunity_id": "opp-won", "title": "Won offer"},
            {"id": "offer-clicks", "opportunity_id": "opp-clicks", "title": "Clicky offer"},
        ]
        supabase.click_events = [
            {"offer_id": "offer-clicks"},
            {"offer_id": "offer-clicks"},
            {"offer_id": "offer-clicks"},
        ]
        supabase.conversion_events = [{"offer_id": "offer-won", "amount_usd": 49}]

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=supabase,
            phase="prune",
        )

        self.assertEqual(summary.prune_decisions_created, 3)
        self.assertEqual(summary.experiments_updated, 2)
        self.assertEqual(summary.launch_tasks_created, 1)
        self.assertIn(("exp-won", "won"), [(row[0], row[1]) for row in supabase.experiment_updates])
        self.assertIn(("exp-stale", "paused"), [(row[0], row[1]) for row in supabase.experiment_updates])
        self.assertEqual(supabase.launch_tasks[0]["category"], "monetize")
        self.assertEqual(supabase.events[-1][0], "revenue_portfolio_pruned")


if __name__ == "__main__":
    unittest.main()
