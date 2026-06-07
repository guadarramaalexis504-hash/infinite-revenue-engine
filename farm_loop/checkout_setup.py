from __future__ import annotations

import json
from pathlib import Path

from .offers import OfferDraft


PROVIDERS = ["stripe", "gumroad", "lemon_squeezy", "manual"]


def build_checkout_setup_rows(
    offers: list[OfferDraft],
    *,
    conversion_webhook_base_url: str = "",
    click_redirect_url: str = "",
) -> list[dict]:
    webhook_base = conversion_webhook_base_url.rstrip("/")
    rows: list[dict] = []
    for offer in offers:
        metadata = {
            "offer_key": offer.offer_key,
            "ire_offer_key": offer.offer_key,
            "source": offer.channel,
            "ire_source": offer.source,
            "ire_external_id": offer.external_id,
            "offer_type": offer.offer_type,
        }
        rows.append(
            {
                "offer_key": offer.offer_key,
                "title": offer.title,
                "channel": offer.channel,
                "offer_type": offer.offer_type,
                "price_usd": offer.price_usd,
                "payment_url": offer.payment_url,
                "checkout_metadata": metadata,
                "provider_webhooks": _provider_webhooks(webhook_base),
                "provider_payload_hints": _provider_payload_hints(),
                "click_redirect_url": click_redirect_url,
                "manual_conversion_command": _manual_conversion_command(offer),
            }
        )
    return rows


class CheckoutSetupExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        conversion_webhook_base_url: str = "",
        click_redirect_url: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.conversion_webhook_base_url = conversion_webhook_base_url
        self.click_redirect_url = click_redirect_url

    def export(self, offers: list[OfferDraft]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        rows = build_checkout_setup_rows(
            offers,
            conversion_webhook_base_url=self.conversion_webhook_base_url,
            click_redirect_url=self.click_redirect_url,
        )
        json_path = self.output_dir / "checkout_setup.json"
        markdown_path = self.output_dir / "CHECKOUT_SETUP.md"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
        markdown_path.write_text(_to_markdown(rows), encoding="utf-8")
        return [json_path, markdown_path]


def _provider_webhooks(webhook_base: str) -> dict[str, str]:
    if not webhook_base:
        return {provider: "" for provider in PROVIDERS}
    return {provider: f"{webhook_base}/{provider}" for provider in PROVIDERS}


def _provider_payload_hints() -> dict[str, str]:
    return {
        "stripe": "Put checkout_metadata keys in Checkout Session metadata.",
        "gumroad": "Gumroad Ping can POST form-encoded sale fields; include offer_key and source as available URL/custom fields, or use the webhook URL with ?token=CONVERSION_WEBHOOK_TOKEN.",
        "lemon_squeezy": "Pass checkout_metadata keys in Lemon Squeezy custom data so webhooks return them under meta.custom_data.",
        "manual": "Use the manual conversion command after invoice, sponsorship, affiliate, or support payment confirmation.",
    }


def _manual_conversion_command(offer: OfferDraft) -> str:
    return (
        "python -m farm_loop.main --record-conversion --dry-run "
        "--conversion-provider manual --conversion-external-id invoice-id "
        f"--conversion-amount-usd {offer.price_usd:.2f} "
        f"--conversion-source {offer.channel} "
        f"--conversion-offer-key {offer.offer_key}"
    )


def _to_markdown(rows: list[dict]) -> str:
    lines = ["# Checkout Setup", ""]
    if not rows:
        lines.append("No offers generated yet.")
        return "\n".join(lines)
    for row in rows:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Offer key: `{row['offer_key']}`",
                f"- Type: `{row['offer_type']}`",
                f"- Channel: `{row['channel']}`",
                f"- Price: `${row['price_usd']:.2f}`",
                f"- Payment URL: {row['payment_url'] or 'not configured'}",
                "",
                "Checkout metadata:",
                "```json",
                json.dumps(row["checkout_metadata"], indent=2, sort_keys=True),
                "```",
                "",
                "Provider webhooks:",
            ]
        )
        for provider, url in row["provider_webhooks"].items():
            lines.append(f"- {provider}: {url or 'configure CONVERSION_WEBHOOK_BASE_URL'}")
        lines.extend(["", "Provider payload notes:"])
        for provider, hint in row["provider_payload_hints"].items():
            lines.append(f"- {provider}: {hint}")
        lines.extend(
            [
                "",
                "Manual conversion fallback:",
                "```powershell",
                row["manual_conversion_command"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)
