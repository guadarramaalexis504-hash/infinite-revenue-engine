from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .offers import generate_offers
from .revenue_scoring import RevenueOpportunity
from .tracking import build_click_redirect_url, build_tracking_url


def build_digital_product_rows(
    opportunities: list[RevenueOpportunity],
    *,
    payment_urls: dict[str, str] | None = None,
    click_redirect_url: str = "",
) -> list[dict]:
    rows: list[dict] = []
    for opportunity in opportunities:
        if opportunity.channel != "digital_product":
            continue
        offer = generate_offers(opportunity, payment_urls=payment_urls)[0]
        checkout_url = ""
        if offer.payment_url:
            if click_redirect_url:
                checkout_url = build_click_redirect_url(
                    click_redirect_url,
                    opportunity,
                    target_url=offer.payment_url,
                    content=offer.offer_type,
                    offer_key=offer.offer_key,
                )
            else:
                checkout_url = build_tracking_url(
                    offer.payment_url,
                    opportunity,
                    content=offer.offer_type,
                    offer_key=offer.offer_key,
                )
        rows.append(
            {
                "source": opportunity.source,
                "external_id": opportunity.external_id,
                "slug": slugify(opportunity.external_id),
                "title": opportunity.title,
                "problem": opportunity.problem,
                "tags": opportunity.tags,
                "channel": opportunity.channel,
                "offer_key": offer.offer_key,
                "price_usd": offer.price_usd,
                "checkout_url": checkout_url,
                "status": "review",
                "included_files": _included_files(opportunity),
                "store_summary": _store_summary(opportunity),
            }
        )
    return rows


class DigitalProductExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        payment_urls: dict[str, str] | None = None,
        click_redirect_url: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.payment_urls = payment_urls or {}
        self.click_redirect_url = click_redirect_url

    def export(self, opportunities: list[RevenueOpportunity]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        rows = build_digital_product_rows(
            opportunities,
            payment_urls=self.payment_urls,
            click_redirect_url=self.click_redirect_url,
        )

        written: list[Path] = []
        json_path = self.output_dir / "digital_products.json"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(json_path)

        markdown_path = self.output_dir / "DIGITAL_PRODUCTS.md"
        markdown_path.write_text(_catalog_markdown(rows), encoding="utf-8")
        written.append(markdown_path)

        for row in rows:
            product_dir = self.output_dir / row["slug"]
            product_dir.mkdir(parents=True, exist_ok=True)
            product_files = {
                "product.json": json.dumps(row, indent=2, sort_keys=True) + "\n",
                "README.md": _readme(row),
                "STORE_LISTING.md": _store_listing(row),
                "LAUNCH_CHECKLIST.md": _launch_checklist(row),
                "index.html": _landing_page(row),
            }
            for filename, body in product_files.items():
                path = product_dir / filename
                path.write_text(body, encoding="utf-8")
                written.append(path)
        return written


def _included_files(opportunity: RevenueOpportunity) -> list[str]:
    tags = {tag.lower() for tag in opportunity.tags}
    files = [
        "README.md",
        "STORE_LISTING.md",
        "LAUNCH_CHECKLIST.md",
        "product.json",
    ]
    if "fastapi" in tags:
        files.append("app/main.py")
        files.append(".env.example")
    if "supabase" in tags:
        files.append("supabase/schema.sql")
        files.append("docs/supabase-security-checklist.md")
    if "github-actions" in tags or "release" in tags:
        files.append(".github/workflows/release.yml")
    if "excel" in tags or "saas" in tags:
        files.append("metrics-template.csv")
    return files


def _store_summary(opportunity: RevenueOpportunity) -> str:
    return f"{opportunity.title} helps with: {opportunity.problem}"


def _catalog_markdown(rows: list[dict]) -> str:
    lines = ["# Digital Products", ""]
    if not rows:
        lines.append("No digital product opportunities selected in this run.")
        return "\n".join(lines) + "\n"
    for row in rows:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Status: {row['status']}",
                f"- Offer Key: {row['offer_key']}",
                f"- Price: ${row['price_usd']:.2f}",
                f"- Checkout URL: {row['checkout_url'] or 'configure OFFER_PAYMENT_URLS before publishing'}",
                f"- Product folder: {row['slug']}/",
                "",
            ]
        )
    return "\n".join(lines)


def _readme(row: dict) -> str:
    files = "\n".join(f"- `{filename}`" for filename in row["included_files"])
    return "\n".join(
        [
            f"# {row['title']}",
            "",
            row["problem"],
            "",
            "## Included Files",
            "",
            files,
            "",
            "## Manual Review",
            "",
            "Verify every file, command, price, screenshot, and claim before uploading this product to a store.",
            "",
        ]
    )


def _store_listing(row: dict) -> str:
    return "\n".join(
        [
            "## Store Listing",
            "",
            f"Title: {row['title']}",
            f"Price: ${row['price_usd']:.2f}",
            f"Offer key metadata: `{row['offer_key']}`",
            "",
            "Description:",
            row["store_summary"],
            "",
            "Delivery:",
            "Upload the reviewed product folder as a zip on Gumroad, Lemon Squeezy, Stripe, or another owned store.",
            "",
        ]
    )


def _launch_checklist(row: dict) -> str:
    items = [
        "Review all generated files manually.",
        "Set checkout metadata: `offer_key`, `ire_offer_key`, `source`, and `external_id`.",
        "Connect the payment URL in `OFFER_PAYMENT_URLS`.",
        "Verify the checkout success event reaches `/webhooks/conversion/<provider>`.",
        "Publish only on owned store pages, owned repo pages, newsletter, or explicitly permitted channels.",
        "Record a manual conversion with `--record-conversion` if the provider webhook is not connected yet.",
    ]
    return "\n".join([f"# Launch Checklist: {row['title']}", "", *[f"- [ ] {item}" for item in items], ""])


def _landing_page(row: dict) -> str:
    files = "\n".join(f"<li>{escape(filename)}</li>" for filename in row["included_files"][:6])
    cta = _checkout_cta(row)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(row['title'])}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f3;
      --ink: #17201b;
      --muted: #5c665f;
      --line: #d8ddd5;
      --surface: #ffffff;
      --accent: #116a5b;
      --accent-soft: #e2f3ee;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Arial, Helvetica, sans-serif; line-height: 1.5; }}
    a {{ color: var(--accent); text-decoration: none; font-weight: 700; }}
    a:hover {{ text-decoration: underline; }}
    .shell {{ max-width: 920px; margin: 0 auto; padding: 28px 20px 56px; }}
    .hero {{ padding: 56px 0 40px; border-top: 1px solid var(--line); }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4.25rem); line-height: 0.98; letter-spacing: 0; }}
    .lead {{ max-width: 760px; color: var(--muted); font-size: 1.08rem; }}
    .card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 18px; }}
    .notice {{ background: var(--accent-soft); border: 1px solid #b6dbd2; border-radius: 8px; padding: 14px 16px; }}
    li {{ margin: 8px 0; }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>{escape(row['title'])}</h1>
      <p class="lead">{escape(row['problem'])}</p>
      {cta}
    </section>
    <section class="card">
      <h2>Included in the pack</h2>
      <ul>{files}</ul>
      <p>Offer key: <code>{escape(row['offer_key'])}</code></p>
    </section>
  </main>
</body>
</html>
"""


def _checkout_cta(row: dict) -> str:
    if not row["checkout_url"]:
        return '<p class="notice">Configure OFFER_PAYMENT_URLS before publishing this product.</p>'
    return f'<p class="notice"><a href="{escape(row["checkout_url"])}">Get the product</a></p>'
