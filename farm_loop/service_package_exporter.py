from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .offers import generate_offers
from .revenue_scoring import RevenueOpportunity
from .tracking import build_click_redirect_url, build_tracking_url


def build_service_package_rows(
    opportunities: list[RevenueOpportunity],
    *,
    payment_urls: dict[str, str] | None = None,
    intake_url: str = "",
    click_redirect_url: str = "",
) -> list[dict]:
    rows: list[dict] = []
    for opportunity in opportunities:
        if opportunity.channel != "paid_setup_kit":
            continue
        offer = generate_offers(opportunity, payment_urls=payment_urls)[0]
        checkout_url = _tracked_url(
            opportunity,
            offer.payment_url,
            click_redirect_url,
            content=offer.offer_type,
            offer_key=offer.offer_key,
        )
        tracked_intake_url = _tracked_url(
            opportunity,
            intake_url,
            click_redirect_url,
            content="service_intake",
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
                "intake_url": tracked_intake_url,
                "status": "review",
                "scope": _scope(opportunity),
                "out_of_scope": _out_of_scope(),
                "delivery_steps": _delivery_steps(opportunity),
                "handoff_items": _handoff_items(opportunity),
            }
        )
    return rows


class ServicePackageExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        payment_urls: dict[str, str] | None = None,
        intake_url: str = "",
        click_redirect_url: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.payment_urls = payment_urls or {}
        self.intake_url = intake_url
        self.click_redirect_url = click_redirect_url

    def export(self, opportunities: list[RevenueOpportunity]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        rows = build_service_package_rows(
            opportunities,
            payment_urls=self.payment_urls,
            intake_url=self.intake_url,
            click_redirect_url=self.click_redirect_url,
        )

        written: list[Path] = []
        json_path = self.output_dir / "service_packages.json"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(json_path)

        markdown_path = self.output_dir / "SERVICE_PACKAGES.md"
        markdown_path.write_text(_catalog_markdown(rows), encoding="utf-8")
        written.append(markdown_path)

        index_path = self.output_dir / "index.html"
        index_path.write_text(_index_page(rows), encoding="utf-8")
        written.append(index_path)

        for row in rows:
            service_dir = self.output_dir / row["slug"]
            service_dir.mkdir(parents=True, exist_ok=True)
            files = {
                "service.json": json.dumps(row, indent=2, sort_keys=True) + "\n",
                "PROPOSAL.md": _proposal(row),
                "SCOPE.md": _scope_markdown(row),
                "DELIVERY_CHECKLIST.md": _delivery_checklist(row),
                "HANDOFF.md": _handoff(row),
                "index.html": _service_page(row),
            }
            for filename, body in files.items():
                path = service_dir / filename
                path.write_text(body, encoding="utf-8")
                written.append(path)
        return written


def _tracked_url(
    opportunity: RevenueOpportunity,
    target_url: str,
    click_redirect_url: str,
    *,
    content: str,
    offer_key: str,
) -> str:
    if not target_url:
        return ""
    if click_redirect_url:
        return build_click_redirect_url(
            click_redirect_url,
            opportunity,
            target_url=target_url,
            content=content,
            offer_key=offer_key,
        )
    return build_tracking_url(target_url, opportunity, content=content, offer_key=offer_key)


def _scope(opportunity: RevenueOpportunity) -> list[str]:
    tags = {tag.lower() for tag in opportunity.tags}
    items = [
        "Review the current project state and confirm the requested outcome.",
        "Configure one fixed integration or automation path end to end.",
        "Provide a short written handoff with changed files, environment variables, and test evidence.",
    ]
    if "supabase" in tags:
        items.append("Check Supabase keys, webhook table writes, RLS impact, and server-side access boundaries.")
    if "github-actions" in tags:
        items.append("Check workflow cron, secrets, permissions, timeout, and manual dispatch behavior.")
    if "webhook" in tags or "stripe" in tags:
        items.append("Validate one provider webhook payload, signature/token gate, and idempotent conversion recording.")
    return items


def _out_of_scope() -> list[str]:
    return [
        "Unbounded debugging outside the accepted fixed scope.",
        "Handling customer production credentials directly without a safer access path.",
        "Guaranteeing platform approval, revenue, traffic, or third-party account outcomes.",
        "Security testing, scraping, or outreach that is not explicitly authorized.",
    ]


def _delivery_steps(opportunity: RevenueOpportunity) -> list[str]:
    return [
        "Confirm access boundaries",
        "Confirm owner approval, payment status, deadline, and rollback expectations.",
        "Capture baseline screenshots, logs, failing command output, or current webhook state.",
        f"Implement the accepted fixed scope for {opportunity.title}.",
        "Run the documented verification command or provider test event.",
        "Record checkout metadata or manual conversion attribution using the stable offer_key.",
        "Send handoff notes, remaining risks, and exact next steps.",
    ]


def _handoff_items(opportunity: RevenueOpportunity) -> list[str]:
    return [
        f"Summary of completed work for {opportunity.title}.",
        "Files changed or settings configured.",
        "Environment variables and secrets touched by name only, never values.",
        "Verification evidence and command output summary.",
        "Known limitations and recommended next paid scope if any.",
    ]


def _catalog_markdown(rows: list[dict]) -> str:
    lines = ["# Service Packages", ""]
    if not rows:
        lines.append("No paid setup kit opportunities selected in this run.")
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
                f"- Intake URL: {row['intake_url'] or 'configure SERVICE_INTAKE_URL before publishing'}",
                f"- Package folder: {row['slug']}/",
                "",
            ]
        )
    return "\n".join(lines)


