import unittest

from farm_loop.main import RunSummary, run_once
from farm_loop.sources_stackexchange import SearchResult


class FakeSource:
    def search_unanswered(self, page_size=20):
        return SearchResult(
            questions=[
                {
                    "question_id": 900,
                    "title": "Python Supabase REST insert 401 in GitHub Actions",
                    "body": "<p>How should I pass headers?</p><pre><code>requests.post(url)</code></pre>",
                    "tags": ["python", "supabase"],
                    "answer_count": 0,
                    "is_answered": False,
                    "view_count": 120,
                    "score": 1,
                    "creation_date": 1780680000,
                    "link": "https://stackoverflow.com/questions/900/example",
                }
            ],
            backoff_seconds=7,
            quota_remaining=9990,
        )


class FakeSupabase:
    def __init__(self, total=0):
        self.total = total
        self.events = []
        self.opportunities = []
        self.drafts = []
        self.finished = []

    def create_run(self):
        return "run-1"

    def finish_run(self, run_id, status, error=None):
        self.finished.append((run_id, status, error))

    def insert_event(self, run_id, event_type, payload):
        self.events.append((run_id, event_type, payload))

    def upsert_opportunity(self, payload):
        self.opportunities.append(payload)
        return [{"id": "opp-1", **payload}]

    def insert_draft(self, payload):
        self.drafts.append(payload)

    def total_tips_usd(self):
        return self.total


class FakeDraftGenerator:
    def generate(self, question, tip_url):
        return type(
            "Draft",
            (),
            {
                "answer_markdown": "Use explicit Supabase REST headers.",
                "code_snippet": "headers = {'apikey': key}",
                "raw_response": {"ok": True},
            },
        )()


class MainLoopTests(unittest.TestCase):
    def test_run_once_records_opportunity_draft_and_backoff_event(self):
        supabase = FakeSupabase(total=0)

        summary = run_once(
            source_client=FakeSource(),
            supabase=supabase,
            draft_generator=FakeDraftGenerator(),
            tip_url="https://buymeacoffee.com/example",
            max_drafts=3,
            target_usd=15,
        )

        self.assertIsInstance(summary, RunSummary)
        self.assertEqual(summary.generated_drafts, 1)
        self.assertEqual(supabase.opportunities[0]["external_id"], "900")
        self.assertEqual(supabase.drafts[0]["opportunity_id"], "opp-1")
        self.assertIn("stackexchange_backoff", [event[1] for event in supabase.events])
        self.assertEqual(supabase.finished, [("run-1", "success", None)])

    def test_run_once_keeps_generating_after_target_by_default(self):
        supabase = FakeSupabase(total=200)

        summary = run_once(
            source_client=FakeSource(),
            supabase=supabase,
            draft_generator=FakeDraftGenerator(),
            tip_url="https://buymeacoffee.com/example",
            max_drafts=3,
            target_usd=15,
        )

        self.assertEqual(summary.status, "success")
        self.assertEqual(summary.generated_drafts, 1)
        self.assertEqual(supabase.opportunities[0]["external_id"], "900")
        self.assertEqual(supabase.drafts[0]["opportunity_id"], "opp-1")
        self.assertIn("target_reached", [event[1] for event in supabase.events])

    def test_run_once_switches_to_monitoring_after_target_when_stop_after_target_enabled(self):
        supabase = FakeSupabase(total=15)

        summary = run_once(
            source_client=FakeSource(),
            supabase=supabase,
            draft_generator=FakeDraftGenerator(),
            tip_url="https://buymeacoffee.com/example",
            max_drafts=3,
            target_usd=15,
            stop_after_target=True,
        )

        self.assertEqual(summary.status, "monitoring")
        self.assertEqual(summary.generated_drafts, 0)
        self.assertEqual(supabase.opportunities, [])
        self.assertEqual(supabase.drafts, [])


if __name__ == "__main__":
    unittest.main()
