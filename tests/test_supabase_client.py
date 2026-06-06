import unittest

from farm_loop.supabase_client import SupabaseClient


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self.payload = payload if payload is not None else []
        self.status_code = status_code
        self.text = str(self.payload)

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.calls = []
        self.responses = []

    def queue(self, payload=None, status_code=200):
        self.responses.append(FakeResponse(payload, status_code))

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        if self.responses:
            return self.responses.pop(0)
        return FakeResponse([{"id": "row-1"}], 200)


class SupabaseClientTests(unittest.TestCase):
    def test_insert_event_posts_to_events_with_required_headers(self):
        session = FakeSession()
        client = SupabaseClient("https://project.supabase.co", "secret-key", session=session)

        client.insert_event("run-1", "run_started", {"ok": True})

        call = session.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://project.supabase.co/rest/v1/events")
        self.assertEqual(call["headers"]["apikey"], "secret-key")
        self.assertEqual(call["headers"]["Authorization"], "Bearer secret-key")
        self.assertEqual(call["headers"]["Content-Type"], "application/json")
        self.assertEqual(call["headers"]["Prefer"], "return=representation")
        self.assertEqual(
            call["json"],
            {"run_id": "run-1", "event_type": "run_started", "payload": {"ok": True}},
        )

    def test_upsert_opportunity_uses_on_conflict_and_merge_prefer_header(self):
        session = FakeSession()
        client = SupabaseClient("https://project.supabase.co/", "secret-key", session=session)

        client.upsert_opportunity({"source": "stackexchange", "external_id": "123"})

        call = session.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"],
            "https://project.supabase.co/rest/v1/opportunities?on_conflict=source,external_id",
        )
        self.assertEqual(call["headers"]["Prefer"], "resolution=merge-duplicates,return=representation")

    def test_total_tips_usd_sums_numeric_amounts(self):
        session = FakeSession()
        session.queue([{"amount_usd": "3.50"}, {"amount_usd": 2}], 200)
        client = SupabaseClient("https://project.supabase.co", "secret-key", session=session)

        self.assertEqual(client.total_tips_usd(), 5.5)
        self.assertEqual(session.calls[0]["method"], "GET")
        self.assertEqual(
            session.calls[0]["url"],
            "https://project.supabase.co/rest/v1/tip_events?select=amount_usd",
        )


if __name__ == "__main__":
    unittest.main()
