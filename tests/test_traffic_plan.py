import json
import tempfile
import unittest
from pathlib import Path

from farm_loop.offers import OfferDraft
from farm_loop.revenue_scoring import RevenueOpportunity
from farm_loop.traffic_plan import TrafficPlanExporter, build_traffic_plan


def make_opportunity(
    *,
    channel="microtool_seo",
    external_id="supabase-rls-checker",
    title="Supabase RLS policy checker",
):
    return RevenueOpportunity(
        source="manual_keywords",
        external_id=external_id,
        title=title,
        url=f"file://keywords.csv#{external_id}",
        problem="Developers need a quick way to review RLS mistakes before launch.",
        tags=["supabase", "rls"],
        channel=channel,
        payout_estimate_usd=300,
        conversion_probability=0.08,
        estimated_cost_usd=5,
        risk_penalty_usd=1,
        build_minutes=45,
        expected_value_usd=21.5,
    )


def make_offer(
    *,
    external_id="supabase-rls-checker",
    channel="microtool_seo",
    offer_type="setup_service",
    price_usd=49,
    payment_url="",
):
    return OfferDraft(
        source="manual_keywords",
        external_id=external_id,
        channel=channel,
        offer_type=offer_type,
        offer_key=f"manual_keywords:{external_id}:{offer_type}",
        title="Supabase RLS policy checker setup help",
        description="Apply the checker to a real Supabase project.",
        price_usd=price_usd,
        cta_label="Get setup help",
        payment_url=payment_url,
    )


class TrafficPlanTests(unittest.TestCase):
    def test_build_traffic_plan_maps_opportunities_to_owned_and_allowed_channels(self):
        plan = build_traffic_plan(
            opportunities=[make_opportunity()],
            offers=[make_offer(payment_url="https://buy.stripe.com/setup")],
            site_base_url="https://revenue.example",
            click_redirect_url="https://track.example/click",
            lead_capture_url="https://forms.example/signup",
        )

        self.assertTrue(plan["traffic_ready"])
        self.assertEqual(plan["summary"]["tracks"], 1)
        self.assertEqual(plan["tracks"][0]["external_id"], "supabase-rls-checker")
        self.assertEqual(plan["tracks"][0]["primary_surface"], "owned_site_seo")
        self.assertIn("owned microtool page", plan["tracks"][0]["distribution_steps"][0].lower())
        self.assertIn("newsletter", plan["tracks"][0]["allowed_surfaces"])
        self.assertIn("click_events", plan["metrics"][0])
        self.assertTrue(any("No third-party autoposting" in guardrail for guardrail in plan["guardrails"]))

    def test_build_traffic_plan_reports_missing_setup_before_autonomous_distribution(self):
        plan = build_traffic_plan(
            opportunities=[make_opportunity(channel="article_affiliate", title="FastAPI hosting comparison")],
            offers=[make_offer(payment_url="")],
            site_base_url="",
            click_redirect_url="",
            lead_capture_url="",
        )

        self.assertFalse(plan["traffic_ready"])
        self.assertIn("Set SITE_BASE_URL", plan["required_setup"])
        self.assertIn("Connect OFFER_PAYMENT_URLS", plan["required_setup"])
        self.assertEqual(plan["tracks"][0]["primary_surface"], "owned_article_seo")
        self.assertIn("affiliate disclosure", " ".join(plan["tracks"][0]["distribution_steps"]).lower())

    def test_exporter_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "traffic-plan"
            exporter = TrafficPlanExporter(output_dir)

            written = exporter.export(
                opportunities=[make_opportunity()],
                offers=[make_offer(payment_url="https://buy.stripe.com/setup")],
                site_base_url="https://revenue.example",
                click_redirect_url="https://track.example/click",
                lead_capture_url="https://forms.example/signup",
            )
            plan = json.loads((output_dir / "traffic_plan.json").read_text(encoding="utf-8"))
            markdown = (output_dir / "TRAFFIC_PLAN.md").read_text(encoding="utf-8")

        self.assertEqual(sorted(path.name for path in written), ["TRAFFIC_PLAN.md", "traffic_plan.json"])
        self.assertTrue(plan["traffic_ready"])
        self.assertIn("# Traffic Plan", markdown)
        self.assertIn("Supabase RLS policy checker", markdown)
        self.assertIn("No third-party autoposting", markdown)

    def test_build_traffic_plan_prioritizes_higher_ticket_paths_over_low_ticket_support(self):
        low_ticket = make_opportunity(
            channel="open_source_sponsorship",
            external_id="repo-sponsor",
            title="Sponsor-only repo helper",
        )
        high_ticket = make_opportunity(
            channel="microtool_seo",
            external_id="supabase-rls-checker",
            title="Supabase RLS policy checker",
        )

        plan = build_traffic_plan(
            opportunities=[low_ticket, high_ticket],
            offers=[
                make_offer(
                    external_id="repo-sponsor",
                    channel="open_source_sponsorship",
                    offer_type="sponsorship",
                    price_usd=5,
                ),
                make_offer(offer_type="setup_service", price_usd=49),
            ],
            site_base_url="https://revenue.example",
        )

        self.assertEqual(plan["tracks"][0]["external_id"], "supabase-rls-checker")
        self.assertEqual(plan["tracks"][0]["best_offer"]["price_usd"], 49.0)
        self.assertEqual(plan["tracks"][1]["best_offer"]["price_usd"], 5.0)


if __name__ == "__main__":
    unittest.main()
