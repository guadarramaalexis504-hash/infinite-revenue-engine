import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.activation_manifest import ActivationManifestExporter, build_activation_manifest_rows
from farm_loop.assets import AssetDraft
from farm_loop.offers import generate_offers
from farm_loop.revenue_scoring import RevenueOpportunity


def make_opportunity(channel="paid_setup_kit", external_id="offer-webhook-setup-service"):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id=external_id,
        title="Webhook Setup Service",
        url=f"file://ideas#{external_id}",
        problem="Creators need payment webhooks saved into Supabase.",
        tags=["webhook", "supabase", "stripe"],
        channel=channel,
        payout_estimate_usd=299,
        conversion_probability=0.12,
        estimated_cost_usd=20,
        risk_penalty_usd=5,
        build_minutes=90,
    )


def make_assets():
    return [
        AssetDraft("support_offer", "Support Offer", "# Offer"),
        AssetDraft("landing_page_copy", "Landing Copy", "# Landing"),
    ]


class ActivationManifestTests(unittest.TestCase):
    def test_build_rows_links_opportunity_to_artifacts_checkout_and_validation_command(self):
        opportunity = make_opportunity()
        offers = generate_offers(
            opportunity,
            payment_urls={"fixed_scope_service": "https://buy.stripe.com/setup"},
        )

        rows = build_activation_manifest_rows(
            [(opportunity, make_assets())],
            offers=offers,
            artifact_dirs={
                "asset_output_dir": "out/revenue-bundle/assets",
                "site_output_dir": "out/revenue-bundle/site",
                "offer_output_dir": "out/revenue-bundle/offers",
                "checkout_setup_output_dir": "out/revenue-bundle/checkout-setup",
                "tracking_deploy_output_dir": "out/revenue-bundle/tracking-deploy",
                "launch_queue_output_dir": "out/revenue-bundle/launch-queue",
                "roadmap_output_dir": "out/revenue-bundle/roadmap",
            },
            activation_report={"ready": False, "next_actions": ["Run gh auth login"]},
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["external_id"], "offer-webhook-setup-service")
        self.assertEqual(row["offer_keys"], ["idea_catalog:offer-webhook-setup-service:fixed_scope_service"])
        self.assertTrue(row["payment_urls_configured"])
        self.assertEqual(row["activation_blockers"], ["Run gh auth login"])
        self.assertEqual(row["local_paths"]["site_page"], "out/revenue-bundle/site/offer-webhook-setup-service/index.html")
        self.assertEqual(
            row["local_paths"]["asset_manifest"],
            "out/revenue-bundle/assets/idea-catalog-offer-webhook-setup-service/manifest.json",
        )
        self.assertEqual(row["local_paths"]["checkout_setup"], "out/revenue-bundle/checkout-setup/CHECKOUT_SETUP.md")
        self.assertIn("--record-conversion", row["commands"]["record_test_conversion"])
        self.assertIn("idea_catalog:offer-webhook-setup-service:fixed_scope_service", row["commands"]["record_test_conversion"])
        self.assertIn("manual review", row["publish_gate"].lower())

    def test_exporter_writes_json_markdown_and_runbook(self):
        opportunity = make_opportunity(channel="microtool_seo", external_id="microtool-supabase-rls")
        offers = generate_offers(opportunity, payment_urls={"support": "https://buymeacoffee.com/example"})

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "activation"
            exporter = ActivationManifestExporter(
                output_dir,
                repo_root="C:/Users/guada/OneDrive/Documentos/15 dlrs",
                protected_workspaces=["C:/Users/guada/OneDrive/Documentos/New project/aipickd-pipeline"],
                artifact_dirs={
                    "site_output_dir": Path(directory) / "site",
                    "microtool_output_dir": Path(directory) / "site" / "tools",
                    "offer_output_dir": Path(directory) / "offers",
                },
            )

            written = exporter.export(
                [(opportunity, make_assets())],
                offers=offers,
                activation_report={"ready": True, "next_actions": []},
            )
            manifest = json.loads((output_dir / "activation_manifest.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "ACTIVATE_NOW.md").read_text(encoding="utf-8")
            runbook = (output_dir / "RUNBOOK.md").read_text(encoding="utf-8")
            handoff = (output_dir / "CLAUDE_HANDOFF.md").read_text(encoding="utf-8")

        self.assertEqual(
            sorted(path.name for path in written),
            ["ACTIVATE_NOW.md", "CLAUDE_HANDOFF.md", "RUNBOOK.md", "activation_manifest.json"],
        )
        expected_root = Path(directory).as_posix()
        self.assertEqual(
            manifest[0]["local_paths"]["microtool_page"],
            f"{expected_root}/site/tools/microtool-supabase-rls/index.html",
        )
        self.assertIn("Webhook/sale test", runbook)
        self.assertIn("microtool-supabase-rls", markdown)
        self.assertIn("https://buymeacoffee.com/example", markdown)
        self.assertIn("C:/Users/guada/OneDrive/Documentos/15 dlrs", handoff)
        self.assertIn("aipickd-pipeline", handoff)
        self.assertIn("Do not use destructive git commands", handoff)
        self.assertIn("supabase/schema.sql", handoff)
        self.assertIn(".\\scripts\\configure-github.ps1", handoff)
        self.assertIn("python -m unittest discover -s tests -v", handoff)


if __name__ == "__main__":
    unittest.main()
