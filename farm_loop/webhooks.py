from __future__ import annotations

from typing import Any


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
