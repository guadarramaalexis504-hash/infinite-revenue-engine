import unittest
from pathlib import Path


class RevenueLoopPlaybookTests(unittest.TestCase):
    def test_playbook_documents_operating_context_and_missing_launch_steps(self):
        body = Path("docs/revenue-loop-playbook.md").read_text(encoding="utf-8")

        for required in [
            "Sonident",
            "aipickd",
            "IDEA_CATALOG_PATH",
            "--portfolio-once --portfolio-phase discover",
            "--portfolio-once --portfolio-phase generate",
            "$20,000",
            "GitHub remote",
            "Payment path",
            "--asset-output-dir",
            "ASSET_OUTPUT_DIR",
            "local review queue",
            "--site-output-dir",
            "SITE_OUTPUT_DIR",
            "owned static site",
            ".github/workflows/pages-site.yml",
            "GitHub Pages",
            "utm_campaign",
            "click_events",
            "CLICK_REDIRECT_URL",
            "click redirect",
            "--launch-queue-output-dir",
            "LAUNCH_QUEUE_OUTPUT_DIR",
            "launch queue",
            "--microtool-output-dir",
            "MICROTOOL_OUTPUT_DIR",
            "interactive microtools",
            "--offer-output-dir",
            "OFFER_OUTPUT_DIR",
            "offer catalog",
            "--portfolio-once --portfolio-phase summarize",
            "portfolio_snapshots",
            "--portfolio-once --portfolio-phase prune",
            "won",
            "paused",
            "--record-conversion",
            "CONVERSION_WEBHOOK_TOKEN",
            "offers/index.html",
            "SERVICE_INTAKE_URL",
            "intake/index.html",
        ]:
            self.assertIn(required, body)


if __name__ == "__main__":
    unittest.main()
