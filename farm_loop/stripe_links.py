"""Auto-create Stripe Payment Links for paid offers.

Top revenue item: turn the catalog of offers into real checkout links with
zero manual work. For each paid offer this creates a Stripe Product, a Price,
and a Payment Link whose metadata carries `offer_key` so the already-deployed
conversion webhook (/webhooks/conversion/stripe) attributes the sale.

Safe by design: no-op when STRIPE_SECRET_KEY is missing or a placeholder, never
logs the key, and a single offer failure never aborts the batch.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
from typing import Callable

Opener = Callable[[urllib.request.Request, float], object]

STRIPE_API = "https://api.stripe.com/v1"

# Offer types that are paid through Stripe. Support/sponsorship go through
# Buy Me a Coffee / GitHub Sponsors instead, so we skip them here.
STRIPE_OFFER_TYPES = {"setup_service", "fixed_scope_service", "digital_product", "paid_report"}


def _looks_real(key: str | None) -> bool:
    if not key:
        return False
    key = key.strip()
    if not key.startswith("sk_"):
        return False
    lowered = key.lower()
    return not any(t in lowered for t in ("your-", "your_", "xxxx", "<", "placeholder", "here"))


class StripeLinkBuilder:
    def __init__(
        self,
        secret_key: str | None,
        *,
        currency: str = "usd",
        opener: Opener | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.secret_key = (secret_key or "").strip()
        self.currency = currency
        self._opener = opener or (lambda req, timeout: urllib.request.urlopen(req, timeout=timeout))
        self._timeout = timeout

    @property
    def enabled(self) -> bool:
        return _looks_real(self.secret_key)

    def _post(self, path: str, fields: list[tuple[str, str]]) -> dict:
        data = urllib.parse.urlencode(fields).encode("utf-8")
        request = urllib.request.Request(
            f"{STRIPE_API}/{path}",
            data=data,
            headers={
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "infinite-revenue-engine",
            },
            method="POST",
        )
        import json

        with self._opener(request, self._timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def create_for_offers(self, offers: list) -> dict[str, str]:
        """Return {offer_key: payment_link_url} for the offers we could create."""
        if not self.enabled:
            return {}
        links: dict[str, str] = {}
        for offer in offers:
            offer_type = getattr(offer, "offer_type", "")
            price = float(getattr(offer, "price_usd", 0) or 0)
            offer_key = getattr(offer, "offer_key", "") or ""
            if offer_type not in STRIPE_OFFER_TYPES or price <= 0 or not offer_key:
                continue
            try:
                links[offer_key] = self._create_one(offer, price, offer_key)
            except Exception:
                # One offer failing must not abort the rest.
                continue
        return links

    def _create_one(self, offer, price: float, offer_key: str) -> str:
        title = (getattr(offer, "title", "") or offer_key)[:250]
        metadata = {
            "offer_key": offer_key,
            "source": getattr(offer, "channel", "") or "",
            "ire_source": getattr(offer, "source", "") or "",
            "ire_external_id": getattr(offer, "external_id", "") or "",
            "offer_type": getattr(offer, "offer_type", "") or "",
        }
        product = self._post(
            "products",
            [("name", title)] + [(f"metadata[{k}]", v) for k, v in metadata.items()],
        )
        price_obj = self._post(
            "prices",
            [
                ("product", str(product.get("id", ""))),
                ("unit_amount", str(int(round(price * 100)))),
                ("currency", self.currency),
            ],
        )
        link = self._post(
            "payment_links",
            [
                ("line_items[0][price]", str(price_obj.get("id", ""))),
                ("line_items[0][quantity]", "1"),
            ]
            + [(f"metadata[{k}]", v) for k, v in metadata.items()],
        )
        return str(link.get("url", ""))


def build_offer_payment_urls_string(mapping: dict[str, str]) -> str:
    """Serialize {offer_key: url} into the OFFER_PAYMENT_URLS format the offer
    resolver understands: `offer_type=url,offer_type=url`. The offer_key is
    `keywords:slug:offer_type`, so the trailing segment is the offer_type."""
    parts: list[str] = []
    for offer_key, url in mapping.items():
        offer_type = offer_key.rsplit(":", 1)[-1] if ":" in offer_key else offer_key
        parts.append(f"{offer_type}={url}")
    return ",".join(parts)
