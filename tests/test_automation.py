import tempfile
import unittest
from pathlib import Path

from farm_loop.automation import (
    github_secret_names,
    insecure_supabase_key_vars,
    load_env_file,
    missing_required_vars,
    placeholder_vars,
)


class AutomationTests(unittest.TestCase):
    def test_load_env_file_parses_quotes_comments_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text(
                """
# comment
SUPABASE_URL="https://example.supabase.co"
SUPABASE_KEY='secret-key'
TIP_URL=https://buymeacoffee.com/example
EMPTY=
                """.strip(),
                encoding="utf-8",
            )

            values = load_env_file(env_path)

        self.assertEqual(values["SUPABASE_URL"], "https://example.supabase.co")
        self.assertEqual(values["SUPABASE_KEY"], "secret-key")
        self.assertEqual(values["TIP_URL"], "https://buymeacoffee.com/example")
        self.assertEqual(values["EMPTY"], "")

    def test_missing_required_vars_reports_only_absent_or_empty_values(self):
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "secret-key",
            "OPENAI_API_KEY": "",
            "STACKEXCHANGE_KEY": "stack-key",
            "BUYMEACOFFEE_WEBHOOK_TOKEN": "webhook-token",
            "TIP_URL": "https://buymeacoffee.com/example",
        }

        self.assertEqual(missing_required_vars(env), ["OPENAI_API_KEY"])

    def test_github_secret_names_match_workflow_required_secrets(self):
        self.assertEqual(
            github_secret_names(),
            [
                "SUPABASE_URL",
                "SUPABASE_KEY",
                "OPENAI_API_KEY",
                "STACKEXCHANGE_KEY",
                "BUYMEACOFFEE_WEBHOOK_TOKEN",
                "TIP_URL",
            ],
        )

    def test_placeholder_vars_detects_example_values(self):
        env = {
            "SUPABASE_URL": "https://your-project-ref.supabase.co",
            "SUPABASE_KEY": "real-looking-secret",
            "OPENAI_API_KEY": "sk-your-openai-key",
            "TIP_URL": "https://www.buymeacoffee.com/real-handle",
        }

        self.assertEqual(placeholder_vars(env), ["SUPABASE_URL", "OPENAI_API_KEY"])

    def test_insecure_supabase_key_vars_rejects_anon_and_publishable_keys(self):
        self.assertEqual(
            insecure_supabase_key_vars({"SUPABASE_KEY": "sb_publishable_abc"}),
            ["SUPABASE_KEY"],
        )
        self.assertEqual(
            insecure_supabase_key_vars({"SUPABASE_KEY": "eyJhbGciOi.fake.jwt"}),
            ["SUPABASE_KEY"],
        )
        self.assertEqual(insecure_supabase_key_vars({"SUPABASE_KEY": "sb_secret_real"}), [])

    def test_configure_github_script_uses_stdin_secret_set_supported_by_gh_cli(self):
        script = Path("scripts/configure-github.ps1").read_text(encoding="utf-8")

        self.assertNotIn("--body-file", script)
        self.assertIn("gh secret set $name --app actions", script)
        self.assertLess(script.index("foreach ($name in $secretNames)"), script.index("gh secret set $name"))

    def test_workflow_sets_idea_catalog_path_for_portfolio_runs(self):
        workflow = Path(".github/workflows/farm-loop.yml").read_text(encoding="utf-8")

        self.assertIn('IDEA_CATALOG_PATH: "data/revenue_ideas.json"', workflow)


if __name__ == "__main__":
    unittest.main()
