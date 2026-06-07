from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .offers import generate_offers
from .revenue_scoring import RevenueOpportunity
from .tracking import build_click_redirect_url, build_tracking_url


REVIEW_GATE = (
    "Do not claim market size, rankings, or revenue potential until every source, keyword, and comparison "
    "has been manually verified."
)


def build_niche_report_rows(
    opportunities: list[RevenueOpportunity],
    *,
    payment_urls: dict[str, str] | None = None,
    click_redirect_url: str = "",
) -> list[dict]:
    rows: list[dict] = []
    for opportunity in opportunities:
        if opportunity.channel != "niche_report":
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
                "report_sections": _report_sections(opportunity),
                "validation_steps": _validation_steps(opportunity),
                "store_summary": _store_summary(opportunity),
                "review_gate": REVIEW_GATE,
            }
        )
    return rows


class NicheReportExporter:
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
        rows = build_niche_report_rows(
            opportunities,
            payment_urls=self.payment_urls,
            click_redirect_url=self.click_redirect_url,
        )

        written: list[Path] = []
        json_path = self.output_dir / "niche_reports.json"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(json_path)

        catalog_path = self.output_dir / "NICHE_REPORTS.md"
        catalog_path.write_text(_catalog_markdown(rows), encoding="utf-8")
        written.append(catalog_path)

        index_path = self.output_dir / "index.html"
        index_path.write_text(_index_page(rows), encoding="utf-8")
        written.append(index_path)

        for row in rows:
            report_dir = self.output_dir / row["slug"]
            report_dir.mkdir(parents=True, exist_ok=True)
            files = {
                "REPORT.md": _report_markdown(row),
                "STORE_LISTING.md": _store_listing(row),
                "VALIDATION_PLAN.md": _validation_plan(row),
                "index.html": _report_page(row),
            }
            for filename, body in files.items():
                path = report_dir / filename
                path.write_text(body, encoding="utf-8")
                written.append(path)
        return written


def _report_sections(opportunity: RevenueOpportunity) -> list[str]:
    tags = ", ".join(opportunity.tags)
    return [
        f"Keyword clusters and search intent around: {tags}.",
        "Audience segments, buyer pain, and urgency signals.",
        "Existing products, templates, tools, communities, and affiliate programs to verify.",
        "Content gaps and low-competition page ideas for owned publishing.",
        "Potential paid offers: mini-report, template pack, setup service, affiliate comparison, or lead magnet.",
        "Validation evidence to collect before publishing.",
        "Risks, excluded claims, and manual review notes.",
    ]


def _validation_steps(opportunity: RevenueOpportunity) -> list[str]:
    return [
        f"Verify that {opportunity.title} has current search demand using a permitted keyword tool or owned analytics.",
        "Collect at least five competing pages or products and summarize their positioning.",
        "Check whether payment, affiliate, or sponsor paths are allowed for the niche.",
        "Write one owned landing page and one free preview before selling the full report.",
        "Record clicks and confirmed purchases through the tracking app or manual conversion command.",
    ]


def _store_summary(opportunity: RevenueOpportunity) -> str:
    return f"A manually reviewed niche report for: {opportunity.problem}"


def _catalog_markdown(rows: list[dict]) -> str:
    lines = ["# Niche Reports", ""]
    if not rows:
        lines.append("No niche report opportunities selected in this run.")
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
                f"- Report folder: {row['slug']}/",
                "",
            ]
        )
    return "\n".join(lines)


def _report_markdown(row: dict) -> str:
    return "\n".join(
        [
            f"# {row['title']}",
            "",
            row["problem"],
            "",
            "## Report Sections",
            "",
            *[f"- {section}" for section in row["report_sections"]],
            "",
            "## Review Gate",
            "",
            row["review_gate"],
            "",
        ]
    )


def _store_listing(row: dict) -> str:
    return "\n".join(
        [
            "# Store Listing",
            "",
            f"Title: {row['title']}",
            f"Price: ${row['price_usd']:.2f}",
            f"Offer key metadata: `{row['offer_key']}`",
            "",
            "Description:",
            row["store_summary"],
            "",
            "Delivery:",
            "Upload a manually verified PDF/Markdown report and include the free preview on your owned site.",
            "",
        ]
    )


def _validation_plan(row: dict) -> str:
    return "\n".join(
        [
            f"# Validation Plan: {row['title']}",
            "",
            *[f"- [ ] {step}" for step in row["validation_steps"]],
            "",
            row["review_gate"],
            "",
        ]
    )


def _index_page(rows: list[dict]) -> str:
    cards = "\n".join(_report_card(row) for row in rows) or '<p class="notice">No niche reports selected.</p>'
    return _page(
        "Niche Reports",
        f"""
        <main class="shell">
          <header class="topbar">
            <strong>Infinite Revenue Engine</strong>
            <span>niche reports</span>
          </header>
          <section class="hero">
            <h1>Niche Reports</h1>
            <p>Reviewable paid mini-report drafts for validating small markets, SEO angles, and product opportunities.</p>
          </section>
          <section class="grid" aria-label="Niche report drafts">
            {cards}
          </section>
        </main>
        """,
    )


def _report_card(row: dict) -> str:
    return f"""
    <article class="card">
      <p class="channel">{escape(row['channel'].replace("_", " "))}</p>
      <h2><a href="{escape(row['slug'])}/">{escape(row['title'])}</a></h2>
      <p>{escape(row['problem'])}</p>
      <p>${row['price_usd']:.2f} paid report draft</p>
    </article>
    """


def _report_page(row: dict) -> str:
    sections = "\n".join(f"<li>{escape(section)}</li>" for section in row["report_sections"])
    checkout = _checkout_cta(row)
    return _page(
        row["title"],
        f"""
        <main class="shell">
          <header class="topbar">
            <a href="../">Niche Reports</a>
            <span>manual review</span>
          </header>
          <section class="hero">
            <h1>{escape(row['title'])}</h1>
            <p>{escape(row['problem'])}</p>
            {checkout}
          </section>
          <section class="card">
            <h2>Report sections</h2>
            <ul>{sections}</ul>
            <p class="notice">{escape(row['review_gate'])}</p>
            <p>Offer key: <code>{escape(row['offer_key'])}</code></p>
          </section>
        </main>
        """,
    )


def _checkout_cta(row: dict) -> str:
    if not row["checkout_url"]:
        return '<p class="notice">Configure OFFER_PAYMENT_URLS before publishing paid reports.</p>'
    return f'<p class="notice"><a href="{escape(row["checkout_url"])}">Get the report</a></p>'


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
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
    .shell {{ max-width: 1040px; margin: 0 auto; padding: 28px 20px 56px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; padding: 12px 0 28px; color: var(--muted); }}
    .hero {{ padding: 56px 0 40px; border-top: 1px solid var(--line); max-width: 760px; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4.25rem); line-height: 0.98; letter-spacing: 0; }}
    h2 {{ letter-spacing: 0; }}
    .hero p {{ color: var(--muted); font-size: 1.08rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 18px; }}
    .channel {{ margin: 0 0 8px; color: var(--accent); text-transform: uppercase; font-size: 0.78rem; font-weight: 700; }}
    .notice {{ background: var(--accent-soft); border: 1px solid #b6dbd2; border-radius: 8px; padding: 14px 16px; }}
    li {{ margin: 8px 0; }}
    @media (max-width: 640px) {{ .topbar {{ display: grid; }} }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
