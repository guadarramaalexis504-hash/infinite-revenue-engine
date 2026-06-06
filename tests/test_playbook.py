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
        ]:
            self.assertIn(required, body)


if __name__ == "__main__":
    unittest.main()
