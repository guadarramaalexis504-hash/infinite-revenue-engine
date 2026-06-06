import json
import unittest

from farm_loop.drafts import DraftGenerator


class FakeResponse:
    status_code = 200
    text = "ok"

    def json(self):
        return {
            "output_text": json.dumps(
                {
                    "answer_markdown": "Use a service-role key only server-side.",
                    "code_snippet": "requests.post(url, headers=headers)",
                }
            )
        }


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return FakeResponse()


class DraftGeneratorTests(unittest.TestCase):
    def test_generate_posts_responses_request_and_parses_structured_text(self):
        session = FakeSession()
        generator = DraftGenerator("openai-key", model="test-model", session=session)
        question = {
            "title": "Supabase REST 401 in GitHub Actions",
            "body": "<p>Why is this failing?</p>",
            "tags": ["python", "supabase"],
            "link": "https://stackoverflow.com/questions/1/example",
        }

        draft = generator.generate(question, tip_url="https://buymeacoffee.com/example")

        call = session.calls[0]
        self.assertEqual(call["url"], "https://api.openai.com/v1/responses")
        self.assertEqual(call["headers"]["Authorization"], "Bearer openai-key")
        self.assertEqual(call["json"]["model"], "test-model")
        self.assertIn("Return only JSON", call["json"]["instructions"])
        self.assertIn("https://buymeacoffee.com/example", call["json"]["input"])
        self.assertEqual(draft.answer_markdown, "Use a service-role key only server-side.")
        self.assertEqual(draft.code_snippet, "requests.post(url, headers=headers)")


if __name__ == "__main__":
    unittest.main()
