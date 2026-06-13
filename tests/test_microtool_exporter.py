import tempfile
import unittest
from pathlib import Path

from farm_loop.microtool_exporter import MicrotoolExporter, is_supported_microtool
from farm_loop.revenue_scoring import RevenueOpportunity, score_opportunity


def opportunity(title, external_id, tags):
    return score_opportunity(
        RevenueOpportunity(
            source="idea_catalog",
            external_id=external_id,
            title=title,
            url=f"file://ideas#{external_id}",
            problem=f"Builders need {title}.",
            tags=tags,
            channel="microtool_seo",
            payout_estimate_usd=250,
            conversion_probability=0.08,
            estimated_cost_usd=4,
            risk_penalty_usd=1,
            build_minutes=35,
        )
    )


class MicrotoolExporterTests(unittest.TestCase):
    def test_detects_supported_microtools_from_tags_and_titles(self):
        self.assertTrue(
            is_supported_microtool(
                opportunity("Supabase RLS Policy Checker", "rls-checker", ["supabase", "rls"])
            )
        )
        self.assertTrue(
            is_supported_microtool(
                opportunity("GitHub Actions YAML Validator", "actions-yaml", ["github-actions", "yaml"])
            )
        )
        self.assertFalse(
            is_supported_microtool(
                opportunity("Generic Setup Service", "setup", ["consulting"])
            )
        )

    def test_exports_interactive_supabase_rls_checker(self):
        opp = opportunity("Supabase RLS Policy Checker", "supabase-rls", ["supabase", "rls"])

        with tempfile.TemporaryDirectory() as directory:
            written = MicrotoolExporter(directory, tip_url="https://buymeacoffee.com/example").export_portfolio(
                [(opp, [])]
            )
            page = (Path(directory) / "supabase-rls" / "index.html").read_text(encoding="utf-8")

        self.assertEqual(len(written), 2)
        self.assertIn("Supabase RLS Policy Checker", page)
        self.assertIn("textarea", page)
        self.assertIn("analyzeRls", page)
        self.assertIn("enable row level security", page)
        self.assertIn("create policy", page)
        self.assertIn("buymeacoffee.com/example?", page)

    def test_exports_interactive_github_actions_checker(self):
        opp = opportunity("GitHub Actions YAML Validator", "actions-yaml", ["github-actions", "yaml"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "actions-yaml" / "index.html").read_text(encoding="utf-8")
            index = (Path(directory) / "index.html").read_text(encoding="utf-8")

        self.assertIn("GitHub Actions YAML Validator", page)
        self.assertIn("textarea", page)
        self.assertIn("analyzeActions", page)
        self.assertIn("pull_request_target", page)
        self.assertIn("permissions: write-all", page)
        self.assertIn("actions-yaml/", index)

    def test_skips_unsupported_opportunities(self):
        opp = opportunity("Generic Setup Service", "setup", ["consulting"])

        with tempfile.TemporaryDirectory() as directory:
            written = MicrotoolExporter(directory).export_portfolio([(opp, [])])

        self.assertEqual(written, [])

    def test_detects_all_new_microtool_kinds(self):
        cases = [
            ("Cron Expression Explainer", "cron-explainer", ["cron", "automation"]),
            ("Environment Variable Auditor", "env-auditor", ["env", "security"]),
            ("Docker Compose Env Checker", "docker-env", ["docker", "env"]),
            ("OpenAI API Cost Calculator", "openai-cost", ["openai-api", "costs", "calculator"]),
            ("Webhook Signature Tester", "webhook-sig", ["webhooks", "security"]),
            ("Stripe Webhook Signature Verifier", "stripe-webhook", ["stripe", "webhooks"]),
            ("Regex Explainer and Test Case Generator", "regex-explainer", ["regex", "testing"]),
        ]
        for title, external_id, tags in cases:
            with self.subTest(tool=external_id):
                self.assertTrue(is_supported_microtool(opportunity(title, external_id, tags)))

    def test_exports_interactive_cron_explainer(self):
        opp = opportunity("Cron Expression Explainer", "cron-explainer", ["cron", "github-actions"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "cron-explainer" / "index.html").read_text(encoding="utf-8")

        self.assertIn("explainCron", page)
        self.assertIn("minute", page.lower())
        self.assertIn("next runs", page.lower())

    def test_exports_interactive_env_auditor(self):
        opp = opportunity("Environment Variable Auditor", "env-auditor", ["env", "security"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "env-auditor" / "index.html").read_text(encoding="utf-8")

        self.assertIn("auditEnv", page)
        self.assertIn("placeholder", page.lower())
        self.assertIn("duplicate", page.lower())
        self.assertIn("never leaves your browser", page.lower())

    def test_exports_interactive_docker_compose_checker(self):
        opp = opportunity("Docker Compose Env Checker", "docker-env", ["docker", "env"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "docker-env" / "index.html").read_text(encoding="utf-8")

        self.assertIn("checkCompose", page)
        self.assertIn("env_file", page)

    def test_exports_interactive_openai_cost_calculator(self):
        opp = opportunity("OpenAI API Cost Calculator", "openai-cost", ["openai-api", "costs"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "openai-cost" / "index.html").read_text(encoding="utf-8")

        self.assertIn("calculateCost", page)
        self.assertIn("per month", page.lower())
        self.assertIn("verify current pricing", page.lower())

    def test_exports_interactive_webhook_signature_tester(self):
        opp = opportunity("Webhook Signature Tester", "webhook-sig", ["webhooks", "security"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "webhook-sig" / "index.html").read_text(encoding="utf-8")

        self.assertIn("computeSignature", page)
        self.assertIn("HMAC", page)
        self.assertIn("never leaves your browser", page.lower())

    def test_exports_interactive_llmstxt_generator(self):
        opp = opportunity("LlmstxtGen - generador de llms.txt", "llmstxt-gen", ["llms-txt-generator", "seo"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "llmstxt-gen" / "index.html").read_text(encoding="utf-8")

        self.assertIn("generateLlms", page)
        self.assertIn("llms.txt", page)

    def test_exports_interactive_ai_robots_generator(self):
        opp = opportunity("AIRobots - robots.txt para crawlers de AI", "ai-robots", ["robots-txt", "ai-crawlers"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "ai-robots" / "index.html").read_text(encoding="utf-8")

        self.assertIn("generateRobots", page)
        self.assertIn("GPTBot", page)
        self.assertIn("ClaudeBot", page)

    def test_detects_and_exports_supabase_pricing_calculator(self):
        opp = opportunity("SupaCost - Supabase Pricing Calculator", "supacost", ["supabase-pricing-calculator", "supabase-egress-cost"])
        self.assertTrue(is_supported_microtool(opp))
        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "supacost" / "index.html").read_text(encoding="utf-8")
        self.assertIn("calcSupabase", page)
        self.assertIn("free tier", page.lower())
        self.assertIn("egress", page.lower())

    def test_detects_and_exports_rls_policy_generator(self):
        opp = opportunity("RLS Forge - Supabase RLS Policy Generator", "rls-forge", ["supabase-rls-policy-generator", "create-policy-postgres"])
        self.assertTrue(is_supported_microtool(opp))
        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "rls-forge" / "index.html").read_text(encoding="utf-8")
        self.assertIn("generatePolicy", page)
        self.assertIn("create policy", page.lower())
        self.assertIn("auth.uid()", page)

    def test_rls_forge_does_not_collide_with_rls_checker(self):
        # The plain checker idea must still render the analyzer, not the generator.
        checker = opportunity("Supabase RLS Policy Checker", "rls-checker", ["supabase", "rls", "security"])
        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(checker, [])])
            page = (Path(directory) / "rls-checker" / "index.html").read_text(encoding="utf-8")
        self.assertIn("analyzeRls", page)
        self.assertNotIn("generatePolicy", page)

    def test_exports_interactive_regex_tester(self):
        opp = opportunity("Regex Explainer and Test Case Generator", "regex-explainer", ["regex", "testing"])

        with tempfile.TemporaryDirectory() as directory:
            MicrotoolExporter(directory).export_portfolio([(opp, [])])
            page = (Path(directory) / "regex-explainer" / "index.html").read_text(encoding="utf-8")

        self.assertIn("testRegex", page)
        self.assertIn("matches", page.lower())


if __name__ == "__main__":
    unittest.main()
