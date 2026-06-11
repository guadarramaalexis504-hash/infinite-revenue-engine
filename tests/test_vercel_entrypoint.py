import json
import unittest
from io import BytesIO
from pathlib import Path

from farm_loop.http_app import create_tracking_app


class _StubSupabase:
    def insert_click_event(self, payload):
        return [payload]


class VercelEntrypointTests(unittest.TestCase):
    def test_vercel_json_rewrites_every_path_to_the_function(self):
        config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))
        rewrites = config.get("rewrites", [])
        self.assertEqual(rewrites, [{"source": "/(.*)", "destination": "/api/index"}])

    def test_api_index_reexports_a_wsgi_app(self):
        source = Path("api/index.py").read_text(encoding="utf-8")
        # The Vercel Python runtime resolves a module-level `app`.
        self.assertIn("application as app", source)

    def test_wsgi_app_health_route_is_callable_like_vercel_invokes_it(self):
        app = create_tracking_app(
            supabase=_StubSupabase(),
            allowed_target_hosts={"buymeacoffee.com"},
        )
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/health",
            "QUERY_STRING": "",
            "wsgi.input": BytesIO(b""),
        }
        body = b"".join(app(environ, start_response))
        self.assertEqual(captured["status"], "200 OK")
        self.assertEqual(json.loads(body.decode("utf-8")), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
