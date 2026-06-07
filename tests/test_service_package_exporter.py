import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.revenue_scoring import RevenueOpportunity
from farm_loop.service_package_exporter import ServicePackageExporter, build_service_package_rows


def make_opportunity(channel="paid_setup_kit"):
    return RevenueOpportunity(
        source="idea_catalog",
        external_id="offer-webhook-setup-service",
        title="Webhook Setup Service",
        url="https://example.com/idea",
        problem="Small SaaS teams need Stripe or Buy Me a Coffee webhooks wired into Supabase safely.",
        tags=["webhook", "supabase", "stripe", "service"],
        channel=channel,
        payout_estimate_usd=299,
        conversion_probability=0.05,
        estimated_cost_usd=8,
        risk_penalty_usd=2,
        build_minutes=60,
        expected_value_usd=4.95,
    )


class ServicePackageExporterTests(unittest.TestCase):
    def test_build_rows_filters_paid_setup_and_tracks_checkout_and_intake(self):
        rows = build_service_package_rows(
            [make_opportunity(), make_opportunity(channel="digital_product")],
            payment_urls={"fixed_scope_service": "https://buy.stripe.com/setup"},
            intake_url="https://forms.example.com/setup",
            click_redirect_url="https://track.example.com/click",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["slug"], "offer-webhook-setup-service")
        self.assertEqual(rows[0]["offer_key"], "idea_catalog:offer-webhook-setup-service:fixed_scope_service")
        self.assertGreaterEqual(rows[0]["price_usd"], 199)
        self.assertIn("target=https%3A%2F%2Fbuy.stripe.com%2Fsetup", rows[0]["checkout_url"])
        self.assertIn("target=https%3A%2F%2Fforms.example.com%2Fsetup", rows[0]["intake_url"])
        self.assertIn("Confirm access boundaries", rows[0]["delivery_steps"])

    def test_exporter_writes_service_package_files_for_manual_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            exporter = ServicePackageExporter(
                Path(directory) / "service-packages",
                payment_urls={"fixed_scope_service": "https://buy.stripe.com/setup"},
                intake_url="https://forms.example.com/setup",
                click_redirect_url="https://track.example.com/click",
            )

            paths = exporter.export([make_opportunity()])

            output_dir = Path(directory) / "service-packages"
            manifest = json.loads((output_dir / "service_packages.json").read_text(encoding="utf-8"))
            catalog = (output_dir / "SERVICE_PACKAGES.md").read_text(encoding="utf-8")
            service_dir = output_dir / "offer-webhook-setup-service"
            proposal = (service_dir / "PROPOSAL.md").read_text(encoding="utf-8")
            scope = (service_dir / "SCOPE.md").read_text(encoding="utf-8")
            checklist = (service_dir / "DELIVERY_CHECKLIST.md").read_text(encoding="utf-8")
            handoff = (service_dir / "HANDOFF.md").read_text(encoding="utf-8")
            service_json = json.loads((service_dir / "service.json").read_text(encoding="utf-8"))
            page = (service_dir / "index.html").read_text(encoding="utf-8")

        self.assertIn("service_packages.json", [path.name for path in paths])
        self.assertEqual(manifest[0]["title"], "Webhook Setup Service")
        self.assertIn("# Service Packages", catalog)
        self.assertIn("Fixed Scope Proposal", proposal)
        self.assertIn("Out of scope", scope)
        self.assertIn("Confirm access boundaries", checklist)
        self.assertIn("Handoff", handoff)
        self.assertEqual(service_json["offer_key"], "idea_catalog:offer-webhook-setup-service:fixed_scope_service")
        self.assertIn("https://track.example.com/click", page)


if __name__ == "__main__":
    unittest.main()
