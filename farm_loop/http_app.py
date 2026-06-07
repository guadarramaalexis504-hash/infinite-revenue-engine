from __future__ import annotations

import argparse
import json
from json import JSONDecodeError
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit
from wsgiref.simple_server import make_server

from .click_handler import handle_click_redirect
from .config import Settings
from .supabase_client import SupabaseClient
from .webhook_handler import handle_buymeacoffee_webhook, handle_conversion_webhook


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WsgiApp = Callable[[dict[str, Any], StartResponse], list[bytes]]


def create_tracking_app(
    *,
    settings: Settings | None = None,
    supabase: Any | None = None,
    allowed_target_hosts: set[str] | None = None,
) -> WsgiApp:
    settings = settings or Settings.from_env()
    supabase = supabase or SupabaseClient(settings.supabase_url or "", settings.supabase_key or "")
    allowed_hosts = allowed_target_hosts if allowed_target_hosts is not None else _allowed_hosts(settings)

    def app(environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
        method = str(environ.get("REQUEST_METHOD") or "GET").upper()
        path = str(environ.get("PATH_INFO") or "/")

        try:
            if path == "/health":
                return _json_response(start_response, "200 OK", {"status": "ok"})

            if path == "/click":
                if method != "GET":
                    return _json_response(start_response, "405 Method Not Allowed", {"error": "Method not allowed"})
                result = handle_click_redirect(
                    query=_query(environ),
                    supabase=supabase,
                    allowed_target_hosts=allowed_hosts,
                )
                start_response("302 Found", [("Location", result["location"]), ("Content-Length", "0")])
                return [b""]

            if path == "/webhooks/buymeacoffee":
                if method != "POST":
                    return _json_response(start_response, "405 Method Not Allowed", {"error": "Method not allowed"})
                result = handle_buymeacoffee_webhook(
                    headers=_headers(environ),
                    payload=_json_body(environ),
                    expected_token=settings.buymeacoffee_webhook_token or "",
                    supabase=supabase,
                )
                return _json_response(start_response, "200 OK", result)

            if path.startswith("/webhooks/conversion/"):
                if method != "POST":
                    return _json_response(start_response, "405 Method Not Allowed", {"error": "Method not allowed"})
                provider = path.removeprefix("/webhooks/conversion/").strip("/")
                if not provider:
                    return _json_response(start_response, "404 Not Found", {"error": "Missing conversion provider"})
                headers = _headers(environ)
                query = _query(environ)
                if "X-Revenue-Webhook-Token" not in headers and query.get("token"):
                    headers["X-Revenue-Webhook-Token"] = query["token"]
                result = handle_conversion_webhook(
                    headers=headers,
                    payload=_json_body(environ),
                    expected_token=settings.conversion_webhook_token or "",
                    provider=provider,
                    supabase=supabase,
                )
                return _json_response(start_response, "200 OK", result)

            return _json_response(start_response, "404 Not Found", {"error": "Not found"})
        except PermissionError as exc:
            return _json_response(start_response, "403 Forbidden", {"error": str(exc)})
        except (ValueError, JSONDecodeError) as exc:
            return _json_response(start_response, "400 Bad Request", {"error": str(exc)})

    return app


def _query(environ: dict[str, Any]) -> dict[str, str]:
    parsed = parse_qs(str(environ.get("QUERY_STRING") or ""), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def _headers(environ: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            header = key.removeprefix("HTTP_").replace("_", "-")
            headers[header] = str(value)
    if "CONTENT_TYPE" in environ:
        headers["Content-Type"] = str(environ["CONTENT_TYPE"])
    return headers


def _json_body(environ: dict[str, Any]) -> dict[str, Any]:
    length = int(environ.get("CONTENT_LENGTH") or "0")
    raw = environ["wsgi.input"].read(length)
    content_type = str(environ.get("CONTENT_TYPE") or "").split(";", 1)[0].strip().lower()
    body = raw.decode("utf-8") if raw else ""
    if content_type == "application/x-www-form-urlencoded":
        parsed = parse_qs(body, keep_blank_values=True)
        return {key: values[-1] if values else "" for key, values in parsed.items()}
    payload = json.loads(body if body else "{}")
    if not isinstance(payload, dict):
        raise ValueError("JSON request body must be an object")
    return payload


def _json_response(start_response: StartResponse, status: str, payload: dict[str, Any]) -> list[bytes]:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _allowed_hosts(settings: Settings) -> set[str]:
    hosts = {host.strip().lower() for host in settings.click_allowed_hosts.split(",") if host.strip()}
    for url in [settings.tip_url, settings.service_intake_url]:
        if url:
            host = urlsplit(url).netloc.lower()
            if host:
                hosts.add(host)
    return hosts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Infinite Revenue tracking HTTP app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)

    app = create_tracking_app()
    with make_server(args.host, args.port, app) as server:
        print(f"tracking HTTP app listening on http://{args.host}:{args.port}")
        server.serve_forever()
    return 0


application = create_tracking_app()


if __name__ == "__main__":
    raise SystemExit(main())
