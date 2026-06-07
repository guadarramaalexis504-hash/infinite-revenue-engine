from __future__ import annotations

import re
from typing import Any


def parse_confirmed_conversion_event(payload: dict[str, Any], *, provider: str) -> dict[str, Any]:
    provider_name = _clean(provider, default="manual")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    obj = _provider_object(payload, data, provider_name)
    metadata = _metadata(payload, obj)

    _validate_confirmed(payload, obj, provider_name)
    provider_external_id = _first_string(
        payload.get("id"),
        data.get("id"),
        obj.get("id"),
        obj.get("identifier"),
        payload.get("external_id"),
        payload.get("sale_id"),
        payload.get("purchase_id"),
        payload.get("order_id"),
    )
    if not provider_external_id:
        raise ValueError("external_id is required for conversion payload")

    currency = _first_string(obj.get("currency"), payload.get("currency"), "USD").upper()
    if currency != "USD" and _first_value(obj.get("total_usd"), payload.get("total_usd")) is None:
        raise ValueError(f"Unsupported conversion currency for amount_usd: {currency}")

    amount_usd = _amount_usd(payload, obj)
    source = _first_string(metadata.get("source"), metadata.get("channel"), payload.get("source"), provider_name)
    offer_id = _first_string(metadata.get("offer_id"), obj.get("offer_id"), payload.get("offer_id")) or None
    offer_key = _first_string(
        metadata.get("offer_key"),
        metadata.get("ire_offer_key"),
        obj.get("offer_key"),
        payload.get("offer_key"),
        payload.get("ire_offer_key"),
    )

    conversion_payload = {
        "offer_id": offer_id,
        "source": source,
        "external_id": _provider_external_id(provider_name, provider_external_id),
        "amount_usd": amount_usd,
        "payload": {
            "provider": provider_name,
            "provider_external_id": provider_external_id,
            "raw": payload,
        },
    }
    if offer_key:
        conversion_payload["payload"]["offer_key"] = offer_key
    event_name = _first_string(_meta(payload).get("event_name"), payload.get("event_name"), payload.get("type"))
    if event_name:
        conversion_payload["payload"]["provider_event_name"] = event_name
    product_permalink = _first_string(payload.get("product_permalink"), obj.get("product_permalink"))
    if product_permalink:
        conversion_payload["payload"]["product_permalink"] = product_permalink
    return conversion_payload


def build_manual_conversion_payload(
    *,
    provider: str,
    external_id: str,
    amount_usd: float,
    source: str,
    offer_id: str | None = None,
    offer_key: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provider_name = _clean(provider, default="manual")
    provider_external_id = str(external_id).strip()
    if not provider_external_id:
        raise ValueError("external_id is required for conversion payload")
    amount = float(amount_usd)
    if amount < 0:
        raise ValueError("amount_usd must be greater than or equal to 0")
    raw_payload = payload or {}
    conversion_payload = {
        "offer_id": offer_id or None,
        "source": _clean(source, default=provider_name),
        "external_id": _provider_external_id(provider_name, provider_external_id),
        "amount_usd": amount,
        "payload": {
            "provider": provider_name,
            "provider_external_id": provider_external_id,
            "raw": raw_payload,
        },
    }
    clean_offer_key = str(offer_key or "").strip()
    if clean_offer_key:
        conversion_payload["payload"]["offer_key"] = clean_offer_key
    return conversion_payload


def _amount_usd(payload: dict[str, Any], obj: dict[str, Any]) -> float:
    direct = _first_value(payload.get("amount_usd"), obj.get("amount_usd"))
    if direct is not None:
        return float(direct)
    cents = _first_value(
        obj.get("total_usd"),
        payload.get("total_usd"),
        obj.get("amount_total"),
        obj.get("amount_paid"),
        obj.get("amount_cents"),
        payload.get("amount_total"),
        payload.get("amount_cents"),
    )
    if cents is None:
        money = _first_value(payload.get("price"), payload.get("sale_price"), payload.get("amount"), obj.get("price"))
        if money is not None:
            return _money_to_float(money)
        raise ValueError("amount_usd is required for conversion payload")
    return round(float(cents) / 100.0, 2)


def _provider_object(payload: dict[str, Any], data: dict[str, Any], provider: str) -> dict[str, Any]:
    if provider == "lemon_squeezy" and isinstance(data.get("attributes"), dict):
        return data["attributes"]
    if isinstance(data.get("object"), dict):
        return data["object"]
    return data if data else payload


def _metadata(payload: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for candidate in [
        obj.get("metadata"),
        payload.get("metadata"),
        _meta(payload).get("custom_data"),
        payload,
    ]:
        if isinstance(candidate, dict):
            merged.update(candidate)
    return merged


def _meta(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("meta")
    return value if isinstance(value, dict) else {}


def _validate_confirmed(payload: dict[str, Any], obj: dict[str, Any], provider: str) -> None:
    if provider == "lemon_squeezy":
        status = _clean(obj.get("status"), default="")
        if status != "paid":
            raise ValueError(f"{provider} payload is not a confirmed paid conversion")
    if provider == "gumroad":
        refunded = str(payload.get("refunded") or payload.get("chargebacked") or "").strip().lower()
        if refunded in {"1", "true", "yes"}:
            raise ValueError(f"{provider} payload is not a confirmed paid conversion")


def _money_to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    text = str(value).strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if not match:
        raise ValueError("amount_usd is required for conversion payload")
    return round(float(match.group(0)), 2)


def _provider_external_id(provider: str, external_id: str) -> str:
    external_id = str(external_id).strip()
    if external_id.startswith(f"{provider}:"):
        return external_id
    return f"{provider}:{external_id}"


def _clean(value: Any, *, default: str) -> str:
    text = str(value or "").strip().lower()
    return text or default


def _first_string(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _first_value(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None
