from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .revenue_scoring import RevenueOpportunity
from .tracking import build_click_redirect_url, build_tracking_url


SAFETY_NOTES = [
    "No automated outreach, no mass issue comments, and no payment links in third-party repositories.",
    "Publish only in an owned GitHub repository after manual review.",
    "Use GitHub Sponsors, support links, or paid support only where the relationship is clearly disclosed.",
]


def build_sponsor_repo_rows(
    opportunities: list[RevenueOpportunity],
    *,
    sponsor_urls: dict[str, str] | None = None,
    click_redirect_url: str = "",
) -> list[dict]:
    rows: list[dict] = []
    for opportunity in opportunities:
        if not _is_sponsorship(opportunity):
            continue
        sponsor_url = _sponsor_url(opportunity, sponsor_urls or {})
        tracked_sponsor_url = _tracked_sponsor_url(opportunity, sponsor_url, click_redirect_url)
        rows.append(
            {
                "source": opportunity.source,
                "external_id": opportunity.external_id,
                "slug": slugify(opportunity.external_id),
                "repo_name": slugify(opportunity.external_id),
                "title": opportunity.title,
                "problem": opportunity.problem,
                "tags": opportunity.tags,
                "channel": opportunity.channel,
                "status": "review",
                "sponsor_url": sponsor_url,
                "tracked_sponsor_url": tracked_sponsor_url,
                "funding_custom_urls": [sponsor_url] if sponsor_url else [],
                "sponsor_tiers": _sponsor_tiers(opportunity),
                "included_files": _included_files(),
                "safety_notes": SAFETY_NOTES,
                "repo_pitch": _repo_pitch(opportunity),
            }
        )
    return rows


class SponsorRepoExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        sponsor_urls: dict[str, str] | None = None,
        click_redirect_url: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.sponsor_urls = sponsor_urls or {}
        self.click_redirect_url = click_redirect_url

    def export(self, opportunities: list[RevenueOpportunity]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        rows = build_sponsor_repo_rows(
            opportunities,
            sponsor_urls=self.sponsor_urls,
            click_redirect_url=self.click_redirect_url,
        )

        written: list[Path] = []
        json_path = self.output_dir / "sponsor_repos.json"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(json_path)

        markdown_path = self.output_dir / "SPONSOR_REPOS.md"
        markdown_path.write_text(_catalog_markdown(rows), encoding="utf-8")
        written.append(markdown_path)

        index_path = self.output_dir / "index.html"
        index_path.write_text(_index_page(rows), encoding="utf-8")
        written.append(index_path)

        for row in rows:
            repo_dir = self.output_dir / row["slug"]
            issue_template_dir = repo_dir / ".github" / "ISSUE_TEMPLATE"
            examples_dir = repo_dir / "examples"
            issue_template_dir.mkdir(parents=True, exist_ok=True)
            examples_dir.mkdir(parents=True, exist_ok=True)

            files = {
                "README.md": _readme(row),
                "CONTRIBUTING.md": _contributing(row),
                "ROADMAP.md": _roadmap(row),
                "index.html": _repo_page(row),
                ".github/FUNDING.yml": _funding_yml(row),
                ".github/ISSUE_TEMPLATE/support.yml": _support_issue_template(row),
                "examples/usage.md": _usage_example(row),
            }
            for relative_path, body in files.items():
                path = repo_dir / relative_path
                path.write_text(body, encoding="utf-8")
                written.append(path)
        return written


def _is_sponsorship(opportunity: RevenueOpportunity) -> bool:
    return opportunity.channel == "open_source_sponsorship"


def _sponsor_url(opportunity: RevenueOpportunity, sponsor_urls: dict[str, str]) -> str:
    normalized = {key.strip().lower(): value.strip() for key, value in sponsor_urls.items() if key.strip() and value.strip()}
    for tag in opportunity.tags:
        tag_key = tag.lower()
        if tag_key in normalized:
            return normalized[tag_key]
    return normalized.get("github") or normalized.get("sponsorship") or normalized.get("*", "")


def _tracked_sponsor_url(opportunity: RevenueOpportunity, sponsor_url: str, click_redirect_url: str) -> str:
    if not sponsor_url:
        return ""
    if click_redirect_url:
        return build_click_redirect_url(
            click_redirect_url,
            opportunity,
            target_url=sponsor_url,
            content="github_sponsors",
        )
    return build_tracking_url(sponsor_url, opportunity, content="github_sponsors")


def _sponsor_tiers(opportunity: RevenueOpportunity) -> list[dict]:
    return [
        {
            "name": "Backer",
            "price_usd": 5,
            "description": f"Support maintenance and examples for {opportunity.title}.",
        },
        {
            "name": "Builder",
            "price_usd": 25,
            "description": "Priority issue review for owned repo questions and practical setup notes.",
        },
        {
            "name": "Setup Partner",
            "price_usd": 99,
            "description": "Fixed-scope setup help after intake, acceptance, and manual review.",
        },
    ]


def _included_files() -> list[str]:
    return [
        "README.md",
        "CONTRIBUTING.md",
        "ROADMAP.md",
        ".github/FUNDING.yml",
        ".github/ISSUE_TEMPLATE/support.yml",
        "examples/usage.md",
        "index.html",
    ]


def _repo_pitch(opportunity: RevenueOpportunity) -> str:
    return f"{opportunity.title} is an owned open-source resource for this problem: {opportunity.problem}"


def _catalog_markdown(rows: list[dict]) -> str:
    lines = ["# Sponsor Repo Kits", ""]
    if not rows:
        lines.append("No open-source sponsorship opportunities selected in this run.")
        return "\n".join(lines) + "\n"
    for row in rows:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Status: {row['status']}",
                f"- Repo folder: {row['slug']}/",
                f"- Sponsor URL: {row['sponsor_url'] or 'configure SPONSOR_URLS before publishing'}",
                f"- Funding file: {row['slug']}/.github/FUNDING.yml",
                f"- README: {row['slug']}/README.md",
                "",
            ]
        )
    return "\n".join(lines)


