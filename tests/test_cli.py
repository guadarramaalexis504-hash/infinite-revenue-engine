import unittest

from farm_loop.main import parse_args, tools_path_for_site


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

    def test_parse_args_supports_click_redirect_url(self):
        args = parse_args(
            [
                "--portfolio-once",
                "--portfolio-phase",
                "generate",
                "--dry-run",
                "--site-output-dir",
                "out/site",
                "--click-redirect-url",
                "https://example.com/click",
            ]
        )

        self.assertEqual(args.click_redirect_url, "https://example.com/click")

    def test_parse_args_supports_launch_queue_output_dir(self):
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

        self.assertEqual(args.launch_queue_output_dir, "out/launch-queue")

    def test_parse_args_supports_microtool_output_dir(self):
        args = parse_args(
            [
                "--portfolio-once",
                "--portfolio-phase",
                "generate",
                "--dry-run",
                "--microtool-output-dir",
                "out/microtools",
            ]
        )

        self.assertEqual(args.microtool_output_dir, "out/microtools")

    def test_parse_args_supports_offer_output_dir(self):
        args = parse_args(
            [
                "--portfolio-once",
                "--portfolio-phase",
                "generate",
                "--dry-run",
                "--offer-output-dir",
                "out/offers",
            ]
        )

        self.assertEqual(args.offer_output_dir, "out/offers")

    def test_parse_args_supports_manual_conversion_recording(self):
        args = parse_args(
            [
                "--record-conversion",
                "--dry-run",
                "--conversion-provider",
                "gumroad",
                "--conversion-external-id",
                "sale-123",
                "--conversion-amount-usd",
                "29",
                "--conversion-source",
                "digital_product",
                "--conversion-offer-id",
                "offer-product",
                "--conversion-payload-json",
                '{"product":"Template pack"}',
            ]
        )

        self.assertTrue(args.record_conversion)
        self.assertEqual(args.conversion_provider, "gumroad")
        self.assertEqual(args.conversion_external_id, "sale-123")
        self.assertEqual(args.conversion_amount_usd, 29)
        self.assertEqual(args.conversion_source, "digital_product")
        self.assertEqual(args.conversion_offer_id, "offer-product")

    def test_tools_path_for_site_returns_relative_tools_url_inside_site_output(self):
        self.assertEqual(tools_path_for_site("out/site", "out/site/tools"), "tools/")
        self.assertEqual(tools_path_for_site("out/site", "out/site/tools/dev"), "tools/dev/")
        self.assertEqual(tools_path_for_site("out/site", "out/microtools"), "")


if __name__ == "__main__":
    unittest.main()
