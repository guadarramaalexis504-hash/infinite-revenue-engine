from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .asset_exporter import slugify
from .assets import AssetDraft
from .offers import OfferDraft
from .revenue_scoring import RevenueOpportunity


def build_activation_manifest_rows(
    opportunities_with_assets: list[tuple[RevenueOpportunity, list[AssetDraft]]],
    *,
    offers: list[OfferDraft],
    artifact_dirs: dict[str, str | Path],
    activation_report: dict | None = None,
) -> list[dict]:
    blockers = _activation_blockers(activation_report)
    rows: list[dict] = []
    for opportunity, assets in opportunities_with_assets:
        opportunity_offers = [
            offer
            for offer in offers
            if offer.source == opportunity.source and offer.external_id == opportunity.external_id
        ]
        offer_keys = [offer.offer_key for offer in opportunity_offers]
        first_offer_key = offer_keys[0] if offer_keys else f"{opportunity.source}:{opportunity.external_id}:manual"
        first_price = opportunity_offers[0].price_usd if opportunity_offers else 0.0
        rows.append(
            {
                "source": opportunity.source,
                "external_id": opportunity.external_id,
                "slug": slugify(opportunity.external_id),
                "title": opportunity.title,
                "channel": opportunity.channel,
                "expected_value_usd": round(opportunity.expected_value_usd, 2),
                "asset_types": [asset.asset_type for asset in assets],
                "offer_keys": offer_keys,
                "offers": [_offer_row(offer) for offer in opportunity_offers],
                "payment_urls_configured": any(offer.payment_url for offer in opportunity_offers),
                "activation_blockers": blockers,
                "local_paths": _local_paths(opportunity, artifact_dirs),
                "commands": _commands(opportunity, first_offer_key, first_price),
                "publish_gate": _publish_gate(opportunity),
            }
        )
    return rows


