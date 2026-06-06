from __future__ import annotations

from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .assets import AssetDraft
from .revenue_scoring import RevenueOpportunity
from .tracking import build_tracking_url


def is_supported_microtool(opportunity: RevenueOpportunity) -> bool:
    return _tool_kind(opportunity) is not None


class MicrotoolExporter:
    def __init__(self, output_dir: str | Path, *, tip_url: str = "") -> None:
        self.output_dir = Path(output_dir)
        self.tip_url = tip_url

    def export_portfolio(self, opportunities_with_assets: list[tuple[RevenueOpportunity, list[AssetDraft]]]) -> list[str]:
        supported = [(opportunity, assets) for opportunity, assets in opportunities_with_assets if is_supported_microtool(opportunity)]
        if not supported:
            return []

        self.output_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        for opportunity, _assets in supported:
            page_dir = self.output_dir / slugify(opportunity.external_id)
            page_dir.mkdir(parents=True, exist_ok=True)
            page_path = page_dir / "index.html"
            page_path.write_text(self._tool_page(opportunity), encoding="utf-8")
            written.append(str(page_path))

        index_path = self.output_dir / "index.html"
        index_path.write_text(self._index_page([item[0] for item in supported]), encoding="utf-8")
        return [str(index_path), *written]

    def _index_page(self, opportunities: list[RevenueOpportunity]) -> str:
        links = "\n".join(
            f"""
            <article class="tool-card">
              <p>{escape(opportunity.channel.replace("_", " "))}</p>
              <h2><a href="{escape(slugify(opportunity.external_id))}/">{escape(opportunity.title)}</a></h2>
              <span>{escape(opportunity.problem)}</span>
            </article>
            """
            for opportunity in opportunities
        )
        return _page(
            "Microtools",
            f"""
            <main class="shell">
              <header class="topbar">
                <strong>Microtools</strong>
                <span>Owned tools</span>
              </header>
              <section class="hero">
                <h1>Useful developer tools</h1>
                <p>Small tools generated from high-intent opportunities. Review before publishing.</p>
              </section>
              <section class="tool-grid">{links}</section>
            </main>
            """,
        )

    def _tool_page(self, opportunity: RevenueOpportunity) -> str:
        kind = _tool_kind(opportunity)
        if kind == "supabase_rls":
            tool = _supabase_rls_tool()
        elif kind == "github_actions_yaml":
            tool = _github_actions_tool()
        else:
            raise ValueError(f"Unsupported microtool: {opportunity.external_id}")

        support = self._support_cta(opportunity)
        return _page(
            opportunity.title,
            f"""
            <main class="shell">
              <header class="topbar">
                <a href="../">Microtools</a>
                <span>owned channel</span>
              </header>
              <section class="hero">
                <h1>{escape(opportunity.title)}</h1>
                <p>{escape(opportunity.problem)}</p>
              </section>
              {tool}
              {support}
            </main>
            """,
        )

    def _support_cta(self, opportunity: RevenueOpportunity) -> str:
        if not self.tip_url:
            return '<p class="notice">Configure TIP_URL before publishing a support CTA.</p>'
        url = build_tracking_url(self.tip_url, opportunity, content="microtool_support")
        return f'<p class="notice">Useful? <a href="{escape(url)}">Support this tool</a>.</p>'


def _tool_kind(opportunity: RevenueOpportunity) -> str | None:
    haystack = " ".join([opportunity.title, opportunity.external_id, *opportunity.tags]).lower()
    if "supabase" in haystack and "rls" in haystack:
        return "supabase_rls"
    if ("github-actions" in haystack or "github actions" in haystack) and "yaml" in haystack:
        return "github_actions_yaml"
    return None


