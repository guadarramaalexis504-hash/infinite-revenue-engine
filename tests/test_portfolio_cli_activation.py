import unittest
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


if __name__ == "__main__":
    unittest.main()
