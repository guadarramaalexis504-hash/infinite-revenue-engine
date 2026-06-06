import unittest

from farm_loop.sources_stackexchange import StackExchangeClient


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.response


class StackExchangeClientTests(unittest.TestCase):
    def test_search_unanswered_builds_advanced_search_request_and_returns_backoff(self):
        session = FakeSession(
            FakeResponse(
                {
                    "items": [{"question_id": 1, "title": "How to use Supabase REST?"}],
                    "backoff": 12,
                    "quota_remaining": 9999,
                }
            )
        )
        client = StackExchangeClient(
            key="se-key",
            tags="python;supabase",
            session=session,
        )

        result = client.search_unanswered(page_size=20)

        call = session.calls[0]
        self.assertEqual(call["url"], "https://api.stackexchange.com/2.3/search/advanced")
        self.assertEqual(call["params"]["site"], "stackoverflow")
        self.assertEqual(call["params"]["accepted"], "False")
        self.assertEqual(call["params"]["answers"], 0)
        self.assertEqual(call["params"]["closed"], "False")
        self.assertEqual(call["params"]["tagged"], "python;supabase")
        self.assertEqual(call["params"]["filter"], "withbody")
        self.assertEqual(call["params"]["key"], "se-key")
        self.assertEqual(result.questions, [{"question_id": 1, "title": "How to use Supabase REST?"}])
        self.assertEqual(result.backoff_seconds, 12)
        self.assertEqual(result.quota_remaining, 9999)

    def test_search_unanswered_raises_clear_error_for_api_error_wrapper(self):
        session = FakeSession(
            FakeResponse(
                {
                    "error_id": 502,
                    "error_name": "throttle_violation",
                    "error_message": "too many requests",
                }
            )
        )
        client = StackExchangeClient(session=session)

        with self.assertRaisesRegex(RuntimeError, "throttle_violation: too many requests"):
            client.search_unanswered()


if __name__ == "__main__":
    unittest.main()
