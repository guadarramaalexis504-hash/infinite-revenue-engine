from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .revenue_scoring import RevenueOpportunity


@dataclass(frozen=True)
class OfferDraft:
    source: str
    external_id: str
    channel: str
    offer_type: str
    offer_key: str
    title: str
    description: str
    price_usd: float
    cta_label: str
    status: str = "draft"
    payment_url: str = ""

    def to_payload(self, opportunity_id: str | None = None) -> dict:
        return {
            "opportunity_id": opportunity_id,
            "channel": self.channel,
            "title": self.title,
            "price_usd": self.price_usd,
            "payment_url": self.payment_url,
            "status": self.status,
            "payload": {
                "source": self.source,
                "external_id": self.external_id,
                "offer_type": self.offer_type,
                "offer_key": self.offer_key,
                "description": self.description,
                "cta_label": self.cta_label,
            },
        }


def parse_offer_payment_urls(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    payment_urls: dict[str, str] = {}
    for raw_item in value.replace("\n", ",").split(","):
        item = raw_item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError("Offer payment URLs must use key=url pairs")
        key, url = item.split("=", 1)
        key = key.strip()
        url = url.strip()
        if not key or not url:
            raise ValueError("Offer payment URL keys and values must be non-empty")
        payment_urls[key] = url
    return payment_urls


def resolve_offer_payment_url(offer_type: str, channel: str, payment_urls: dict[str, str] | None) -> str:
    if not payment_urls:
        return ""
    return payment_urls.get(offer_type) or payment_urls.get(channel) or payment_urls.get("*", "")


def build_offer_key(opportunity: RevenueOpportunity, offer_type: str) -> str:
    return f"{opportunity.source}:{opportunity.external_id}:{offer_type}"


def generate_offers(
    opportunity: RevenueOpportunity,
    *,
    payment_urls: dict[str, str] | None = None,
) -> list[OfferDraft]:
    channel = opportunity.channel
    if channel == "microtool_seo":
        return [
            _offer(
                opportunity,
                offer_type="support",
                title=f"Support {opportunity.title}",
                description="Optional support for this useful tool on an owned channel. No third-party spam or automated posting.",
                price_usd=5,
                cta_label="Support this tool",
                payment_url=resolve_offer_payment_url("support", channel, payment_urls),
            ),
            _offer(
                opportunity,
                offer_type="setup_service",
                title=f"{opportunity.title} setup help",
                description="Fixed-scope help applying this tool's findings to a real project after manual review.",
                price_usd=49,
                cta_label="Get setup help",
                payment_url=resolve_offer_payment_url("setup_service", channel, payment_urls),
            ),
        ]
    if channel == "paid_setup_kit":
        return [
            _offer(
                opportunity,
                offer_type="fixed_scope_service",
                title=opportunity.title,
                description="Done-for-you fixed-scope setup with clear deliverables, intake, and manual acceptance.",
                price_usd=max(199, min(299, round(opportunity.payout_estimate_usd))),
                cta_label="Book fixed setup",
                payment_url=resolve_offer_payment_url("fixed_scope_service", channel, payment_urls),
            )
        ]
    if channel == "digital_product":
        return [
            _offer(
                opportunity,
                offer_type="digital_product",
                title=opportunity.title,
                description="Downloadable template or starter kit sold from an owned store after manual review.",
                price_usd=29,
                cta_label="Get the template",
                payment_url=resolve_offer_payment_url("digital_product", channel, payment_urls),
            )
        ]
    if channel == "github_issue_helper":
        return [
            _offer(
                opportunity,
                offer_type="sponsorship",
                title=f"Sponsor {opportunity.title}",
                description="Owned sponsorship CTA for useful open-source help. Do not add payment links to third-party issues.",
                price_usd=5,
                cta_label="Sponsor this work",
                payment_url=resolve_offer_payment_url("sponsorship", channel, payment_urls),
            )
        ]
    return [
        _offer(
            opportunity,
            offer_type="support",
            title=f"Support {opportunity.title}",
            description="Optional support CTA for an owned or explicitly permitted channel.",
            price_usd=5,
            cta_label="Support this work",
            payment_url=resolve_offer_payment_url("support", channel, payment_urls),
        )
    ]


class OfferCatalogExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(self, offers: list[OfferDraft]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / "offers.json"
        markdown_path = self.output_dir / "OFFERS.md"
        json_path.write_text(
            json.dumps([asdict(offer) for offer in offers], indent=2, sort_keys=True),
            encoding="utf-8",
        )
        markdown_path.write_text(_to_markdown(offers), encoding="utf-8")
        return [json_path, markdown_path]


def _offer(
    opportunity: RevenueOpportunity,
    *,
    offer_type: str,
    title: str,
    description: str,
    price_usd: float,
    cta_label: str,
    payment_url: str = "",
) -> OfferDraft:
    return OfferDraft(
        source=opportunity.source,
        external_id=opportunity.external_id,
        channel=opportunity.channel,
        offer_type=offer_type,
        offer_key=build_offer_key(opportunity, offer_type),
        title=title,
        description=description,
        price_usd=float(price_usd),
        cta_label=cta_label,
        payment_url=payment_url,
    )


def _to_markdown(offers: list[OfferDraft]) -> str:
    lines = ["# Offer Catalog", ""]
    for offer in offers:
        lines.extend(
            [
                f"## {offer.title}",
                "",
                f"- Type: {offer.offer_type}",
                f"- Offer Key: {offer.offer_key}",
                f"- Channel: {offer.channel}",
                f"- External ID: {offer.external_id}",
                f"- Price: ${offer.price_usd:.2f}",
                f"- Payment URL: {offer.payment_url or 'not configured'}",
                f"- CTA: {offer.cta_label}",
                f"- Status: {offer.status}",
                f"- Description: {offer.description}",
                "",
            ]
        )
    return "\n".join(lines)
