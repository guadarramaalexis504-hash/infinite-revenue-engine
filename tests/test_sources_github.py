import unittest

from farm_loop.sources_github import GitHubIssuesClient


class FakeResponse:
    def __init__(self, items=None, status_code=200, text="ok"):
        self._items = items or [
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
        self.status_code = status_code
        self.text = text

    def json(self):
        return {"items": self._items}


class FakeSession:
    def __init__(self, responses=None):
        self.calls = []
        self.responses = list(responses or [])

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        if self.responses:
            return self.responses.pop(0)
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

    def test_search_bounty_issues_finds_safe_bounty_tasks_and_filters_prs_security_and_duplicates(self):
        bounty_item = {
            "id": 2001,
            "html_url": "https://github.com/acme/docs/issues/9",
            "title": "Paid docs bounty: Supabase quickstart",
            "body": "Reward offered for a docs-only starter guide with acceptance criteria.",
            "repository_url": "https://api.github.com/repos/acme/docs",
            "labels": [{"name": "bounty"}, {"name": "documentation"}],
        }
        security_item = {
            "id": 2002,
            "html_url": "https://github.com/acme/app/issues/10",
            "title": "Find auth bypass",
            "body": "Security testing needed.",
            "repository_url": "https://api.github.com/repos/acme/app",
            "labels": [{"name": "bounty"}, {"name": "security"}],
        }
        pr_item = {
            "id": 2003,
            "html_url": "https://github.com/acme/docs/pull/11",
            "title": "PR",
            "body": "ignore",
            "pull_request": {},
            "repository_url": "https://api.github.com/repos/acme/docs",
            "labels": [{"name": "bounty"}],
        }
        session = FakeSession(
            responses=[
                FakeResponse([bounty_item, security_item, pr_item]),
                FakeResponse([bounty_item]),
            ]
        )
        client = GitHubIssuesClient(token="gh-token", session=session)

        opportunities = client.search_bounty_issues(query_terms=["supabase", "docs"], max_items=10)

        self.assertEqual(len(session.calls), 2)
        self.assertIn("is:issue", session.calls[0]["params"]["q"])
        self.assertIn("bounty", session.calls[0]["params"]["q"])
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].source, "github_bounty")
        self.assertEqual(opportunities[0].external_id, "2001")
        self.assertEqual(opportunities[0].channel, "bounty_scanner")
        self.assertIn("documentation", opportunities[0].tags)
        self.assertGreaterEqual(opportunities[0].payout_estimate_usd, 100)


if __name__ == "__main__":
    unittest.main()