def _proposal(row: dict) -> str:
    return "\n".join(
        [
            f"# Fixed Scope Proposal: {row['title']}",
            "",
            row["problem"],
            "",
            f"Price: ${row['price_usd']:.2f}",
            f"Offer key: `{row['offer_key']}`",
            "",
            "## What is included",
            "",
            *[f"- {item}" for item in row["scope"]],
            "",
            "## Acceptance criteria",
            "",
            "- The agreed setup path works in one reviewed environment.",
            "- Verification evidence is documented in the handoff.",
            "- Any follow-up work is listed separately instead of expanding scope silently.",
            "",
        ]
    )


def _scope_markdown(row: dict) -> str:
    return "\n".join(
        [
            f"# Scope: {row['title']}",
            "",
            "## In scope",
            "",
            *[f"- {item}" for item in row["scope"]],
            "",
            "## Out of scope",
            "",
            *[f"- {item}" for item in row["out_of_scope"]],
            "",
        ]
    )


def _delivery_checklist(row: dict) -> str:
    return "\n".join(
        [
            f"# Delivery Checklist: {row['title']}",
            "",
            *[f"- [ ] {item}" for item in row["delivery_steps"]],
            "",
        ]
    )


def _handoff(row: dict) -> str:
    return "\n".join(
        [
            f"# Handoff: {row['title']}",
            "",
            *[f"- {item}" for item in row["handoff_items"]],
            "",
            "Do not include secret values in the handoff.",
            "",
        ]
    )


def _index_page(rows: list[dict]) -> str:
    cards = "\n".join(_service_card(row) for row in rows) or '<p class="notice">No service packages selected.</p>'
    return _page(
        "Service Packages",
        f"""
        <main class="shell">
          <header class="topbar">
            <strong>Infinite Revenue Engine</strong>
            <span>service packages</span>
          </header>
          <section class="hero">
            <h1>Service Packages</h1>
            <p>Reviewable fixed-scope service packages for paid setup kits, intake, delivery, and handoff.</p>
          </section>
          <section class="grid" aria-label="Service packages">
            {cards}
          </section>
        </main>
        """,
    )


def _service_card(row: dict) -> str:
    return f"""
    <article class="card">
      <p class="channel">{escape(row['channel'].replace("_", " "))}</p>
      <h2><a href="{escape(row['slug'])}/">{escape(row['title'])}</a></h2>
      <p>{escape(row['problem'])}</p>
      <p>${row['price_usd']:.2f} fixed scope</p>
    </article>
    """


def _service_page(row: dict) -> str:
    scope = "\n".join(f"<li>{escape(item)}</li>" for item in row["scope"])
    delivery = "\n".join(f"<li>{escape(item)}</li>" for item in row["delivery_steps"])
    ctas = "\n".join(_cta_links(row)) or '<p class="notice">Configure payment and intake URLs before publishing.</p>'
    return _page(
        row["title"],
        f"""
        <main class="shell">
          <header class="topbar">
            <a href="../">Service Packages</a>
            <span>manual review</span>
          </header>
          <section class="hero">
            <h1>{escape(row['title'])}</h1>
            <p>{escape(row['problem'])}</p>
            {ctas}
          </section>
          <section class="card">
            <h2>Scope</h2>
            <ul>{scope}</ul>
            <h2>Delivery steps</h2>
            <ul>{delivery}</ul>
            <p>Offer key: <code>{escape(row['offer_key'])}</code></p>
          </section>
        </main>
        """,
    )


def _cta_links(row: dict) -> list[str]:
    links: list[str] = []
    if row["checkout_url"]:
        links.append(f'<p class="notice"><a href="{escape(row["checkout_url"])}">Pay fixed scope</a></p>')
    if row["intake_url"]:
        links.append(f'<p class="notice"><a href="{escape(row["intake_url"])}">Start intake</a></p>')
    return links


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
