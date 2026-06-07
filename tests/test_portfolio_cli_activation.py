import unittest
from pathlib import Path
from unittest.mock import patch

from farm_loop.config import Settings
from farm_loop.main import parse_args, run_portfolio_single
from farm_loop.revenue_engine import RevenuePortfolioSummary


class PortfolioCLIActivationTests(unittest.TestCase):
    def test_run_portfolio_single_passes_activation_report_when_launch_queue_is_exported(self):
        report = {
            "ready": False,
            "next_actions": ["Replace placeholder .env values: OPENAI_API_KEY"],
        }
        settings = Settings(
            supabase_url=None,
            supabase_key=None,
            openai_api_key=None,
            stackexchange_key=None,
            tip_url="",
        )
        args = parse_args(
            [
                "--portfolio-once",
                "--portfolio-phase",
                "generate",
                "--dry-run",
                "--launch-queue-output-dir",
                "out/launch-queue",
            ]
        )

        with (
            patch("farm_loop.main.Settings.from_env", return_value=settings),
            patch("farm_loop.main.collect_activation_report", return_value=report) as collect_report,
            patch("farm_loop.main.run_revenue_portfolio_once") as run_once,
        ):
            run_once.return_value = RevenuePortfolioSummary(
                status="success",
                discovered=0,
                selected=0,
                assets_created=0,
            )

            result = run_portfolio_single(args)

        self.assertEqual(result, 0)
        collect_report.assert_called_once()
        self.assertEqual(run_once.call_args.kwargs["activation_report"], report)

    def test_run_portfolio_single_expands_bundle_output_dir_to_all_exporters(self):
        report = {
            "ready": False,
            "next_actions": ["Run gh auth login"],
        }
        settings = Settings(
            supabase_url=None,
            supabase_key=None,
            openai_api_key=None,
            stackexchange_key=None,
            tip_url="",
            asset_output_dir="env/assets",
            site_output_dir="env/site",
            launch_queue_output_dir="env/launch-queue",
            microtool_output_dir="env/microtools",
            offer_output_dir="env/offers",
            checkout_setup_output_dir="env/checkout-setup",
            tracking_deploy_output_dir="env/tracking-deploy",
            lead_magnet_output_dir="env/lead-magnets",
            digital_product_output_dir="env/digital-products",
            service_package_output_dir="env/service-packages",
            niche_report_output_dir="env/niche-reports",
            affiliate_article_output_dir="env/affiliate-articles",
            sponsor_repo_output_dir="env/sponsor-repos",
            roadmap_output_dir="env/roadmap",
        )
        args = parse_args(
            [
                "--portfolio-once",
                "--portfolio-phase",
                "generate",
                "--dry-run",
                "--bundle-output-dir",
                "out/revenue-bundle",
            ]
        )

        with (
            patch("farm_loop.main.Settings.from_env", return_value=settings),
            patch("farm_loop.main.collect_activation_report", return_value=report) as collect_report,
            patch("farm_loop.main.run_revenue_portfolio_once") as run_once,
        ):
            run_once.return_value = RevenuePortfolioSummary(
                status="success",
                discovered=0,
                selected=0,
                assets_created=0,
            )

            result = run_portfolio_single(args)

        kwargs = run_once.call_args.kwargs
        self.assertEqual(result, 0)
        collect_report.assert_called_once()
        self.assertEqual(kwargs["asset_exporter"].output_dir, Path("out/revenue-bundle/assets"))
        self.assertEqual(kwargs["site_exporter"].output_dir, Path("out/revenue-bundle/site"))
        self.assertEqual(kwargs["microtool_exporter"].output_dir, Path("out/revenue-bundle/site/tools"))
        self.assertEqual(kwargs["offer_exporter"].output_dir, Path("out/revenue-bundle/offers"))
        self.assertEqual(kwargs["checkout_setup_exporter"].output_dir, Path("out/revenue-bundle/checkout-setup"))
        self.assertEqual(kwargs["tracking_deploy_exporter"].output_dir, Path("out/revenue-bundle/tracking-deploy"))
        self.assertEqual(kwargs["lead_magnet_exporter"].output_dir, Path("out/revenue-bundle/lead-magnets"))
        self.assertEqual(kwargs["digital_product_exporter"].output_dir, Path("out/revenue-bundle/digital-products"))
        self.assertEqual(kwargs["service_package_exporter"].output_dir, Path("out/revenue-bundle/service-packages"))
        self.assertEqual(kwargs["niche_report_exporter"].output_dir, Path("out/revenue-bundle/niche-reports"))
        self.assertEqual(kwargs["affiliate_article_exporter"].output_dir, Path("out/revenue-bundle/affiliate-articles"))
        self.assertEqual(kwargs["sponsor_repo_exporter"].output_dir, Path("out/revenue-bundle/sponsor-repos"))
        self.assertEqual(kwargs["roadmap_exporter"].output_dir, Path("out/revenue-bundle/roadmap"))
        self.assertEqual(kwargs["launch_queue_exporter"].output_dir, Path("out/revenue-bundle/launch-queue"))
        self.assertEqual(kwargs["activation_report"], report)


if __name__ == "__main__":
    unittest.main()
