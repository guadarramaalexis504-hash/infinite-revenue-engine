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


class FakeServicePackageExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities):
        self.exports.append(opportunities)
        return ["service_packages.json", "SERVICE_PACKAGES.md", "PROPOSAL.md", "SCOPE.md"]


class FakeNicheReportExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities):
        self.exports.append(opportunities)
        return ["niche_reports.json", "NICHE_REPORTS.md", "REPORT.md", "STORE_LISTING.md"]


class FakeAffiliateArticleExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities):
        self.exports.append(opportunities)
        return ["affiliate_articles.json", "AFFILIATE_ARTICLES.md", "index.html", "ARTICLE.md"]


class FakeSponsorRepoExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities):
        self.exports.append(opportunities)
        return ["sponsor_repos.json", "SPONSOR_REPOS.md", "README.md", "FUNDING.yml"]


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


class FakeActivationManifestExporter:
    def __init__(self):
        self.exports = []

    def export(self, opportunities_with_assets, *, offers, activation_report):
        self.exports.append(
            {
                "opportunities_with_assets": opportunities_with_assets,
                "offers": offers,
                "activation_report": activation_report,
            }
        )
        return ["activation_manifest.json", "ACTIVATE_NOW.md", "RUNBOOK.md", "CLAUDE_HANDOFF.md"]


class FakeRevenueForecastExporter:
    def __init__(self):
        self.exports = []

    def export(self, *, offers, milestones):
        self.exports.append({"offers": offers, "milestones": milestones})
        return ["revenue_forecast.json", "REVENUE_FORECAST.md"]


class FakeOfferLadderExporter:
    def __init__(self):
        self.exports = []

    def export(self, *, offers, milestones):
        self.exports.append({"offers": offers, "milestones": milestones})
        return ["offer_ladder.json", "OFFER_LADDER.md"]


class FakeLaunchSprintExporter:
    def __init__(self):
        self.exports = []

    def export(self, *, opportunities, offers, milestones, activation_report):
        self.exports.append(
            {
                "opportunities": opportunities,
                "offers": offers,
                "milestones": milestones,
                "activation_report": activation_report,
            }
        )
        return ["launch_sprint.json", "30_DAY_LAUNCH_PLAN.md"]


class FakeTrafficPlanExporter:
    def __init__(self):
        self.exports = []

    def export(self, *, opportunities, offers, site_base_url, click_redirect_url, lead_capture_url):
        self.exports.append(
            {
                "opportunities": opportunities,
                "offers": offers,
                "site_base_url": site_base_url,
                "click_redirect_url": click_redirect_url,
                "lead_capture_url": lead_capture_url,
            }
        )
        return ["traffic_plan.json", "TRAFFIC_PLAN.md"]


