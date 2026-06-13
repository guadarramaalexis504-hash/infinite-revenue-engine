import unittest

from farm_loop.revenue_winners import (
    OfferPerformance,
    build_winner_plan,
    generate_variant_opportunities,
    summarize_offer_performance,
)


def offer(offer_key, *, opportunity_id="opp1", title="GitHub Actions YAML Validator", channel="microtool_seo", price=49.0):
    return {
        "id": "row-" + offer_key,
        "opportunity_id": opportunity_id,
        "channel": channel,
        "title": title,
        "price_usd": price,
        "payload": {"offer_key": offer_key, "offer_type": offer_key.rsplit(":", 1)[-1]},
    }


def click(offer_key):
    return {"offer_id": None, "source": "revenue_site", "payload": {"offer_key": offer_key}}


def conversion(offer_key, amount):
    return {"offer_id": None, "source": "microtool_seo", "amount_usd": amount, "payload": {"offer_key": offer_key}}


class WinnerSummaryTests(unittest.TestCase):
    def test_summarize_aggregates_clicks_conversions_revenue(self):
        offers = [offer("kw:a:setup_service"), offer("kw:b:digital_product", title="RLS Pack", price=19)]
        clicks = [click("kw:a:setup_service"), click("kw:a:setup_service"), click("kw:b:digital_product")]
        conversions = [conversion("kw:a:setup_service", 49.0)]

        perf = summarize_offer_performance(offers, clicks, conversions)
        by_key = {p.offer_key: p for p in perf}
        self.assertEqual(by_key["kw:a:setup_service"].clicks, 2)
        self.assertEqual(by_key["kw:a:setup_service"].conversions, 1)
        self.assertEqual(by_key["kw:a:setup_service"].revenue, 49.0)
        self.assertEqual(by_key["kw:b:digital_product"].clicks, 1)
        self.assertEqual(by_key["kw:b:digital_product"].revenue, 0.0)

    def test_summary_is_sorted_by_revenue_then_clicks(self):
        offers = [offer("kw:a:x"), offer("kw:b:x", opportunity_id="opp2"), offer("kw:c:x", opportunity_id="opp3")]
        clicks = [click("kw:b:x"), click("kw:b:x"), click("kw:c:x")]
        conversions = [conversion("kw:c:x", 99.0)]
        perf = summarize_offer_performance(offers, clicks, conversions)
        self.assertEqual(perf[0].offer_key, "kw:c:x")  # has revenue -> first
        self.assertEqual(perf[1].offer_key, "kw:b:x")  # more clicks -> second


class VariantGenerationTests(unittest.TestCase):
    def test_generates_distinct_variant_opportunities(self):
        winner = OfferPerformance(
            offer_key="kw:rls:setup_service",
            title="Supabase RLS Setup",
            channel="paid_setup_kit",
            price_usd=199.0,
            clicks=10,
            conversions=2,
            revenue=398.0,
        )
        variants = generate_variant_opportunities(winner, count=3)
        self.assertEqual(len(variants), 3)
        ids = {v["external_id"] for v in variants}
        self.assertEqual(len(ids), 3)  # all unique
        for v in variants:
            self.assertEqual(v["source"], "winner_variant")
            self.assertEqual(v["channel"], "paid_setup_kit")
            self.assertGreater(v["payout_estimate_usd"], 0)
            self.assertIn("Supabase RLS Setup", v["title"])

    def test_variant_payout_tracks_winner_price(self):
        winner = OfferPerformance("a:b:digital_product", "Cron Pack", "digital_product", 19.0, 5, 1, 19.0)
        variants = generate_variant_opportunities(winner, count=2)
        self.assertTrue(all(v["payout_estimate_usd"] >= 19.0 for v in variants))


class WinnerPlanTests(unittest.TestCase):
    def test_plan_only_makes_variants_for_offers_with_revenue(self):
        offers = [offer("win:a:setup_service"), offer("lose:b:digital_product", opportunity_id="opp2")]
        clicks = [click("lose:b:digital_product")] * 5
        conversions = [conversion("win:a:setup_service", 49.0)]

        plan = build_winner_plan(offers=offers, clicks=clicks, conversions=conversions, max_variants_per_winner=2)
        self.assertEqual(len(plan.winners), 1)
        self.assertEqual(plan.winners[0].offer_key, "win:a:setup_service")
        self.assertEqual(len(plan.variant_opportunities), 2)
        self.assertTrue(all(v["source"] == "winner_variant" for v in plan.variant_opportunities))

    def test_plan_is_empty_without_conversions(self):
        offers = [offer("kw:a:x")]
        clicks = [click("kw:a:x")] * 9
        plan = build_winner_plan(offers=offers, clicks=clicks, conversions=[])
        self.assertEqual(plan.winners, [])
        self.assertEqual(plan.variant_opportunities, [])


if __name__ == "__main__":
    unittest.main()
