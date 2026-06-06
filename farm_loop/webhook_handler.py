from __future__ import annotations

from typing import Any

from .webhooks import parse_buymeacoffee_event, verify_webhook_token


def handle_buymeacoffee_webhook(
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    expected_token: str,
    supabase: Any,
) -> dict[str, Any]:
    if not verify_webhook_token(headers, expected_token):
        raise PermissionError("Invalid Buy Me a Coffee webhook token")

    tip_payload = parse_buymeacoffee_event(payload)
    rows = supabase.insert_tip_event(tip_payload)
    if hasattr(supabase, "insert_event"):
        supabase.insert_event(
            None,
            "tip_recorded",
            {
                "provider": tip_payload["provider"],
                "external_id": tip_payload["external_id"],
                "amount_usd": tip_payload["amount_usd"],
            },
        )
    return {"status": "recorded", "tip_event": rows}
