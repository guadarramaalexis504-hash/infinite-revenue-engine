import io
import json
import unittest

from farm_loop.config import Settings
from farm_loop.http_app import create_tracking_app


class FakeSupabase:
    def __init__(self):
        self.clicks = []
        self.tips = []
        self.conversions = []
        self.events = []

    def insert_click_event(self, payload):
        self.clicks.append(payload)
        return [{"id": "click-1"}]

    def insert_tip_event(self, payload):
        self.tips.append(payload)
        return [{"id": "tip-1"}]

    def insert_conversion_event(self, payload):
        self.conversions.append(payload)
        return [{"id": "conversion-1"}]

    def insert_event(self, run_id, event_type, payload):
        self.events.append((run_id, event_type, payload))


def call_app(app, *, method="GET", path="/", query="", body=None, headers=None, content_type="application/json"):
    if isinstance(body, bytes):
        body_bytes = body
    else:
        body_bytes = b"" if body is None else json.dumps(body).encode("utf-8")
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "wsgi.input": io.BytesIO(body_bytes),
        "CONTENT_LENGTH": str(len(body_bytes)),
        "CONTENT_TYPE": content_type,
    }
    for key, value in (headers or {}).items():
        environ[f"HTTP_{key.upper().replace('-', '_')}"] = value

    captured = {}

    def start_response(status, response_headers):
        captured["status"] = status
        captured["headers"] = dict(response_headers)

    response = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], response


class TrackingHttpAppTests(unittest.TestCase):
    def make_app(self, supabase):
        settings = Settings(
            supabase_url=None,
            supabase_key=None,
            openai_api_key=None,
            stackexchange_key=None,
            tip_url="https://buymeacoffee.com/example",
            buymeacoffee_webhook_token="bmac-token",
            conversion_webhook_token="conversion-token",
        )
        return create_tracking_app(
            settings=settings,
            supabase=supabase,
            allowed_target_hosts={"buymeacoffee.com"},
        )

    def test_health_returns_json_ok(self):
        status, headers, body = call_app(self.make_app(FakeSupabase()), path="/health")

        self.assertEqual(status, "200 OK")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_click_endpoint_records_click_and_redirects_to_safe_target(self):
        supabase = FakeSupabase()
        app = self.make_app(supabase)
        query = (
            "target=https%3A%2F%2Fbuymeacoffee.com%2Fexample"
            "&opportunity_source=idea_catalog"
            "&opportunity_external_id=microtool-supabase-rls"
            "&channel=microtool_seo"
            "&content=support_cta"
        )

        status, headers, body = call_app(app, path="/click", query=query)

        self.assertEqual(status, "302 Found")
        self.assertEqual(headers["Location"], "https://buymeacoffee.com/example")
        self.assertEqual(body, b"")
        self.assertEqual(supabase.clicks[0]["payload"]["opportunity_external_id"], "microtool-supabase-rls")
        self.assertEqual(supabase.events[-1][1], "click_recorded")

    def test_buymeacoffee_webhook_records_tip_event(self):
        supabase = FakeSupabase()
        payload = {"data": {"id": "support-123", "amount": "5.00", "currency": "USD"}}

        status, _headers, body = call_app(
            self.make_app(supabase),
            method="POST",
            path="/webhooks/buymeacoffee",
            body=payload,
            headers={"X-BuyMeACoffee-Token": "bmac-token"},
        )

        self.assertEqual(status, "200 OK")
        self.assertEqual(json.loads(body)["status"], "recorded")
        self.assertEqual(supabase.tips[0]["external_id"], "support-123")
        self.assertEqual(supabase.tips[0]["amount_usd"], 5.0)

    def test_conversion_webhook_records_confirmed_revenue(self):
        supabase = FakeSupabase()
        payload = {
            "id": "evt_123",
            "data": {
                "object": {
                    "amount_total": 9900,
                    "currency": "usd",
                    "metadata": {"offer_id": "offer-1", "source": "paid_setup_kit"},
                }
            },
        }

        status, _headers, body = call_app(
            self.make_app(supabase),
            method="POST",
            path="/webhooks/conversion/stripe",
            body=payload,
            headers={"X-Revenue-Webhook-Token": "conversion-token"},
        )

        self.assertEqual(status, "200 OK")
        self.assertEqual(json.loads(body)["status"], "recorded")
        self.assertEqual(supabase.conversions[0]["external_id"], "stripe:evt_123")
        self.assertEqual(supabase.conversions[0]["amount_usd"], 99.0)

    def test_conversion_webhook_accepts_form_encoded_gumroad_ping(self):
        supabase = FakeSupabase()
        body = (
            b"sale_id=sale-123&price=19.00&currency=USD"
            b"&source=niche_report"
            b"&offer_key=idea_catalog%3Areport%3Apaid_report"
            b"&product_permalink=report-pack"
        )

        status, _headers, response = call_app(
            self.make_app(supabase),
            method="POST",
            path="/webhooks/conversion/gumroad",
            body=body,
            headers={"X-Revenue-Webhook-Token": "conversion-token"},
            content_type="application/x-www-form-urlencoded",
        )

        self.assertEqual(status, "200 OK")
        self.assertEqual(json.loads(response)["status"], "recorded")
        self.assertEqual(supabase.conversions[0]["external_id"], "gumroad:sale-123")
        self.assertEqual(supabase.conversions[0]["amount_usd"], 19.0)
        self.assertEqual(supabase.conversions[0]["payload"]["offer_key"], "idea_catalog:report:paid_report")

    def test_conversion_webhook_accepts_token_query_for_providers_without_custom_headers(self):
        supabase = FakeSupabase()
        body = b"sale_id=sale-123&price=19.00&currency=USD&source=niche_report"

        status, _headers, response = call_app(
            self.make_app(supabase),
            method="POST",
            path="/webhooks/conversion/gumroad",
            query="token=conversion-token",
            body=body,
            content_type="application/x-www-form-urlencoded",
        )

        self.assertEqual(status, "200 OK")
        self.assertEqual(json.loads(response)["status"], "recorded")
        self.assertEqual(supabase.conversions[0]["external_id"], "gumroad:sale-123")

    def test_click_endpoint_rejects_disallowed_target_host(self):
        status, _headers, body = call_app(
            self.make_app(FakeSupabase()),
            path="/click",
            query=(
                "target=https%3A%2F%2Fevil.example%2Fpay"
                "&opportunity_source=idea_catalog"
                "&opportunity_external_id=microtool-supabase-rls"
                "&channel=microtool_seo"
            ),
        )

        self.assertEqual(status, "403 Forbidden")
        self.assertIn("not allowed", json.loads(body)["error"])


if __name__ == "__main__":
    unittest.main()
