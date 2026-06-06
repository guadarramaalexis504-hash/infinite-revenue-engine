import unittest

from farm_loop.scoring import rank_questions, score_question, to_opportunity_payload


class ScoringTests(unittest.TestCase):
    def test_scores_clear_recent_unanswered_question_higher_than_weak_question(self):
        strong = {
            "question_id": 101,
            "title": "FastAPI Supabase insert returns 401 with service key in GitHub Actions",
            "body": "<p>I get a 401 when posting to Supabase REST from GitHub Actions.</p><pre><code>requests.post(url)</code></pre>",
            "tags": ["python", "fastapi", "supabase"],
            "answer_count": 0,
            "is_answered": False,
            "view_count": 180,
            "score": 2,
            "creation_date": 1780680000,
            "link": "https://stackoverflow.com/questions/101/example",
        }
        weak = {
            "question_id": 102,
            "title": "help",
            "body": "it broke",
            "tags": ["misc"],
            "answer_count": 2,
            "is_answered": True,
            "view_count": 5,
            "score": -2,
            "creation_date": 1600000000,
            "link": "https://stackoverflow.com/questions/102/example",
        }

        self.assertGreater(score_question(strong), score_question(weak))
        self.assertGreaterEqual(score_question(strong), 60)
        self.assertLess(score_question(weak), 50)

    def test_rank_questions_deduplicates_by_question_id_and_limits_results(self):
        first = {
            "question_id": 201,
            "title": "Python requests timeout in GitHub Actions calling Supabase REST",
            "body": "<p>How can I handle timeout retries?</p><pre><code>requests.get(url, timeout=10)</code></pre>",
            "tags": ["python", "supabase"],
            "answer_count": 0,
            "is_answered": False,
            "view_count": 100,
            "score": 1,
            "creation_date": 1780680000,
            "link": "https://stackoverflow.com/questions/201/example",
        }
        duplicate = dict(first)
        duplicate["title"] = "Duplicate title should not matter"
        second = {
            "question_id": 202,
            "title": "OpenAI Responses JSON schema parsing in Python",
            "body": "<p>Need structured output parsing.</p>",
            "tags": ["python", "openai-api"],
            "answer_count": 0,
            "is_answered": False,
            "view_count": 80,
            "score": 0,
            "creation_date": 1780680000,
            "link": "https://stackoverflow.com/questions/202/example",
        }

        ranked = rank_questions([first, duplicate, second], max_items=2, min_score=40)

        self.assertEqual([item["question_id"] for item in ranked], [201, 202])

    def test_opportunity_payload_uses_expected_supabase_shape(self):
        question = {
            "question_id": 301,
            "title": "Supabase REST insert from Python",
            "link": "https://stackoverflow.com/questions/301/example",
            "tags": ["python", "supabase"],
        }

        payload = to_opportunity_payload(question, score=74)

        self.assertEqual(
            payload,
            {
                "source": "stackexchange",
                "external_id": "301",
                "title": "Supabase REST insert from Python",
                "url": "https://stackoverflow.com/questions/301/example",
                "tags": ["python", "supabase"],
                "score": 74,
                "status": "new",
            },
        )


if __name__ == "__main__":
    unittest.main()
