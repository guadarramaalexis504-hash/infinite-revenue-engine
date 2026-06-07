from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .revenue_scoring import RevenueOpportunity
from .tracking import build_click_redirect_url, build_tracking_url


def build_lead_magnet_rows(
    opportunities: list[RevenueOpportunity],
    *,
    lead_capture_url: str = "",
    click_redirect_url: str = "",
) -> list[dict]:
    rows: list[dict] = []
    for opportunity in opportunities:
        if not _is_lead_magnet(opportunity):
            continue
        opt_in_url = ""
        if lead_capture_url:
            if click_redirect_url:
                opt_in_url = build_click_redirect_url(
                    click_redirect_url,
                    opportunity,
                    target_url=lead_capture_url,
                    content="lead_magnet_opt_in",
                )
            else:
                opt_in_url = build_tracking_url(lead_capture_url, opportunity, content="lead_magnet_opt_in")
        rows.append(
            {
                "source": opportunity.source,
                "external_id": opportunity.external_id,
                "slug": slugify(opportunity.external_id),
                "title": opportunity.title,
                "problem": opportunity.problem,
                "tags": opportunity.tags,
                "channel": opportunity.channel,
                "expected_value_usd": opportunity.expected_value_usd,
                "status": "review",
                "opt_in_url": opt_in_url,
                "checklist_items": _checklist_items(opportunity),
            }
        )
    return rows


class LeadMagnetExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        lead_capture_url: str = "",
        click_redirect_url: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.lead_capture_url = lead_capture_url
        self.click_redirect_url = click_redirect_url

    def export(self, opportunities: list[RevenueOpportunity]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        rows = build_lead_magnet_rows(
            opportunities,
            lead_capture_url=self.lead_capture_url,
            click_redirect_url=self.click_redirect_url,
        )

        written: list[Path] = []
        json_path = self.output_dir / "lead_magnets.json"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(json_path)

        markdown_path = self.output_dir / "LEAD_MAGNETS.md"
        markdown_path.write_text(_markdown(rows), encoding="utf-8")
        written.append(markdown_path)

        index_path = self.output_dir / "index.html"
        index_path.write_text(_index_page(rows), encoding="utf-8")
        written.append(index_path)

        for row in rows:
            lead_dir = self.output_dir / row["slug"]
            lead_dir.mkdir(parents=True, exist_ok=True)
            page_path = lead_dir / "index.html"
            page_path.write_text(_landing_page(row), encoding="utf-8")
            written.append(page_path)

            checklist_path = lead_dir / "checklist.md"
            checklist_path.write_text(_checklist_markdown(row), encoding="utf-8")
            written.append(checklist_path)

        return written


def _is_lead_magnet(opportunity: RevenueOpportunity) -> bool:
    normalized_tags = {tag.lower().replace("_", "-") for tag in opportunity.tags}
    return opportunity.channel == "lead_magnet" or "lead-magnet" in normalized_tags


def _checklist_items(opportunity: RevenueOpportunity) -> list[str]:
    tags = {tag.lower() for tag in opportunity.tags}
    items = [
        f"Define the painful outcome this solves: {opportunity.problem}",
        "List the exact prerequisites before someone starts.",
        "Add a quick self-audit so the reader can score their current setup.",
        "Include one copy-paste command, query, or template when safe.",
        "Add proof notes: source, screenshot, test output, or manual verification.",
        "Write the next paid help offer in one plain sentence.",
        "Add attribution fields before publishing: source, external_id, and campaign.",
        "Review the final checklist manually before public release.",
    ]
    if "supabase" in tags:
        items.insert(1, "Review RLS policies, service-role key exposure, backups, auth redirects, and storage policies.")
    if "github-actions" in tags or "github" in tags:
        items.insert(1, "Review workflow permissions, secret usage, cron frequency, and failed-run recovery.")
    if "automation" in tags or "ai" in tags:
        items.insert(1, "Estimate manual time saved, API cost, failure cases, and rollback steps.")
    return items


def _markdown(rows: list[dict]) -> str:
    lines = ["# Lead Magnets", ""]
    if not rows:
        lines.append("No lead magnet opportunities selected in this run.")
        return "\n".join(lines) + "\n"
    for row in rows:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Status: {row['status']}",
                f"- Source: {row['source']}:{row['external_id']}",
                f"- Opt-in URL: {row['opt_in_url'] or 'configure LEAD_CAPTURE_URL before publishing'}",
                f"- Landing page: {row['slug']}/index.html",
                f"- Checklist: {row['slug']}/checklist.md",
                "",
            ]
        )
    return "\n".join(lines)


def _checklist_markdown(row: dict) -> str:
    lines = [f"# {row['title']}", "", row["problem"], "", "## Checklist", ""]
    lines.extend(f"- [ ] {item}" for item in row["checklist_items"])
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "Review this checklist, connect the opt-in form, then publish only on owned or explicitly permitted channels.",
            "",
        ]
    )
    return "\n".join(lines)


def _index_page(rows: list[dict]) -> str:
    cards = "\n".join(_lead_card(row) for row in rows) or '<p class="notice">No lead magnets selected.</p>'
    return _page(
        "Lead Magnets",
        f"""
        <main class="shell">
          <header class="topbar">
            <strong>Infinite Revenue Engine</strong>
            <span>lead magnets</span>
          </header>
          <section class="hero">
            <h1>Lead Magnets</h1>
            <p>Reviewable opt-in assets for building an owned audience before selling setup services, templates, or support.</p>
          </section>
          <section class="grid" aria-label="Lead magnet drafts">
            {cards}
          </section>
        </main>
        """,
    )


def _lead_card(row: dict) -> str:
    return f"""
    <article class="card">
      <p class="channel">{escape(row['channel'].replace("_", " "))}</p>
      <h2><a href="{escape(row['slug'])}/">{escape(row['title'])}</a></h2>
      <p>{escape(row['problem'])}</p>
      <p><a href="{escape(row['slug'])}/checklist.md">Review checklist</a></p>
    </article>
    """


def _landing_page(row: dict) -> str:
    items = "\n".join(f"<li>{escape(item)}</li>" for item in row["checklist_items"][:6])
    cta = _opt_in_cta(row)
    return _page(
        row["title"],
        f"""
        <main class="shell">
          <header class="topbar">
            <a href="../">Lead Magnets</a>
            <span>manual review</span>
          </header>
          <section class="hero">
            <p class="channel">{escape(row['channel'].replace("_", " "))}</p>
            <h1>{escape(row['title'])}</h1>
            <p>{escape(row['problem'])}</p>
            {cta}
          </section>
          <section class="card">
            <h2>What the checklist covers</h2>
            <ul>{items}</ul>
            <p><a href="checklist.md">Review the Markdown checklist</a></p>
          </section>
        </main>
        """,
    )


def _opt_in_cta(row: dict) -> str:
    if not row["opt_in_url"]:
        return '<p class="notice">Configure LEAD_CAPTURE_URL before publishing this opt-in page.</p>'
    return f'<p class="notice"><a href="{escape(row["opt_in_url"])}">Get the checklist</a></p>'


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