class FakeAllIdeasCatalogExporter:
    def __init__(self):
        self.exports = []

    def export(self, *, ideas, selected_external_ids, milestones):
        self.exports.append(
            {
                "ideas": ideas,
                "selected_external_ids": selected_external_ids,
                "milestones": milestones,
            }
        )
        return ["all_revenue_ideas.json", "ALL_REVENUE_IDEAS.md"]


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

    def test_run_revenue_portfolio_once_can_export_service_packages(self):
        service_exporter = FakeServicePackageExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            service_package_exporter=service_exporter,
        )

        self.assertEqual(summary.service_packages_exported, 4)
        self.assertEqual(len(service_exporter.exports), 1)
        self.assertEqual(service_exporter.exports[0][0].external_id, "kw-portfolio")

    def test_run_revenue_portfolio_once_can_export_niche_reports(self):
        niche_exporter = FakeNicheReportExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            niche_report_exporter=niche_exporter,
        )

        self.assertEqual(summary.niche_reports_exported, 4)
        self.assertEqual(len(niche_exporter.exports), 1)
        self.assertEqual(niche_exporter.exports[0][0].external_id, "kw-portfolio")

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

    def test_run_revenue_portfolio_once_can_export_sponsor_repo_kits(self):
        sponsor_exporter = FakeSponsorRepoExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            sponsor_repo_exporter=sponsor_exporter,
        )

        self.assertEqual(summary.sponsor_repos_exported, 4)
        self.assertEqual(len(sponsor_exporter.exports), 1)
        self.assertEqual(sponsor_exporter.exports[0][0].external_id, "kw-portfolio")

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

    def test_run_revenue_portfolio_once_can_export_activation_manifest(self):
        activation_exporter = FakeActivationManifestExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            max_opportunities=3,
            dry_run=True,
            activation_manifest_exporter=activation_exporter,
            activation_report={"ready": False, "next_actions": ["Run gh auth login"]},
        )

        self.assertEqual(summary.activation_manifest_exported, 4)
        self.assertEqual(len(activation_exporter.exports), 1)
        self.assertEqual(
            activation_exporter.exports[0]["opportunities_with_assets"][0][0].external_id,
            "kw-portfolio",
        )
        self.assertEqual(activation_exporter.exports[0]["offers"][0].offer_key, "manual_keywords:kw-portfolio:support")
        self.assertEqual(activation_exporter.exports[0]["activation_report"]["next_actions"], ["Run gh auth login"])

    def test_run_revenue_portfolio_once_can_export_revenue_forecast(self):
        forecast_exporter = FakeRevenueForecastExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            dry_run=True,
            max_opportunities=3,
            milestones=[15, 200, 1000, 20000],
            revenue_forecast_exporter=forecast_exporter,
        )

        self.assertEqual(summary.revenue_forecast_exported, 2)
        self.assertEqual(len(forecast_exporter.exports), 1)
        self.assertEqual(forecast_exporter.exports[0]["milestones"], [15, 200, 1000, 20000])
        self.assertEqual(len(forecast_exporter.exports[0]["offers"]), 2)

    def test_run_revenue_portfolio_once_can_export_offer_ladder(self):
        ladder_exporter = FakeOfferLadderExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            dry_run=True,
            max_opportunities=3,
            milestones=[15, 200, 1000, 20000],
            offer_ladder_exporter=ladder_exporter,
        )

        self.assertEqual(summary.offer_ladder_exported, 2)
        self.assertEqual(len(ladder_exporter.exports), 1)
        self.assertEqual(ladder_exporter.exports[0]["milestones"], [15, 200, 1000, 20000])
        self.assertEqual(len(ladder_exporter.exports[0]["offers"]), 2)

    def test_run_revenue_portfolio_once_can_export_launch_sprint(self):
        sprint_exporter = FakeLaunchSprintExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            dry_run=True,
            max_opportunities=3,
            milestones=[15, 200, 1000, 20000],
            launch_sprint_exporter=sprint_exporter,
            activation_report={"ready": False, "next_actions": ["Run gh auth login"]},
        )

        self.assertEqual(summary.launch_sprint_exported, 2)
        self.assertEqual(len(sprint_exporter.exports), 1)
        self.assertEqual(sprint_exporter.exports[0]["opportunities"][0].external_id, "kw-portfolio")
        self.assertEqual(sprint_exporter.exports[0]["milestones"], [15, 200, 1000, 20000])
        self.assertEqual(sprint_exporter.exports[0]["activation_report"]["ready"], False)

    def test_run_revenue_portfolio_once_can_export_traffic_plan(self):
        traffic_exporter = FakeTrafficPlanExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            dry_run=True,
            max_opportunities=3,
            traffic_plan_exporter=traffic_exporter,
            site_base_url="https://revenue.example",
            click_redirect_url="https://track.example/click",
            lead_capture_url="https://forms.example/signup",
        )

        self.assertEqual(summary.traffic_plan_exported, 2)
        self.assertEqual(len(traffic_exporter.exports), 1)
        self.assertEqual(traffic_exporter.exports[0]["opportunities"][0].external_id, "kw-portfolio")
        self.assertEqual(traffic_exporter.exports[0]["site_base_url"], "https://revenue.example")

    def test_run_revenue_portfolio_once_can_export_all_ideas_catalog(self):
        all_ideas_exporter = FakeAllIdeasCatalogExporter()

        summary = run_revenue_portfolio_once(
            sources=[FakeSource()],
            supabase=None,
            dry_run=True,
            max_opportunities=3,
            milestones=[15, 200, 1000, 20000],
            all_ideas_exporter=all_ideas_exporter,
        )

        self.assertEqual(summary.all_ideas_exported, 2)
        self.assertEqual(len(all_ideas_exporter.exports), 1)
        self.assertEqual(all_ideas_exporter.exports[0]["ideas"][0].external_id, "kw-portfolio")
        self.assertEqual(all_ideas_exporter.exports[0]["selected_external_ids"], {"kw-portfolio"})
        self.assertEqual(all_ideas_exporter.exports[0]["milestones"], [15, 200, 1000, 20000])

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
