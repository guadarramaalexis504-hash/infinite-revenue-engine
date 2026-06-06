import unittest

from farm_loop.main import parse_args


class CLITests(unittest.TestCase):
    def test_parse_args_supports_portfolio_phases(self):
        args = parse_args(["--portfolio-once", "--portfolio-phase", "summarize", "--dry-run"])

        self.assertTrue(args.portfolio_once)
        self.assertEqual(args.portfolio_phase, "summarize")
        self.assertTrue(args.dry_run)

    def test_parse_args_supports_local_asset_output_dir(self):
        args = parse_args(
            [
                "--portfolio-once",
                "--portfolio-phase",
                "generate",
                "--dry-run",
                "--asset-output-dir",
                "out/review-queue",
            ]
        )

        self.assertEqual(args.asset_output_dir, "out/review-queue")

    def test_parse_args_supports_static_site_output_dir(self):
        args = parse_args(
            [
                "--portfolio-once",
                "--portfolio-phase",
                "generate",
                "--dry-run",
                "--site-output-dir",
                "out/site",
            ]
        )

        self.assertEqual(args.site_output_dir, "out/site")


if __name__ == "__main__":
    unittest.main()
