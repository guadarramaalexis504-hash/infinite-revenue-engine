from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any


def verify_stripe_signature(
    raw_body: str | bytes,
    signature_header: str,
    secret: str | None,
    *,
    tolerance: int = 300,
    now: int | None = None,
) -> bool:
    """Verify a Stripe `Stripe-Signature` header (scheme v1, HMAC-SHA256).

    Stripe signs `"{timestamp}.{raw_body}"`. We recompute the HMAC with the
    endpoint secret and constant-time compare against every v1 in the header,
    and reject signatures whose timestamp drifts beyond `tolerance` seconds.
    """
    if not secret or not signature_header:
        return False
    if isinstance(raw_body, bytes):
        raw_body = raw_body.decode("utf-8", errors="replace")

    timestamp: str | None = None
    signatures: list[str] = []
    for part in signature_header.split(","):
        if "=" not in part:
            return False
        key, _, value = part.strip().partition("=")
        if key == "t":
            timestamp = value
        elif key == "v1":
            signatures.append(value)
    if not timestamp or not signatures:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False

    current = int(now if now is not None else time.time())
    if abs(current - ts) > tolerance:
        return False

    expected = hmac.new(secret.encode(), f"{ts}.{raw_body}".encode(), hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, candidate) for candidate in signatures)


TOKEN_HEADERS = {
    "x-buymeacoffee-token",
    "x-bmac-token",
    "x-verification-token",
    "verification-token",
    "x-revenue-webhook-token",
}


def verify_webhook_token(headers: dict[str, str], expected_token: str | None) -> bool:
    if not expected_token:
        return False
    normalized = {key.lower(): value for key, value in headers.items()}
    return any(normalized.get(header) == expected_token for header in TOKEN_HEADERS)


def parse_buymeacoffee_event(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    external_id = (
        data.get("id")
        or data.get("support_id")
        or data.get("transaction_id")
        or payload.get("id")
    )
    if not external_id:
        raise ValueError("Buy Me a Coffee payload does not include an event id")

    amount = (
        data.get("amount_usd")
        or data.get("amount")
        or data.get("support_amount")
        or data.get("coffee_price")
        or 0
    )
    currency = str(data.get("currency") or data.get("support_currency") or "USD").upper()
    if currency != "USD":
        raise ValueError(f"Unsupported Buy Me a Coffee currency for amount_usd: {currency}")

    return {
        "provider": "buymeacoffee",
        "external_id": str(external_id),
        "amount_usd": float(amount),
        "payload": payload,
    }
