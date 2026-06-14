"""Standalone client-side web tools (the /apps/ section).

Each tool is a self-contained static page with vanilla JS that runs 100% in the
browser — no backend, no data leaves the tab (the trust hook). These target
high-intent "... online" tool queries (base64 decode online, json formatter,
sha256 generator) that reference docs don't satisfy, and funnel to the offers.

Kept deliberately separate from the opportunity-driven microtool_exporter so
adding tools here can't break that pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path


@dataclass(frozen=True)
class WebTool:
    slug: str
    title: str
    h1: str
    description: str
    body: str  # static HTML + inline <script>; inserted verbatim


# Nav entry consumed by main.py (homepage nav + sitemap).
APPS_NAV = ("Free tools", "apps/")


def _tool_ui(*, input_rows: int, controls: str, output_rows: int, script: str, output_readonly: bool = True) -> str:
    ro = " readonly" if output_readonly else ""
    return f"""
        <div class="tool">
          <label for="in">Input</label>
          <textarea id="in" rows="{input_rows}" spellcheck="false" placeholder="Paste here…"></textarea>
          <div class="row">{controls}</div>
          <label for="out">Output</label>
          <textarea id="out" rows="{output_rows}" spellcheck="false"{ro}></textarea>
          <p class="err" id="err" role="alert"></p>
          <p class="trust">🔒 Runs entirely in your browser. Nothing is uploaded.</p>
        </div>
        <script>{script}</script>
        """


def _btn(label: str, fn: str) -> str:
    return f'<button type="button" onclick="{fn}">{escape(label)}</button>'


def build_web_tools() -> list[WebTool]:
    tools: list[WebTool] = []

    tools.append(WebTool(
        slug="base64-encode-decode",
        title="Base64 Encode / Decode — online, in your browser",
        h1="Base64 Encoder & Decoder",
        description="Encode text to Base64 or decode Base64 back to text, entirely in your browser. UTF-8 safe, nothing uploaded.",
        body=_tool_ui(
            input_rows=6,
            controls=_btn("Encode", "enc()") + _btn("Decode", "dec()") + _btn("Copy", "cp()"),
            output_rows=6,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function er(m){E('err').textContent=m;}"
                "function enc(){try{E('out').value=btoa(unescape(encodeURIComponent(E('in').value)));er('');}catch(e){er('Cannot encode: '+e.message);}}"
                "function dec(){try{E('out').value=decodeURIComponent(escape(atob(E('in').value.trim())));er('');}catch(e){er('Invalid Base64 input.');}}"
                "function cp(){navigator.clipboard.writeText(E('out').value);}"
            ),
        ),
    ))

    tools.append(WebTool(
        slug="json-formatter",
        title="JSON Formatter & Validator — online, in your browser",
        h1="JSON Formatter & Validator",
        description="Pretty-print, minify, and validate JSON in your browser. Shows the exact parse error. Nothing is uploaded.",
        body=_tool_ui(
            input_rows=8,
            controls=_btn("Format", "fmt()") + _btn("Minify", "mini()") + _btn("Copy", "cp()"),
            output_rows=8,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function er(m){E('err').textContent=m;}"
                "function fmt(){try{E('out').value=JSON.stringify(JSON.parse(E('in').value),null,2);er('');}catch(e){er('Invalid JSON: '+e.message);}}"
                "function mini(){try{E('out').value=JSON.stringify(JSON.parse(E('in').value));er('');}catch(e){er('Invalid JSON: '+e.message);}}"
                "function cp(){navigator.clipboard.writeText(E('out').value);}"
            ),
        ),
    ))

    tools.append(WebTool(
        slug="url-encode-decode",
        title="URL Encode / Decode — online, in your browser",
        h1="URL Encoder & Decoder",
        description="Percent-encode or decode URL components in your browser. Handy for query strings and links. Nothing uploaded.",
        body=_tool_ui(
            input_rows=6,
            controls=_btn("Encode", "enc()") + _btn("Decode", "dec()") + _btn("Copy", "cp()"),
            output_rows=6,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function er(m){E('err').textContent=m;}"
                "function enc(){E('out').value=encodeURIComponent(E('in').value);er('');}"
                "function dec(){try{E('out').value=decodeURIComponent(E('in').value);er('');}catch(e){er('Invalid percent-encoding.');}}"
                "function cp(){navigator.clipboard.writeText(E('out').value);}"
            ),
        ),
    ))

    tools.append(WebTool(
        slug="uuid-generator",
        title="UUID Generator (v4) — online, in your browser",
        h1="UUID v4 Generator",
        description="Generate random UUID v4 identifiers in your browser with crypto.randomUUID(). Generate one or many, then copy.",
        body=_tool_ui(
            input_rows=2,
            controls=_btn("Generate 1", "gen(1)") + _btn("Generate 10", "gen(10)") + _btn("Copy", "cp()"),
            output_rows=10,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function gen(n){var a=[];for(var i=0;i<n;i++){a.push(crypto.randomUUID());}E('out').value=a.join('\\n');}"
                "function cp(){navigator.clipboard.writeText(E('out').value);}"
                "gen(1);"
            ),
        ),
    ))

    tools.append(WebTool(
        slug="sha256-hash-generator",
        title="SHA-256 Hash Generator — online, in your browser",
        h1="SHA-256 Hash Generator",
        description="Compute the SHA-256 hash of any text in your browser using the WebCrypto API. Nothing is uploaded.",
        body=_tool_ui(
            input_rows=6,
            controls=_btn("Hash (SHA-256)", "h()") + _btn("Copy", "cp()"),
            output_rows=3,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function er(m){E('err').textContent=m;}"
                "async function h(){try{var d=new TextEncoder().encode(E('in').value);var b=await crypto.subtle.digest('SHA-256',d);"
                "E('out').value=[...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('');er('');}catch(e){er('Error: '+e.message);}}"
                "function cp(){navigator.clipboard.writeText(E('out').value);}"
            ),
        ),
    ))

    tools.append(WebTool(
        slug="unix-timestamp-converter",
        title="Unix Timestamp Converter — epoch to date, in your browser",
        h1="Unix Timestamp Converter",
        description="Convert a Unix epoch timestamp (seconds or milliseconds) to a human date in UTC, or grab the current timestamp.",
        body=_tool_ui(
            input_rows=2,
            controls=_btn("To date", "toDate()") + _btn("Now", "now()") + _btn("Copy", "cp()"),
            output_rows=3,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function er(m){E('err').textContent=m;}"
                "function toDate(){var v=parseInt((E('in').value||'').trim(),10);if(isNaN(v)){er('Enter a number.');return;}"
                "var ms=v<1e12?v*1000:v;var d=new Date(ms);E('out').value=d.toISOString()+' (UTC)\\n'+d.toString();er('');}"
                "function now(){E('in').value=Math.floor(Date.now()/1000);toDate();}"
                "function cp(){navigator.clipboard.writeText(E('out').value);}"
            ),
        ),
    ))

    tools.append(WebTool(
        slug="text-case-converter",
        title="Text Case Converter — UPPER, lower, Title, in your browser",
        h1="Text Case Converter",
        description="Convert text to UPPERCASE, lowercase, Title Case, or Sentence case instantly in your browser.",
        body=_tool_ui(
            input_rows=6,
            controls=(
                _btn("UPPER", "up()") + _btn("lower", "low()") + _btn("Title", "title()") + _btn("Copy", "cp()")
            ),
            output_rows=6,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function o(v){E('out').value=v;}"
                "function up(){o(E('in').value.toUpperCase());}"
                "function low(){o(E('in').value.toLowerCase());}"
                "function title(){o(E('in').value.replace(/\\w\\S*/g,function(t){return t.charAt(0).toUpperCase()+t.substr(1).toLowerCase();}));}"
                "function cp(){navigator.clipboard.writeText(E('out').value);}"
            ),
        ),
    ))

    tools.append(WebTool(
        slug="word-character-counter",
        title="Word & Character Counter — online, in your browser",
        h1="Word & Character Counter",
        description="Count words, characters, sentences, lines, and reading time live as you type, entirely in your browser.",
        body=_tool_ui(
            input_rows=8,
            controls=_btn("Count", "count()"),
            output_rows=3,
            script=(
                "function E(i){return document.getElementById(i);}"
                "function count(){var t=E('in').value;var w=(t.match(/\\S+/g)||[]).length;"
                "var s=(t.match(/[.!?]+/g)||[]).length;var mins=Math.max(1,Math.round(w/200));"
                "E('out').value='Words: '+w+'\\nCharacters: '+t.length+'\\nSentences: '+s+'\\nLines: '+t.split('\\n').length+'\\nReading time: ~'+mins+' min';}"
                "E('in').addEventListener('input',count);"
            ),
        ),
    ))

    return tools


class WebToolsExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        site_base_url: str = "",
        offers_path: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.site_base_url = site_base_url.rstrip("/")
        self.offers_path = offers_path

    def export(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        tools = build_web_tools()
        written: list[str] = []
        for tool in tools:
            tool_dir = self.output_dir / tool.slug
            tool_dir.mkdir(parents=True, exist_ok=True)
            path = tool_dir / "index.html"
            path.write_text(self._tool_page(tool, tools), encoding="utf-8")
            written.append(str(path))
        index_path = self.output_dir / "index.html"
        index_path.write_text(self._index_page(tools), encoding="utf-8")
        sitemap_path = self.output_dir / "sitemap.xml"
        sitemap_path.write_text(self._sitemap(tools), encoding="utf-8")
        return [str(index_path), str(sitemap_path), *written]

    def _tool_page(self, tool: WebTool, all_tools: list[WebTool]) -> str:
        others = [t for t in all_tools if t.slug != tool.slug]
        related = "".join(
            f'<li><a href="../{escape(t.slug)}/">{escape(t.h1)}</a></li>' for t in others
        )
        cta = ""
        if self.offers_path:
            cta = f'<p class="notice">Need this built into your app or pipeline? <a href="../{escape(self.offers_path.lstrip("/"))}">See the setup offers</a>.</p>'
        return self._page(
            tool.title,
            f"""
            <main class="shell">
              <header class="topbar"><a href="../">Free developer tools</a><a class="nav-link" href="../../">Home</a></header>
              <article class="detail">
                <p class="channel">Free online tool</p>
                <h1>{escape(tool.h1)}</h1>
                <p class="lead">{escape(tool.description)}</p>
                {tool.body}
                {cta}
                <h2>More tools</h2>
                <ul class="related">{related}</ul>
              </article>
            </main>
            """,
            description=tool.description,
            canonical=self._absolute_url(f"{tool.slug}/"),
        )

    def _index_page(self, tools: list[WebTool]) -> str:
        cards = "".join(
            f'<li><a href="{escape(t.slug)}/">{escape(t.h1)}</a> — {escape(t.description)}</li>'
            for t in tools
        )
        return self._page(
            "Free developer tools — fast, private, in your browser",
            f"""
            <main class="shell">
              <header class="topbar"><strong>Free developer tools</strong><a class="nav-link" href="../">Home</a></header>
              <section class="hero"><div>
                <h1>Free developer tools</h1>
                <p>Fast, private, single-purpose tools that run entirely in your browser — nothing is uploaded.</p>
              </div></section>
              <section><ul class="list">{cards}</ul></section>
            </main>
            """,
            description="Free, private, single-purpose developer tools that run entirely in your browser: Base64, JSON, URL, UUID, SHA-256, timestamps, and more.",
            canonical=self._absolute_url(""),
        )

    def _sitemap(self, tools: list[WebTool]) -> str:
        paths = [""] + [f"{t.slug}/" for t in tools]
        urls = "\n".join(f"  <url><loc>{escape(self._absolute_url(p))}</loc></url>" for p in paths)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""

    def _absolute_url(self, path: str) -> str:
        normalized = path.strip().lstrip("/")
        if self.site_base_url:
            return f"{self.site_base_url}/{normalized}" if normalized else f"{self.site_base_url}/"
        return f"/{normalized}" if normalized else "/"

    def _page(self, title: str, body: str, *, description: str = "", canonical: str = "") -> str:
        desc = description or title
        canon = f'\n  <link rel="canonical" href="{escape(canonical)}">' if canonical else ""
        og = (
            '\n  <meta property="og:type" content="website">'
            f'\n  <meta property="og:title" content="{escape(title)}">'
            f'\n  <meta property="og:description" content="{escape(desc)}">'
            '\n  <meta name="twitter:card" content="summary">'
        )
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(desc)}">{canon}{og}
  <style>
    :root {{ color-scheme: light; --bg:#f7f7f3; --ink:#17201b; --muted:#5c665f; --line:#d8ddd5; --surface:#fff; --accent:#116a5b; --accent-soft:#e2f3ee; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Arial,Helvetica,sans-serif; line-height:1.5; }}
    a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
    .shell {{ max-width:900px; margin:0 auto; padding:24px 20px 56px; }}
    .topbar {{ display:flex; gap:16px; flex-wrap:wrap; padding:12px 0 24px; color:var(--muted); }}
    .nav-link {{ margin-left:auto; }}
    .hero {{ padding:36px 0 24px; border-top:1px solid var(--line); }}
    h1 {{ margin:0; font-size:clamp(1.7rem,4vw,2.8rem); line-height:1.05; }}
    .lead {{ color:var(--muted); font-size:1.05rem; max-width:720px; }}
    .detail {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:24px; }}
    .channel {{ margin:0 0 8px; color:var(--accent); text-transform:uppercase; font-size:.78rem; font-weight:700; }}
    label {{ display:block; font-weight:700; font-size:.85rem; margin:14px 0 6px; }}
    textarea {{ width:100%; border:1px solid var(--line); border-radius:8px; padding:12px; font-family:Consolas,monospace; font-size:.95rem; background:var(--bg); resize:vertical; }}
    .row {{ display:flex; gap:10px; flex-wrap:wrap; margin:12px 0; }}
    button {{ background:var(--accent); color:#fff; border:0; border-radius:6px; padding:10px 16px; cursor:pointer; font-size:.95rem; }}
    button:hover {{ opacity:.92; }}
    .err {{ color:#b00020; min-height:1.2em; margin:6px 0 0; font-size:.9rem; }}
    .trust {{ color:var(--muted); font-size:.82rem; margin:8px 0 0; }}
    .notice {{ background:var(--accent-soft); border:1px solid #b6dbd2; border-radius:8px; padding:14px 16px; margin-top:20px; }}
    .related, .list {{ padding-left:20px; }}
    h2 {{ margin-top:26px; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
