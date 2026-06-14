import unittest

from farm_loop.discord_notify import (
    DiscordNotifier,
    build_conversion_message,
    build_daily_summary_message,
    build_error_message,
    build_ideas_message,
    build_site_build_message,
)


class SiteBuildMessageTests(unittest.TestCase):
    def test_includes_total_clusters_and_url(self):
        msg = build_site_build_message(
            clusters=[("emoji", 116), ("color", 148), ("country", 216)],
            total_pages=480,
            site_url="https://revenue.example",
        )
        self.assertIn("480", msg)
        self.assertIn("3 clusters", msg)
        self.assertIn("country", msg)
        self.assertIn("https://revenue.example", msg)
        # Highest-count cluster should be listed first.
        self.assertLess(msg.index("country"), msg.index("emoji"))


class FakeResponse:
    def __init__(self, status: int = 204) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b""


class DiscordNotifierTests(unittest.TestCase):
    def test_disabled_when_no_webhook_url(self):
        sent = []
        notifier = DiscordNotifier(webhook_url=None, opener=lambda req, timeout: sent.append(req))
        result = notifier.send("hello", username="Bot")
        self.assertFalse(result)
        self.assertEqual(sent, [])

    def test_disabled_for_placeholder_url(self):
        sent = []
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/your-webhook-here",
            opener=lambda req, timeout: sent.append(req),
        )
        self.assertFalse(notifier.send("hi"))
        self.assertEqual(sent, [])

    def test_posts_json_payload_to_webhook(self):
        captured = {}

        def opener(req, timeout):
            captured["url"] = req.full_url
            captured["data"] = req.data
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            return FakeResponse(204)

        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/123/abc",
            opener=opener,
        )
        ok = notifier.send("Revenue update", username="Revenue Engine")
        self.assertTrue(ok)
        self.assertEqual(captured["url"], "https://discord.com/api/webhooks/123/abc")
        self.assertIn("application/json", captured["headers"]["content-type"])
        import json

        body = json.loads(captured["data"].decode("utf-8"))
        self.assertEqual(body["content"], "Revenue update")
        self.assertEqual(body["username"], "Revenue Engine")

    def test_send_truncates_content_over_2000_chars(self):
        captured = {}

        def opener(req, timeout):
            captured["data"] = req.data
            return FakeResponse(204)

        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/1/x", opener=opener)
        notifier.send("x" * 5000)
        import json

        body = json.loads(captured["data"].decode("utf-8"))
        self.assertLessEqual(len(body["content"]), 2000)

    def test_send_returns_false_on_opener_error(self):
        def opener(req, timeout):
            raise OSError("network down")

        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/1/x", opener=opener)
        self.assertFalse(notifier.send("hi"))

    def test_daily_summary_message_includes_key_metrics(self):
        msg = build_daily_summary_message(
            {
                "opportunities": 10,
                "assets": 246,
                "offers": 76,
                "clicks": 5,
                "conversions": 1,
                "revenue_usd": 49.0,
                "site_url": "https://example.com",
            }
        )
        self.assertIn("246", msg)
        self.assertIn("$49", msg)
        self.assertIn("https://example.com", msg)

    def test_conversion_message_masks_nothing_sensitive_and_shows_amount(self):
        msg = build_conversion_message(amount_usd=49.0, source="microtool_seo", offer_key="setup:rls")
        self.assertIn("$49", msg)
        self.assertIn("microtool_seo", msg)
        self.assertIn("setup:rls", msg)

    def test_error_message_includes_phase_and_detail(self):
        msg = build_error_message(phase="generate", detail="Supabase 400 on offers")
        self.assertIn("generate", msg)
        self.assertIn("Supabase 400", msg)

    def test_ideas_message_lists_titles(self):
        msg = build_ideas_message(["Idea A", "Idea B", "Idea C"], total=184)
        self.assertIn("Idea A", msg)
        self.assertIn("184", msg)


if __name__ == "__main__":
    unittest.main()