class ActivationManifestExporter:
    def __init__(self, output_dir: str | Path, *, artifact_dirs: dict[str, str | Path] | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.artifact_dirs = artifact_dirs or {}

    def export(
        self,
        opportunities_with_assets: list[tuple[RevenueOpportunity, list[AssetDraft]]],
        *,
        offers: list[OfferDraft],
        activation_report: dict | None = None,
    ) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        rows = build_activation_manifest_rows(
            opportunities_with_assets,
            offers=offers,
            artifact_dirs=self.artifact_dirs,
            activation_report=activation_report,
        )
        json_path = self.output_dir / "activation_manifest.json"
        markdown_path = self.output_dir / "ACTIVATE_NOW.md"
        runbook_path = self.output_dir / "RUNBOOK.md"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(_to_markdown(rows), encoding="utf-8")
        runbook_path.write_text(_runbook(rows), encoding="utf-8")
        return [json_path, markdown_path, runbook_path]


def _activation_blockers(report: dict | None) -> list[str]:
    if not report or report.get("ready"):
        return []
    return [str(action) for action in report.get("next_actions", []) if str(action).strip()]


def _offer_row(offer: OfferDraft) -> dict:
    return {
        "offer_key": offer.offer_key,
        "offer_type": offer.offer_type,
        "title": offer.title,
        "price_usd": offer.price_usd,
        "payment_url": offer.payment_url,
        "cta_label": offer.cta_label,
    }


def _local_paths(opportunity: RevenueOpportunity, artifact_dirs: dict[str, str | Path]) -> dict[str, str]:
    external_slug = slugify(opportunity.external_id)
    asset_slug = f"{slugify(opportunity.source)}-{external_slug}"
    paths = {
        "asset_manifest": _join(artifact_dirs.get("asset_output_dir"), asset_slug, "manifest.json"),
        "site_page": _join(artifact_dirs.get("site_output_dir"), external_slug, "index.html"),
        "offers_catalog": _join(artifact_dirs.get("offer_output_dir"), "OFFERS.md"),
        "checkout_setup": _join(artifact_dirs.get("checkout_setup_output_dir"), "CHECKOUT_SETUP.md"),
        "tracking_deploy": _join(artifact_dirs.get("tracking_deploy_output_dir"), "DEPLOY_TRACKING_APP.md"),
        "launch_queue": _join(artifact_dirs.get("launch_queue_output_dir"), "LAUNCH_QUEUE.md"),
        "roadmap": _join(artifact_dirs.get("roadmap_output_dir"), "OPPORTUNITY_ROADMAP.md"),
    }
    if opportunity.channel == "microtool_seo":
        paths["microtool_page"] = _join(artifact_dirs.get("microtool_output_dir"), external_slug, "index.html")
    if opportunity.channel == "digital_product":
        paths["digital_product_pack"] = _join(artifact_dirs.get("digital_product_output_dir"), external_slug, "README.md")
    if opportunity.channel == "paid_setup_kit":
        paths["service_package"] = _join(artifact_dirs.get("service_package_output_dir"), external_slug, "SCOPE.md")
    if opportunity.channel == "niche_report":
        paths["niche_report"] = _join(artifact_dirs.get("niche_report_output_dir"), external_slug, "REPORT.md")
    if opportunity.channel == "article_affiliate":
        paths["affiliate_article"] = _join(artifact_dirs.get("affiliate_article_output_dir"), external_slug, "ARTICLE.md")
    if opportunity.channel in {"github_issue_helper", "open_source_sponsorship"}:
        paths["sponsor_repo_kit"] = _join(artifact_dirs.get("sponsor_repo_output_dir"), external_slug, "README.md")
    return {key: value for key, value in paths.items() if value}


def _join(base: str | Path | None, *parts: str) -> str:
    if not base:
        return ""
    path = str(base).replace("\\", "/").rstrip("/\\")
    for part in parts:
        path += "/" + part.strip("/\\")
    return path


def _commands(opportunity: RevenueOpportunity, offer_key: str, amount: float) -> dict[str, str]:
    external_slug = slugify(opportunity.external_id)
    return {
        "preview_bundle": "python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --bundle-output-dir out/revenue-bundle",
        "record_test_conversion": (
            "python -m farm_loop.main --record-conversion --dry-run "
            "--conversion-provider manual "
            f"--conversion-external-id test-{external_slug} "
            f"--conversion-amount-usd {amount:.2f} "
            f"--conversion-source {opportunity.channel} "
            f"--conversion-offer-key {offer_key}"
        ),
        "preflight": "python -m farm_loop.automation --json",
    }


def _publish_gate(opportunity: RevenueOpportunity) -> str:
    if opportunity.source.lower() in {"stackexchange", "stackoverflow"}:
        return "Manual review required. Publish only on owned channels; do not post AI-generated answers to Stack Overflow."
    if opportunity.channel in {"github_issue_helper", "open_source_sponsorship"}:
        return "Manual review required. Publish in owned repos or useful PRs only; do not add payment links to third-party issues."
    if opportunity.channel == "article_affiliate":
        return "Manual review required. Verify claims, pricing, screenshots, and affiliate terms before publishing."
    return "Manual review required before publishing, connecting checkout, or claiming revenue."


def _to_markdown(rows: list[dict]) -> str:
    lines = ["# Activate Now", ""]
    if not rows:
        lines.append("No opportunities selected in this run.")
        return "\n".join(lines)
    blockers = rows[0].get("activation_blockers", [])
    if blockers:
        lines.extend(["## Global blockers", ""])
        lines.extend(f"- {blocker}" for blocker in blockers)
        lines.append("")
    for row in rows:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Channel: {row['channel']}",
                f"- Expected value: ${row['expected_value_usd']:.2f}",
                f"- Payment configured: {'yes' if row['payment_urls_configured'] else 'no'}",
                f"- Publish gate: {row['publish_gate']}",
            ]
        )
        for path_name, path in row["local_paths"].items():
            lines.append(f"- {path_name}: `{path}`")
        for offer in row["offers"]:
            payment = offer["payment_url"] or "not configured"
            lines.append(f"- Offer: `{offer['offer_key']}` at ${offer['price_usd']:.2f} -> {payment}")
        lines.extend(
            [
                "- Test command:",
                f"  `{row['commands']['record_test_conversion']}`",
                "",
            ]
        )
    return "\n".join(lines)


def _runbook(rows: list[dict]) -> str:
    lines = [
        "# Activation Runbook",
        "",
        "1. Fix global blockers from `ACTIVATE_NOW.md`.",
        "2. Open the local asset and site paths for each selected opportunity.",
        "3. Manually review claims, code, pricing, links, and policy constraints.",
        "4. Connect the checkout URL and copy the matching `offer_key` into provider metadata.",
        "5. Webhook/sale test: run the dry-run conversion command, then repeat live only after credentials are configured.",
        "6. Publish only to owned or explicitly permitted channels.",
        "7. Watch `click_events`, `conversion_events`, dashboard snapshots, and pruning output before scaling.",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Offer keys: {', '.join(row['offer_keys']) or 'none'}",
                f"- Conversion test: `{row['commands']['record_test_conversion']}`",
                "",
            ]
        )
    return "\n".join(lines)
