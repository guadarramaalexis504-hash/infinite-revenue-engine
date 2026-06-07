from __future__ import annotations

import json
from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .revenue_scoring import RevenueOpportunity
from .tracking import build_click_redirect_url, build_tracking_url


DISCLOSURE = (
    "Disclosure: this article may include affiliate links. Use only honest, allowed affiliate programs, "
    "review claims manually, and never hide paid relationships."
)


def build_affiliate_article_rows(
    opportunities: list[RevenueOpportunity],
    *,
    affiliate_urls: dict[str, str] | None = None,
    click_redirect_url: str = "",
) -> list[dict]:
    rows: list[dict] = []
    for opportunity in opportunities:
        if opportunity.channel != "article_affiliate":
            continue
        rows.append(
            {
                "source": opportunity.source,
                "external_id": opportunity.external_id,
                "slug": slugify(opportunity.external_id),
                "title": opportunity.title,
                "problem": opportunity.problem,
                "tags": opportunity.tags,
                "channel": opportunity.channel,
                "status": "review",
                "disclosure": DISCLOSURE,
                "affiliate_links": _affiliate_links(opportunity, affiliate_urls or {}, click_redirect_url),
                "outline_sections": _outline_sections(opportunity),
            }
        )
    return rows


class AffiliateArticleExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        affiliate_urls: dict[str, str] | None = None,
        click_redirect_url: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.affiliate_urls = affiliate_urls or {}
        self.click_redirect_url = click_redirect_url

    def export(self, opportunities: list[RevenueOpportunity]) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        rows = build_affiliate_article_rows(
            opportunities,
            affiliate_urls=self.affiliate_urls,
            click_redirect_url=self.click_redirect_url,
        )

        written: list[Path] = []
        json_path = self.output_dir / "affiliate_articles.json"
        json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(json_path)

        markdown_path = self.output_dir / "AFFILIATE_ARTICLES.md"
        markdown_path.write_text(_catalog_markdown(rows), encoding="utf-8")
        written.append(markdown_path)

        index_path = self.output_dir / "index.html"
        index_path.write_text(_index_page(rows), encoding="utf-8")
        written.append(index_path)

        for row in rows:
            article_dir = self.output_dir / row["slug"]
            article_dir.mkdir(parents=True, exist_ok=True)
            files = {
                "ARTICLE.md": _article_markdown(row),
                "DISCLOSURE.md": f"# Disclosure\n\n{row['disclosure']}\n",
                "index.html": _article_page(row),
            }
            for filename, body in files.items():
                path = article_dir / filename
                path.write_text(body, encoding="utf-8")
                written.append(path)
        return written


def _affiliate_links(
    opportunity: RevenueOpportunity,
    affiliate_urls: dict[str, str],
    click_redirect_url: str,
) -> list[dict]:
    links: list[dict] = []
    normalized = {key.strip().lower(): value for key, value in affiliate_urls.items() if key.strip() and value.strip()}
    for tag in opportunity.tags:
        key = tag.lower()
        if key not in normalized:
            continue
        links.append(_link_row(opportunity, key, normalized[key], click_redirect_url))
    if not links and "*" in normalized:
        links.append(_link_row(opportunity, "default", normalized["*"], click_redirect_url))
    return links


def _link_row(opportunity: RevenueOpportunity, key: str, target_url: str, click_redirect_url: str) -> dict:
    content = f"affiliate_{key}"
    if click_redirect_url:
        url = build_click_redirect_url(
            click_redirect_url,
            opportunity,
            target_url=target_url,
            content=content,
        )
    else:
        url = build_tracking_url(target_url, opportunity, content=content)
    return {"key": key, "label": key.replace("-", " ").replace("_", " ").title(), "url": url}


def _outline_sections(opportunity: RevenueOpportunity) -> list[str]:
    return [
        f"Problem summary: {opportunity.problem}",
        "Who this comparison is for and who should skip it.",
        "Decision criteria: pricing, setup time, reliability, lock-in, support, and compliance.",
        "Shortlist of tools or providers to compare. Add only sources you can verify.",
        "Hands-on notes, screenshots, command output, or pricing evidence.",
        "Recommendation matrix with no exaggerated claims.",
        "Affiliate disclosure and non-affiliate alternatives.",
        "Next step CTA for a related checklist, product, or setup service.",
    ]


def _catalog_markdown(rows: list[dict]) -> str:
    lines = ["# Affiliate Articles", ""]
    if not rows:
        lines.append("No affiliate article opportunities selected in this run.")
        return "\n".join(lines) + "\n"
    for row in rows:
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Status: {row['status']}",
                f"- Source: {row['source']}:{row['external_id']}",
                f"- Affiliate links configured: {len(row['affiliate_links'])}",
                f"- Article: {row['slug']}/ARTICLE.md",
                f"- Disclosure: {row['slug']}/DISCLOSURE.md",
                "",
            ]
        )
    return "\n".join(lines)


def _article_markdown(row: dict) -> str:
    lines = [f"# {row['title']}", "", row["disclosure"], "", "## Outline", ""]
    lines.extend(f"- {section}" for section in row["outline_sections"])
    lines.extend(["", "## Affiliate Links", ""])
    if row["affiliate_links"]:
        lines.extend(f"- [{link['label']}]({link['url']})" for link in row["affiliate_links"])
    else:
        lines.append("- Configure AFFILIATE_URLS before publishing monetized links.")
    lines.extend(
        [
            "",
            "## Review Gate",
            "",
            "Publish only after verifying claims, pricing, screenshots, and affiliate program terms.",
            "",
        ]
    )
    return "\n".join(lines)


def _index_page(rows: list[dict]) -> str:
    cards = "\n".join(_article_card(row) for row in rows) or '<p class="notice">No affiliate articles selected.</p>'
    return _page(
        "Affiliate Articles",
        f"""
        <main class="shell">
          <header class="topbar">
            <strong>Infinite Revenue Engine</strong>
            <span>affiliate articles</span>
          </header>
          <section class="hero">
            <h1>Affiliate Articles</h1>
            <p>Reviewable owned-channel article drafts with disclosure, comparison structure, and tracked affiliate links.</p>
          </section>
          <section class="grid" aria-label="Affiliate article drafts">
            {cards}
          </section>
        </main>
        """,
    )


def _article_card(row: dict) -> str:
    return f"""
    <article class="card">
      <p class="channel">{escape(row['channel'].replace("_", " "))}</p>
      <h2><a href="{escape(row['slug'])}/">{escape(row['title'])}</a></h2>
      <p>{escape(row['problem'])}</p>
      <p>{escape(row['disclosure'])}</p>
    </article>
    """


def _article_page(row: dict) -> str:
    sections = "\n".join(f"<li>{escape(section)}</li>" for section in row["outline_sections"])
    links = "\n".join(
        f'<li><a href="{escape(link["url"])}">{escape(link["label"])}</a></li>' for link in row["affiliate_links"]
    )
    if not links:
        links = "<li>Configure AFFILIATE_URLS before publishing monetized links.</li>"
    return _page(
        row["title"],
        f"""
        <main class="shell">
          <header class="topbar">
            <a href="../">Affiliate Articles</a>
            <span>manual review</span>
          </header>
          <section class="hero">
            <h1>{escape(row['title'])}</h1>
            <p>{escape(row['problem'])}</p>
            <p class="notice">{escape(row['disclosure'])}</p>
          </section>
          <section class="card">
            <h2>Article outline</h2>
            <ul>{sections}</ul>
            <h2>Tracked links</h2>
            <ul>{links}</ul>
          </section>
        </main>
        """,
    )


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