def _readme(row: dict) -> str:
    tiers = "\n".join(f"- {tier['name']}: ${tier['price_usd']} - {tier['description']}" for tier in row["sponsor_tiers"])
    notes = "\n".join(f"- {note}" for note in row["safety_notes"])
    sponsor_line = (
        f"[Sponsor this work]({row['tracked_sponsor_url']})"
        if row["tracked_sponsor_url"]
        else "Configure SPONSOR_URLS before publishing the sponsor CTA."
    )
    return "\n".join(
        [
            f"# {row['title']}",
            "",
            row["repo_pitch"],
            "",
            "## GitHub Sponsors",
            "",
            sponsor_line,
            "",
            "## Sponsor tiers",
            "",
            tiers,
            "",
            "## Safety",
            "",
            notes,
            "",
            "## Manual review",
            "",
            "Review claims, examples, sponsor pricing, and support promises before creating the public repo.",
            "",
        ]
    )


def _funding_yml(row: dict) -> str:
    if not row["funding_custom_urls"]:
        return "# Configure SPONSOR_URLS before publishing.\ncustom: []\n"
    urls = "\n".join(f"  - {json.dumps(url)}" for url in row["funding_custom_urls"])
    return f"custom:\n{urls}\n"


def _support_issue_template(row: dict) -> str:
    return "\n".join(
        [
            "name: paid support request",
            "description: Request paid support for this owned repo after reviewing scope.",
            "title: \"[Support]: \"",
            "labels: [support, needs-triage]",
            "body:",
            "  - type: markdown",
            "    attributes:",
            f"      value: \"Use this only for a paid support request related to {row['title']}.\"",
            "  - type: textarea",
            "    id: scope",
            "    attributes:",
            "      label: Scope",
            "      description: Describe the repo, deadline, stack, and success criteria.",
            "    validations:",
            "      required: true",
            "",
        ]
    )


