import unittest

from farm_loop.main import parse_args


class CLITests(unittest.TestCase):
    def test_parse_args_supports_portfolio_phases(self):
        args = parse_args(["--portfolio-once", "--portfolio-phase", "summarize", "--dry-run"])

        self.assertTrue(args.portfolio_once)
        self.assertEqual(args.portfolio_phase, "summarize")
        self.assertTrue(args.dry_run)


if __name__ == "__main__":
    unittest.main()
