from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlsplit


def handle_click_redirect(
    *,
    query: Mapping[str, str],
    supabase: Any,
    allowed_target_hosts: set[str],
) -> dict[str, Any]:
    target_url = _required(query, "target")
    parts = urlsplit(target_url)
    if parts.scheme != "https":
        raise ValueError("Click redirect target must use https")
    host = parts.netloc.lower()
    if host not in {item.lower() for item in allowed_target_hosts}:
        raise PermissionError(f"Click redirect target host is not allowed: {host}")

    offer_key = query.get("offer_key") or None
    click_payload = {
        "offer_id": None,
        "source": "revenue_site",
        "payload": {
            "opportunity_source": _required(query, "opportunity_source"),
            "opportunity_external_id": _required(query, "opportunity_external_id"),
            "channel": _required(query, "channel"),
            "target_url": target_url,
            "content": query.get("content", "support_cta"),
        },
    }
    if offer_key:
        click_payload["payload"]["offer_key"] = offer_key
    rows = supabase.insert_click_event(click_payload)
    if hasattr(supabase, "insert_event"):
        supabase.insert_event(
            None,
            "click_recorded",
            {
                "source": click_payload["source"],
                "opportunity_external_id": click_payload["payload"]["opportunity_external_id"],
                "channel": click_payload["payload"]["channel"],
                "offer_key": offer_key,
            },
        )
    return {"status": "redirect", "location": target_url, "click_event": rows}


def _required(query: Mapping[str, str], key: str) -> str:
    value = query.get(key)
    if not value:
        raise ValueError(f"Missing required click parameter: {key}")
    return str(value)
