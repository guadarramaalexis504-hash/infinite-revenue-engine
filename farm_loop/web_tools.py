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

    tools.append(WebTool(
        slug="jwt-decoder",
        title="JWT Decoder — decode JSON Web Tokens in your browser",
        h1="JWT Decoder",
        description="Decode a JWT's header and payload in your browser and check its expiry. The token never leaves your tab.",
        body=_tool_ui(
            input_rows=4,
            controls=_btn("Decode", "dec()") + _btn("Copy", "cp()"),
            output_rows=12,
            script=(
                r"""function E(i){return document.getElementById(i);}function er(m){E('err').textContent=m;}
function b64u(s){s=s.replace(/-/g,'+').replace(/_/g,'/');while(s.length%4)s+='=';return decodeURIComponent(escape(atob(s)));}
function dec(){try{var p=E('in').value.trim().split('.');if(p.length<2){er('Not a JWT - expected header.payload.signature.');return;}var h=JSON.parse(b64u(p[0]));var pl=JSON.parse(b64u(p[1]));var o='HEADER:\n'+JSON.stringify(h,null,2)+'\n\nPAYLOAD:\n'+JSON.stringify(pl,null,2);if(pl.exp){o+='\n\nexp: '+new Date(pl.exp*1000).toISOString()+(Date.now()>pl.exp*1000?' (EXPIRED)':' (valid)');}E('out').value=o;er('');}catch(e){er('Invalid JWT: '+e.message);}}
function cp(){navigator.clipboard.writeText(E('out').value);}"""
            ),
        ),
    ))

    tools.append(WebTool(
        slug="html-encode-decode",
        title="HTML Encode / Decode — escape HTML entities online",
        h1="HTML Entity Encoder & Decoder",
        description="Escape text into HTML entities or decode entities back to text, entirely in your browser.",
        body=_tool_ui(
            input_rows=6,
            controls=_btn("Encode", "enc()") + _btn("Decode", "dec()") + _btn("Copy", "cp()"),
            output_rows=6,
            script=(
                r"""function E(i){return document.getElementById(i);}
function enc(){E('out').value=E('in').value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
function dec(){var t=document.createElement('textarea');t.innerHTML=E('in').value;E('out').value=t.value;}
function cp(){navigator.clipboard.writeText(E('out').value);}"""
            ),
        ),
    ))

    tools.append(WebTool(
        slug="slugify",
        title="Slug Generator — make URL-safe slugs online",
        h1="Slug Generator (Slugify)",
        description="Turn any title into a clean URL slug, stripping accents and symbols. Great for Spanish text too.",
        body=_tool_ui(
            input_rows=4,
            controls=_btn("Slugify", "slug()") + _btn("Copy", "cp()"),
            output_rows=3,
            script=(
                r"""function E(i){return document.getElementById(i);}
function slug(){E('out').value=E('in').value.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');}
function cp(){navigator.clipboard.writeText(E('out').value);}"""
            ),
        ),
    ))

    tools.append(WebTool(
        slug="sort-dedupe-lines",
        title="Sort & Dedupe Lines — online text line tool",
        h1="Sort & Deduplicate Lines",
        description="Sort lines alphabetically, remove duplicates, or reverse a list — all in your browser.",
        body=_tool_ui(
            input_rows=8,
            controls=(
                _btn("Sort A-Z", "srt()") + _btn("Dedupe", "dedupe()") + _btn("Sort + Dedupe", "both()") + _btn("Reverse", "rev()") + _btn("Copy", "cp()")
            ),
            output_rows=8,
            script=(
                r"""function E(i){return document.getElementById(i);}
function L(){return E('in').value.split('\n');}
function O(a){E('out').value=a.join('\n');}
function srt(){O(L().slice().sort());}
function dedupe(){O([...new Set(L())]);}
function both(){O([...new Set(L())].sort());}
function rev(){O(L().slice().reverse());}
function cp(){navigator.clipboard.writeText(E('out').value);}"""
            ),
        ),
    ))

    tools.append(WebTool(
        slug="password-generator",
        title="Password Generator — strong random passwords in your browser",
        h1="Password Generator",
        description="Generate strong random passwords with crypto.getRandomValues. Pick length and character sets; nothing leaves your browser.",
        body=r"""
        <div class="tool">
          <label for="len">Length</label>
          <input id="len" type="number" value="16" min="4" max="128">
          <div class="row" style="margin-top:10px">
            <label class="opt"><input type="checkbox" id="cl" checked> a-z</label>
            <label class="opt"><input type="checkbox" id="cu" checked> A-Z</label>
            <label class="opt"><input type="checkbox" id="cd" checked> 0-9</label>
            <label class="opt"><input type="checkbox" id="cs" checked> symbols</label>
          </div>
          <div class="row"><button type="button" onclick="gen()">Generate</button><button type="button" onclick="cp()">Copy</button></div>
          <label for="out">Password</label>
          <input id="out" readonly>
          <p class="trust">&#128274; Generated with crypto.getRandomValues - never leaves your browser.</p>
        </div>
        <script>
        function gen(){var s='';if(document.getElementById('cl').checked)s+='abcdefghijklmnopqrstuvwxyz';if(document.getElementById('cu').checked)s+='ABCDEFGHIJKLMNOPQRSTUVWXYZ';if(document.getElementById('cd').checked)s+='0123456789';if(document.getElementById('cs').checked)s+='!@#$%^&*()-_=+[]?';var o=document.getElementById('out');if(!s){o.value='Select at least one set';return;}var n=Math.max(4,Math.min(128,parseInt(document.getElementById('len').value)||16));var a=new Uint32Array(n);crypto.getRandomValues(a);var p='';for(var i=0;i<n;i++)p+=s[a[i]%s.length];o.value=p;}
        function cp(){navigator.clipboard.writeText(document.getElementById('out').value);}
        gen();
        </script>
        """,
    ))

    tools.append(WebTool(
        slug="color-converter",
        title="Color Converter — HEX to RGB to HSL online",
        h1="Color Converter",
        description="Convert a color between HEX, RGB, and HSL with a live picker and swatch, all in your browser.",
        body=r"""
        <div class="tool">
          <div class="row" style="align-items:center;gap:14px">
            <input type="color" id="pick" value="#116a5b" oninput="fromPick()" style="max-width:80px">
            <div style="flex:1">
              <label for="hex">HEX</label>
              <input id="hex" value="#116A5B" oninput="fromHex()" placeholder="#FF6347">
            </div>
          </div>
          <label for="rgb">RGB</label><input id="rgb" readonly>
          <label for="hsl">HSL</label><input id="hsl" readonly>
          <div class="swatch" id="sw"></div>
          <p class="err" id="err"></p>
        </div>
        <script>
        function E(i){return document.getElementById(i);}
        function fromPick(){E('hex').value=E('pick').value.toUpperCase();fromHex();}
        function fromHex(){var h=E('hex').value.trim().replace('#','');if(h.length===3)h=h[0]+h[0]+h[1]+h[1]+h[2]+h[2];if(!/^[0-9a-fA-F]{6}$/.test(h)){E('err').textContent='Enter a valid hex like #FF6347';return;}E('err').textContent='';var r=parseInt(h.slice(0,2),16),g=parseInt(h.slice(2,4),16),b=parseInt(h.slice(4,6),16);E('rgb').value='rgb('+r+', '+g+', '+b+')';E('hsl').value=toHsl(r,g,b);E('sw').style.background='#'+h;E('pick').value='#'+h.toLowerCase();}
        function toHsl(r,g,b){r/=255;g/=255;b/=255;var mx=Math.max(r,g,b),mn=Math.min(r,g,b),l=(mx+mn)/2,h,s;if(mx===mn){h=s=0;}else{var d=mx-mn;s=l>0.5?d/(2-mx-mn):d/(mx+mn);if(mx===r)h=(g-b)/d+(g<b?6:0);else if(mx===g)h=(b-r)/d+2;else h=(r-g)/d+4;h*=60;}return 'hsl('+Math.round(h)+', '+Math.round(s*100)+'%, '+Math.round(l*100)+'%)';}
        fromHex();
        </script>
        """,
    ))

    tools.append(WebTool(
        slug="number-base-converter",
        title="Number Base Converter — binary, decimal, hex, octal",
        h1="Number Base Converter",
        description="Convert numbers between binary, decimal, hexadecimal, and octal live as you type, in your browser.",
        body=r"""
        <div class="tool">
          <label for="b10">Decimal (base 10)</label><input id="b10" oninput="up(10)" placeholder="255">
          <label for="b16">Hexadecimal (base 16)</label><input id="b16" oninput="up(16)" placeholder="ff">
          <label for="b2">Binary (base 2)</label><input id="b2" oninput="up(2)" placeholder="11111111">
          <label for="b8">Octal (base 8)</label><input id="b8" oninput="up(8)" placeholder="377">
          <p class="err" id="err"></p>
        </div>
        <script>
        function E(i){return document.getElementById(i);}
        function up(base){var v=E('b'+base).value.trim();if(v===''){return;}var n=parseInt(v,base);if(isNaN(n)){E('err').textContent='Invalid base-'+base+' number';return;}E('err').textContent='';if(base!==10)E('b10').value=n.toString(10);if(base!==16)E('b16').value=n.toString(16);if(base!==2)E('b2').value=n.toString(2);if(base!==8)E('b8').value=n.toString(8);}
        </script>
        """,
    ))

    tools.append(WebTool(
        slug="lorem-ipsum-generator",
        title="Lorem Ipsum Generator — placeholder text online",
        h1="Lorem Ipsum Generator",
        description="Generate placeholder lorem ipsum paragraphs in your browser. Pick how many, then copy.",
        body=r"""
        <div class="tool">
          <label for="n">Paragraphs</label>
          <input id="n" type="number" value="3" min="1" max="50">
          <div class="row"><button type="button" onclick="gen()">Generate</button><button type="button" onclick="cp()">Copy</button></div>
          <label for="out">Output</label>
          <textarea id="out" rows="10" readonly></textarea>
        </div>
        <script>
        var W='lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute irure in reprehenderit voluptate velit esse cillum eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt culpa qui officia deserunt mollit anim id est laborum'.split(' ');
        function rnd(n){return Math.floor(Math.random()*n);}
        function sent(){var n=7+rnd(10),s=[];for(var i=0;i<n;i++)s.push(W[rnd(W.length)]);var t=s.join(' ');return t.charAt(0).toUpperCase()+t.slice(1)+'.';}
        function para(){var n=3+rnd(4),p=[];for(var i=0;i<n;i++)p.push(sent());return p.join(' ');}
        function gen(){var c=Math.max(1,Math.min(50,parseInt(document.getElementById('n').value)||3)),a=[];for(var i=0;i<c;i++)a.push(para());document.getElementById('out').value=a.join('\n\n');}
        function cp(){navigator.clipboard.writeText(document.getElementById('out').value);}
        gen();
        </script>
        """,
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
    input {{ width:100%; border:1px solid var(--line); border-radius:8px; padding:10px; font-family:Consolas,monospace; font-size:.95rem; background:var(--bg); }}
    input[type=color] {{ height:48px; padding:4px; cursor:pointer; }}
    input[type=number] {{ max-width:160px; }}
    .swatch {{ height:80px; border-radius:8px; border:1px solid var(--line); margin-top:10px; }}
    .out-box {{ background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:12px; min-height:46px; font-family:Consolas,monospace; word-break:break-word; }}
    .opt {{ display:inline-flex; align-items:center; gap:6px; margin:0 14px 8px 0; font-weight:400; }}
    .opt input {{ width:auto; }}
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
