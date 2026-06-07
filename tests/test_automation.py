import tempfile
import unittest
from pathlib import Path

from farm_loop.automation import (
    build_activation_report,
    github_secret_names,
    insecure_supabase_key_vars,
    load_env_file,
    missing_required_vars,
    optional_github_secret_names,
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

    def test_optional_github_secret_names_include_click_redirect(self):
        self.assertEqual(
            optional_github_secret_names(),
            ["CLICK_REDIRECT_URL", "CONVERSION_WEBHOOK_TOKEN", "SERVICE_INTAKE_URL", "SITE_BASE_URL", "OFFER_PAYMENT_URLS"],
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

    def test_configure_github_script_supports_repo_override_and_optional_click_secret(self):
        script = Path("scripts/configure-github.ps1").read_text(encoding="utf-8")

        self.assertIn("[string]$Repo", script)
        self.assertIn("$optionalSecretNames", script)
        self.assertIn('"CLICK_REDIRECT_URL"', script)
        self.assertIn('"CONVERSION_WEBHOOK_TOKEN"', script)
        self.assertIn('"SERVICE_INTAKE_URL"', script)
        self.assertIn('"SITE_BASE_URL"', script)
        self.assertIn('"OFFER_PAYMENT_URLS"', script)
        self.assertIn("gh auth status", script)
        self.assertIn("No git remote found", script)

    def test_farm_loop_workflow_exposes_github_token_for_issue_discovery(self):
        workflow = Path(".github/workflows/farm-loop.yml").read_text(encoding="utf-8")

        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", workflow)

    def test_doctor_script_runs_automation_module(self):
        script = Path("scripts/doctor.ps1").read_text(encoding="utf-8")

        self.assertIn("-m", script)
        self.assertIn("farm_loop.automation", script)

    def test_activation_report_flags_external_blockers(self):
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "sb_secret_real",
            "OPENAI_API_KEY": "sk-real",
            "STACKEXCHANGE_KEY": "stack-key",
            "BUYMEACOFFEE_WEBHOOK_TOKEN": "webhook-token",
            "TIP_URL": "https://buymeacoffee.com/example",
        }

        report = build_activation_report(
            env=env,
            env_exists=True,
            schema_exists=True,
            farm_workflow_exists=True,
            pages_workflow_exists=True,
            git_remote_exists=False,
            gh_installed=True,
            gh_authenticated=False,
        )

        self.assertFalse(report["ready"])
        failed = {check["name"] for check in report["checks"] if check["status"] == "fail"}
        self.assertEqual(failed, {"git_remote", "gh_auth"})
        self.assertIn("Add git remote origin", report["next_actions"])
        self.assertIn("Run gh auth login", report["next_actions"])

    def test_activation_report_accepts_ready_configuration(self):
        env = {
            "SUPABASE_URL": "https://abc123.supabase.co",
            "SUPABASE_KEY": "sb_secret_real",
            "OPENAI_API_KEY": "sk-real",
            "STACKEXCHANGE_KEY": "stack-key",
            "BUYMEACOFFEE_WEBHOOK_TOKEN": "webhook-token",
            "TIP_URL": "https://buymeacoffee.com/example",
            "CLICK_REDIRECT_URL": "https://revenue.example.net/click",
        }

        report = build_activation_report(
            env=env,
            env_exists=True,
            schema_exists=True,
            farm_workflow_exists=True,
            pages_workflow_exists=True,
            git_remote_exists=True,
            gh_installed=True,
            gh_authenticated=True,
        )

        self.assertTrue(report["ready"])
        self.assertEqual(report["next_actions"], [])

    def test_workflow_sets_idea_catalog_path_for_portfolio_runs(self):
        workflow = Path(".github/workflows/farm-loop.yml").read_text(encoding="utf-8")

        self.assertIn('IDEA_CATALOG_PATH: "data/revenue_ideas.json"', workflow)

    def test_pages_workflow_deploys_owned_static_site_with_official_actions(self):
        workflow = Path(".github/workflows/pages-site.yml").read_text(encoding="utf-8")

        for required in [
            "permissions:",
            "pages: write",
            "id-token: write",
            "actions/configure-pages@v5",
            "actions/upload-pages-artifact@v4",
            "actions/deploy-pages@v4",
            "--site-output-dir out/site",
            "--microtool-output-dir out/site/tools",
            "path: out/site",
            "environment:",
            "name: github-pages",
        ]:
            self.assertIn(required, workflow)

    def test_env_example_documents_local_asset_output_dir(self):
        env_example = Path(".env.example").read_text(encoding="utf-8")
        gitignore = Path(".gitignore").read_text(encoding="utf-8")

        self.assertIn("ASSET_OUTPUT_DIR=out/revenue-assets", env_example)
        self.assertIn("SITE_OUTPUT_DIR=out/site", env_example)
        self.assertIn("CLICK_REDIRECT_URL=", env_example)
        self.assertIn("LAUNCH_QUEUE_OUTPUT_DIR=out/launch-queue", env_example)
        self.assertIn("MICROTOOL_OUTPUT_DIR=out/microtools", env_example)
        self.assertIn("OFFER_OUTPUT_DIR=out/offers", env_example)
        self.assertIn("CHECKOUT_SETUP_OUTPUT_DIR=out/checkout-setup", env_example)
        self.assertIn("CONVERSION_WEBHOOK_BASE_URL=", env_example)
        self.assertIn("TRACKING_DEPLOY_OUTPUT_DIR=out/tracking-deploy", env_example)
        self.assertIn("TRACKING_PUBLIC_BASE_URL=", env_example)
        self.assertIn("LEAD_MAGNET_OUTPUT_DIR=out/lead-magnets", env_example)
        self.assertIn("LEAD_CAPTURE_URL=", env_example)
        self.assertIn("DIGITAL_PRODUCT_OUTPUT_DIR=out/digital-products", env_example)
        self.assertIn("AFFILIATE_ARTICLE_OUTPUT_DIR=out/affiliate-articles", env_example)
        self.assertIn("AFFILIATE_URLS=", env_example)
        self.assertIn("SPONSOR_REPO_OUTPUT_DIR=out/sponsor-repos", env_example)
        self.assertIn("SPONSOR_URLS=", env_example)
        self.assertIn("ROADMAP_OUTPUT_DIR=out/roadmap", env_example)
        self.assertIn("BUNDLE_OUTPUT_DIR=out/revenue-bundle", env_example)
        self.assertIn("CLICK_ALLOWED_HOSTS=buymeacoffee.com,www.buymeacoffee.com", env_example)
        self.assertIn("CONVERSION_WEBHOOK_TOKEN=", env_example)
        self.assertIn("SERVICE_INTAKE_URL=", env_example)
        self.assertIn("OFFER_PAYMENT_URLS=", env_example)
        self.assertIn("SITE_BASE_URL=", env_example)
        self.assertIn("out/", gitignore)

    def test_pages_workflow_passes_optional_click_redirect_url(self):
        workflow = Path(".github/workflows/pages-site.yml").read_text(encoding="utf-8")

        self.assertIn("CLICK_REDIRECT_URL: ${{ secrets.CLICK_REDIRECT_URL }}", workflow)
        self.assertIn("--click-redirect-url \"${CLICK_REDIRECT_URL}\"", workflow)
        self.assertIn("SERVICE_INTAKE_URL: ${{ secrets.SERVICE_INTAKE_URL }}", workflow)
        self.assertIn("--intake-url \"${SERVICE_INTAKE_URL}\"", workflow)
        self.assertIn("SITE_BASE_URL: ${{ secrets.SITE_BASE_URL }}", workflow)
        self.assertIn("--site-base-url \"${SITE_BASE_URL}\"", workflow)
        self.assertIn("OFFER_PAYMENT_URLS: ${{ secrets.OFFER_PAYMENT_URLS }}", workflow)
        self.assertIn("--offer-payment-urls \"${OFFER_PAYMENT_URLS}\"", workflow)


if __name__ == "__main__":
    unittest.main()