def _contributing(row: dict) -> str:
    notes = "\n".join(f"- {note}" for note in row["safety_notes"])
    return "\n".join(
        [
            f"# Contributing to {row['title']}",
            "",
            "Contributions are welcome after manual review.",
            "",
            "## Rules",
            "",
            notes,
            "- Keep examples reproducible and small.",
            "- Do not add affiliate or sponsor links to third-party issues.",
            "",
        ]
    )


def _roadmap(row: dict) -> str:
    return "\n".join(
        [
            f"# Roadmap: {row['title']}",
            "",
            "## Sponsor tiers",
            "",
            *[f"- [ ] Validate {tier['name']} tier at ${tier['price_usd']}." for tier in row["sponsor_tiers"]],
            "",
            "## Repo launch",
            "",
            "- [ ] Create owned GitHub repo.",
            "- [ ] Copy these files into the repo.",
            "- [ ] Enable GitHub Sponsors or configure a permitted support link.",
            "- [ ] Publish examples and link the repo from the owned site.",
            "- [ ] Track clicks and confirmed revenue in Supabase.",
            "",
        ]
    )


def _usage_example(row: dict) -> str:
    return "\n".join(
        [
            f"# Usage Example: {row['title']}",
            "",
            "This is a placeholder usage example for manual completion.",
            "",
            "1. Replace this with a real command, screenshot, or checklist.",
            "2. Add proof that the result works.",
            "3. Link back to the owned repo README and sponsor CTA.",
            "",
        ]
    )


def _index_page(rows: list[dict]) -> str:
    cards = "\n".join(_repo_card(row) for row in rows) or '<p class="notice">No sponsor repo kits selected.</p>'
    return _page(
        "Sponsor Repo Kits",
        f"""
        <main class="shell">
          <header class="topbar">
            <strong>Infinite Revenue Engine</strong>
            <span>sponsor repos</span>
          </header>
          <section class="hero">
            <h1>Sponsor Repo Kits</h1>
            <p>Reviewable open-source repo kits for GitHub Sponsors, support offers, and owned documentation.</p>
          </section>
          <section class="grid" aria-label="Sponsor repo kits">
            {cards}
          </section>
        </main>
        """,
    )


def _repo_card(row: dict) -> str:
    return f"""
    <article class="card">
      <p class="channel">{escape(row['channel'].replace("_", " "))}</p>
      <h2><a href="{escape(row['slug'])}/">{escape(row['title'])}</a></h2>
      <p>{escape(row['problem'])}</p>
      <p>{escape(row['safety_notes'][0])}</p>
    </article>
    """


def _repo_page(row: dict) -> str:
    tiers = "\n".join(
        f"<li><strong>{escape(tier['name'])}</strong>: ${tier['price_usd']} - {escape(tier['description'])}</li>"
        for tier in row["sponsor_tiers"]
    )
    files = "\n".join(f"<li>{escape(filename)}</li>" for filename in row["included_files"])
    cta = _sponsor_cta(row)
    return _page(
        row["title"],
        f"""
        <main class="shell">
          <header class="topbar">
            <a href="../">Sponsor Repo Kits</a>
            <span>manual review</span>
          </header>
          <section class="hero">
            <h1>{escape(row['title'])}</h1>
            <p>{escape(row['problem'])}</p>
            {cta}
          </section>
          <section class="card">
            <h2>Included files</h2>
            <ul>{files}</ul>
            <h2>Sponsor tiers</h2>
            <ul>{tiers}</ul>
            <p class="notice">{escape(row['safety_notes'][0])}</p>
          </section>
        </main>
        """,
    )


def _sponsor_cta(row: dict) -> str:
    if not row["tracked_sponsor_url"]:
        return '<p class="notice">Configure SPONSOR_URLS before publishing sponsor CTAs.</p>'
    return f'<p class="notice"><a href="{escape(row["tracked_sponsor_url"])}">Sponsor this work</a></p>'


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