def _supabase_rls_tool() -> str:
    return """
    <section class="tool">
      <label for="input">Paste Supabase SQL policies</label>
      <textarea id="input" spellcheck="false" placeholder="alter table public.profiles enable row level security;\ncreate policy ..."></textarea>
      <button type="button" onclick="analyzeRls()">Analyze RLS</button>
      <div id="results" class="results" aria-live="polite"></div>
    </section>
    <script>
      function addResult(items, ok, text) {
        items.push('<li class="' + (ok ? 'ok' : 'warn') + '">' + text + '</li>');
      }
      function analyzeRls() {
        const sql = document.getElementById('input').value.toLowerCase();
        const items = [];
        addResult(items, /enable\\s+row\\s+level\\s+security/.test(sql), 'Checks for enable row level security statements.');
        addResult(items, /create\\s+policy/.test(sql), 'Checks for create policy statements.');
        addResult(items, /authenticated|auth\\.uid\\s*\\(/.test(sql), 'Looks for authenticated user constraints.');
        addResult(items, !/using\\s*\\(\\s*true\\s*\\)/.test(sql), 'Flags broad using (true) policies for manual review.');
        addResult(items, !/anon/.test(sql), 'Flags anon access mentions for manual review.');
        document.getElementById('results').innerHTML = '<ul>' + items.join('') + '</ul>';
      }
    </script>
    """


def _github_actions_tool() -> str:
    return """
    <section class="tool">
      <label for="input">Paste GitHub Actions YAML</label>
      <textarea id="input" spellcheck="false" placeholder="name: CI\non: [push]\njobs:\n  test:"></textarea>
      <button type="button" onclick="analyzeActions()">Analyze workflow</button>
      <div id="results" class="results" aria-live="polite"></div>
    </section>
    <script>
      function addResult(items, ok, text) {
        items.push('<li class="' + (ok ? 'ok' : 'warn') + '">' + text + '</li>');
      }
      function analyzeActions() {
        const yaml = document.getElementById('input').value;
        const lower = yaml.toLowerCase();
        const items = [];
        addResult(items, /^on\\s*:/m.test(yaml), 'Checks for an on: trigger.');
        addResult(items, /^jobs\\s*:/m.test(yaml), 'Checks for a jobs: block.');
        addResult(items, !/\\t/.test(yaml), 'Flags tabs because YAML indentation should use spaces.');
        addResult(items, !/pull_request_target/.test(lower), 'Flags pull_request_target for security review.');
        addResult(items, !/permissions\\s*:\\s*write-all/.test(lower), 'Flags permissions: write-all.');
        addResult(items, !/echo\\s+.*\\$\\{\\{\\s*secrets\\./.test(lower), 'Flags possible secret echo statements.');
        document.getElementById('results').innerHTML = '<ul>' + items.join('') + '</ul>';
      }
    </script>
    """


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
      --bg: #f6f7f2;
      --ink: #151916;
      --muted: #5c655f;
      --line: #d9ded6;
      --surface: #ffffff;
      --accent: #0c6b5d;
      --warn: #8a4a0a;
      --ok: #0b6847;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .shell {{ max-width: 1080px; margin: 0 auto; padding: 28px 20px 56px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; padding: 12px 0 28px; color: var(--muted); }}
    .hero {{ padding: 44px 0 28px; border-top: 1px solid var(--line); }}
    h1 {{ max-width: 860px; margin: 0; font-size: clamp(2rem, 5vw, 4.2rem); line-height: 1; letter-spacing: 0; }}
    .hero p {{ max-width: 760px; color: var(--muted); font-size: 1.05rem; }}
    .tool, .tool-card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .tool-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .tool-card h2 {{ margin: 6px 0; font-size: 1.2rem; }}
    .tool-card p {{ margin: 0; color: var(--accent); text-transform: uppercase; font-size: 0.76rem; font-weight: 700; }}
    .tool-card span {{ color: var(--muted); }}
    label {{ display: block; margin-bottom: 10px; font-weight: 700; }}
    textarea {{
      width: 100%;
      min-height: 360px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      font-family: Consolas, monospace;
      font-size: 0.95rem;
    }}
    button {{
      margin-top: 12px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      padding: 11px 16px;
      font-weight: 700;
      cursor: pointer;
    }}
    .results ul {{ padding-left: 22px; }}
    .ok {{ color: var(--ok); }}
    .warn {{ color: var(--warn); }}
    .notice {{ margin-top: 16px; background: #e3f2ee; border: 1px solid #b8d9d0; border-radius: 8px; padding: 14px 16px; }}
    @media (max-width: 640px) {{
      .topbar {{ display: grid; }}
      textarea {{ min-height: 300px; }}
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
