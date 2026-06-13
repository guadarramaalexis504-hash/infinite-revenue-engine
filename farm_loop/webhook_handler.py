from __future__ import annotations

from typing import Any

from .conversions import parse_confirmed_conversion_event
from .webhooks import parse_buymeacoffee_event, verify_stripe_signature, verify_webhook_token


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


def handle_conversion_webhook(
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    expected_token: str,
    provider: str,
    supabase: Any,
    raw_body: str = "",
    stripe_webhook_secret: str | None = None,
    now: int | None = None,
) -> dict[str, Any]:
    normalized = {key.lower(): value for key, value in headers.items()}
    # Real Stripe events are authenticated by HMAC signature, not a shared
    # token. When a Stripe endpoint secret is configured, require it.
    if provider == "stripe" and stripe_webhook_secret:
        signature = normalized.get("stripe-signature", "")
        if not verify_stripe_signature(raw_body, signature, stripe_webhook_secret, now=now):
            raise PermissionError("Invalid Stripe webhook signature")
    elif not verify_webhook_token(headers, expected_token):
        raise PermissionError("Invalid conversion webhook token")

    conversion_payload = parse_confirmed_conversion_event(payload, provider=provider)
    rows = supabase.insert_conversion_event(conversion_payload)
    if hasattr(supabase, "insert_event"):
        supabase.insert_event(
            None,
            "conversion_recorded",
            {
                "source": conversion_payload["source"],
                "external_id": conversion_payload["external_id"],
                "amount_usd": conversion_payload["amount_usd"],
            },
        )
    return {"status": "recorded", "conversion_event": rows}
