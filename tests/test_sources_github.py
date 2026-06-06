import unittest

from farm_loop.sources_github import GitHubIssuesClient


class FakeResponse:
    status_code = 200
    text = "ok"

    def json(self):
        return {
            "items": [
                {
                    "id": 1001,
                    "html_url": "https://github.com/acme/tool/issues/7",
                    "title": "Need Supabase RLS example",
                    "body": "Can someone add a working setup guide?",
                    "repository_url": "https://api.github.com/repos/acme/tool",
                    "labels": [{"name": "help wanted"}, {"name": "documentation"}],
                },
                {
                    "id": 1002,
                    "html_url": "https://github.com/acme/tool/pull/8",
                    "title": "Existing PR",
                    "body": "ignore",
                    "pull_request": {},
                    "repository_url": "https://api.github.com/repos/acme/tool",
                    "labels": [],
                },
            ]
        }


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return FakeResponse()


class GitHubIssuesClientTests(unittest.TestCase):
    def test_search_help_wanted_issues_uses_github_search_and_filters_prs(self):
        session = FakeSession()
        client = GitHubIssuesClient(token="gh-token", session=session)

        opportunities = client.search_help_wanted_issues(
            query_terms=["supabase", "github actions"],
            max_items=10,
        )

        call = session.calls[0]
        self.assertEqual(call["url"], "https://api.github.com/search/issues")
        self.assertIn("is:issue", call["params"]["q"])
        self.assertIn("label:\"help wanted\"", call["params"]["q"])
        self.assertEqual(call["headers"]["Authorization"], "Bearer gh-token")
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].source, "github")
        self.assertEqual(opportunities[0].external_id, "1001")
        self.assertEqual(opportunities[0].channel, "github_issue_helper")


if __name__ == "__main__":
    unittest.main()
