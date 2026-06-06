import unittest

from farm_loop.revenue_scoring import (
    RevenueOpportunity,
    compute_expected_value,
    rank_revenue_opportunities,
)


class RevenueScoringTests(unittest.TestCase):
    def test_expected_value_formula_penalizes_cost_and_risk(self):
        opportunity = RevenueOpportunity(
            source="github",
            external_id="owner/repo#42",
            title="Supabase RLS setup is confusing",
            url="https://github.com/owner/repo/issues/42",
            problem="Users need a safe RLS starter kit.",
            tags=["supabase", "rls", "github-actions"],
            channel="github_issue_helper",
            payout_estimate_usd=120,
            conversion_probability=0.12,
            estimated_cost_usd=3.50,
            risk_penalty_usd=2.00,
            build_minutes=45,
        )

        self.assertEqual(compute_expected_value(opportunity), 8.9)

    def test_rank_revenue_opportunities_prefers_high_value_reusable_low_risk_work(self):
        good = RevenueOpportunity(
            source="manual_keywords",
            external_id="kw-1",
            title="GitHub Actions YAML checker",
            url="file://keywords.csv#kw-1",
            problem="People break workflow YAML often.",
            tags=["github-actions", "yaml"],
            channel="microtool_seo",
            payout_estimate_usd=250,
            conversion_probability=0.08,
            estimated_cost_usd=4,
            risk_penalty_usd=1,
            build_minutes=30,
        )
        weak = RevenueOpportunity(
            source="manual_keywords",
            external_id="kw-2",
            title="Generic coding tips",
            url="file://keywords.csv#kw-2",
            problem="Too broad.",
            tags=["general"],
            channel="article_affiliate",
            payout_estimate_usd=20,
            conversion_probability=0.02,
            estimated_cost_usd=5,
            risk_penalty_usd=3,
            build_minutes=120,
        )

        ranked = rank_revenue_opportunities([weak, good], max_items=1)

        self.assertEqual(ranked[0].external_id, "kw-1")
        self.assertGreater(ranked[0].expected_value_usd, 0)

    def test_rank_revenue_opportunities_deduplicates_same_channel_title_across_sources(self):
        lower_value = RevenueOpportunity(
            source="manual_keywords",
            external_id="kw-supabase-rls",
            title="Supabase RLS policy checker",
            url="file://keywords.csv#kw-supabase-rls",
            problem="Developers need RLS feedback.",
            tags=["supabase", "rls"],
            channel="microtool_seo",
            payout_estimate_usd=250,
            conversion_probability=0.08,
            estimated_cost_usd=5,
            risk_penalty_usd=1,
            build_minutes=45,
        )
        higher_value = RevenueOpportunity(
            source="idea_catalog",
            external_id="microtool-supabase-rls-policy-checker",
            title="Supabase RLS Policy Checker",
            url="file://ideas#microtool-supabase-rls-policy-checker",
            problem="Solo builders need a quick way to catch missing or unsafe RLS policies.",
            tags=["supabase", "rls", "postgres"],
            channel="microtool_seo",
            payout_estimate_usd=300,
            conversion_probability=0.08,
            estimated_cost_usd=5,
            risk_penalty_usd=1,
            build_minutes=45,
        )

        ranked = rank_revenue_opportunities([lower_value, higher_value], max_items=10)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].external_id, "microtool-supabase-rls-policy-checker")


if __name__ == "__main__":
    unittest.main()
