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
        builders = {
            "supabase_rls": _supabase_rls_tool,
            "github_actions_yaml": _github_actions_tool,
            "cron_explainer": _cron_explainer_tool,
            "env_auditor": _env_auditor_tool,
            "docker_compose_checker": _docker_compose_tool,
            "openai_cost_calculator": _openai_cost_tool,
            "webhook_signature_tester": _webhook_signature_tool,
            "regex_tester": _regex_tester_tool,
            "llmstxt_generator": _llmstxt_generator_tool,
            "ai_robots_generator": _ai_robots_tool,
        }
        if kind not in builders:
            raise ValueError(f"Unsupported microtool: {opportunity.external_id}")
        tool = builders[kind]()

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
    if "docker" in haystack and ("compose" in haystack or "env" in haystack):
        return "docker_compose_checker"
    if "cron" in haystack and ("explain" in haystack or "expression" in haystack):
        return "cron_explainer"
    if "env" in haystack and ("audit" in haystack or "variable" in haystack):
        return "env_auditor"
    if "openai" in haystack and ("cost" in haystack or "calculator" in haystack):
        return "openai_cost_calculator"
    if "webhook" in haystack and ("signature" in haystack or "verifier" in haystack or "tester" in haystack):
        return "webhook_signature_tester"
    if "regex" in haystack:
        return "regex_tester"
    if "llms" in haystack:
        return "llmstxt_generator"
    if "robots" in haystack and ("ai" in haystack or "crawler" in haystack):
        return "ai_robots_generator"
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


def _cron_explainer_tool() -> str:
    return r"""
    <section class="tool">
      <label for="input">Cron expression (5 fields: minute hour day-of-month month day-of-week)</label>
      <textarea id="input" spellcheck="false" style="min-height:64px" placeholder="*/5 * * * *"></textarea>
      <button type="button" onclick="explainCron()">Explain cron</button>
      <div id="results" class="results" aria-live="polite"></div>
    </section>
    <script>
      var FIELDS = [
        {name: 'minute', min: 0, max: 59},
        {name: 'hour', min: 0, max: 23},
        {name: 'day of month', min: 1, max: 31},
        {name: 'month', min: 1, max: 12},
        {name: 'day of week', min: 0, max: 6}
      ];
      function parseField(spec, min, max) {
        var allowed = new Set();
        var parts = spec.split(',');
        for (var p = 0; p < parts.length; p++) {
          var part = parts[p];
          var step = 1;
          var stepSplit = part.split('/');
          if (stepSplit.length === 2) { part = stepSplit[0]; step = parseInt(stepSplit[1], 10); }
          if (!step || step < 1) return null;
          var lo = min, hi = max;
          if (part !== '*') {
            var range = part.split('-');
            lo = parseInt(range[0], 10);
            hi = range.length === 2 ? parseInt(range[1], 10) : (stepSplit.length === 2 ? max : lo);
            if (isNaN(lo) || isNaN(hi) || lo < min || hi > max + (min === 0 && max === 6 ? 1 : 0) || lo > hi) return null;
          }
          for (var v = lo; v <= hi; v += step) allowed.add(v === 7 && max === 6 ? 0 : v);
        }
        return allowed;
      }
      function describeField(spec, field) {
        if (spec === '*') return 'every ' + field.name;
        if (/^\*\/\d+$/.test(spec)) return 'every ' + spec.split('/')[1] + ' ' + field.name + '(s)';
        return field.name + ' ' + spec;
      }
      function explainCron() {
        var raw = document.getElementById('input').value.trim().replace(/\s+/g, ' ');
        var out = document.getElementById('results');
        var fields = raw.split(' ');
        if (fields.length !== 5) {
          out.innerHTML = '<ul><li class="warn">Expected 5 fields, got ' + fields.length + '. GitHub Actions and crontab use: minute hour day-of-month month day-of-week.</li></ul>';
          return;
        }
        var sets = [], descriptions = [];
        for (var i = 0; i < 5; i++) {
          var set = parseField(fields[i], FIELDS[i].min, FIELDS[i].max);
          if (!set || set.size === 0) {
            out.innerHTML = '<ul><li class="warn">Could not parse field ' + (i + 1) + ' ("' + fields[i] + '") as ' + FIELDS[i].name + ' (' + FIELDS[i].min + '-' + FIELDS[i].max + ').</li></ul>';
            return;
          }
          sets.push(set);
          descriptions.push('<li class="ok"><strong>' + fields[i] + '</strong> &rarr; ' + describeField(fields[i], FIELDS[i]) + '</li>');
        }
        var domRestricted = fields[2] !== '*', dowRestricted = fields[4] !== '*';
        var runs = [];
        var cursor = new Date();
        cursor.setUTCSeconds(0, 0);
        cursor = new Date(cursor.getTime() + 60000);
        for (var step = 0; step < 1051200 && runs.length < 5; step++) {
          var ok = sets[0].has(cursor.getUTCMinutes()) && sets[1].has(cursor.getUTCHours()) && sets[3].has(cursor.getUTCMonth() + 1);
          if (ok) {
            var domOk = sets[2].has(cursor.getUTCDate());
            var dowOk = sets[4].has(cursor.getUTCDay());
            ok = (domRestricted && dowRestricted) ? (domOk || dowOk) : (domOk && dowOk);
          }
          if (ok) runs.push(cursor.toISOString().slice(0, 16).replace('T', ' ') + ' UTC');
          cursor = new Date(cursor.getTime() + 60000);
        }
        var note = (domRestricted && dowRestricted) ? '<li class="warn">Both day-of-month and day-of-week are restricted: standard cron runs when EITHER matches.</li>' : '';
        out.innerHTML = '<h3>Meaning</h3><ul>' + descriptions.join('') + note + '</ul>' +
          '<h3>Next runs (UTC)</h3><ul>' + (runs.length ? runs.map(function (r) { return '<li class="ok">' + r + '</li>'; }).join('') : '<li class="warn">No run found in the next 2 years.</li>') + '</ul>' +
          '<p>GitHub Actions schedules always run in UTC and may be delayed a few minutes under load.</p>';
      }
    </script>
    """


def _env_auditor_tool() -> str:
    return r"""
    <section class="tool">
      <label for="input">Paste your .env file (it never leaves your browser - this page makes zero network calls)</label>
      <textarea id="input" spellcheck="false" placeholder="DATABASE_URL=postgres://...&#10;API_KEY=sk-your-key"></textarea>
      <button type="button" onclick="auditEnv()">Audit env file</button>
      <div id="results" class="results" aria-live="polite"></div>
    </section>
    <script>
      function auditEnv() {
        var raw = document.getElementById('input').value;
        var items = [];
        if (raw.charCodeAt(0) === 0xFEFF) items.push('<li class="warn">File starts with a BOM (\\ufeff). Many parsers and CLIs choke on it - save as UTF-8 without BOM or plain ASCII.</li>');
        if (raw.indexOf('\r\n') !== -1 && raw.replace(/\r\n/g, '').indexOf('\r') !== -1) items.push('<li class="warn">Mixed line endings (CRLF and CR). Normalize to one style.</li>');
        var lines = raw.split(/\r\n|\r|\n/);
        var seen = {}, count = 0;
        var placeholderRe = /(your[-_]|example|changeme|change[-_]me|xxx|todo|placeholder|<.+>)/i;
        var secretRes = [
          [/^sk-[A-Za-z0-9_-]{20,}/, 'OpenAI-style key'],
          [/^(ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}/, 'GitHub token'],
          [/^github_pat_/, 'GitHub fine-grained token'],
          [/^AKIA[0-9A-Z]{16}/, 'AWS access key'],
          [/^eyJ[A-Za-z0-9_-]+\./, 'JWT (possibly a Supabase service key)'],
          [/^sb_secret_/, 'Supabase secret key'],
          [/^xox[baprs]-/, 'Slack token']
        ];
        for (var i = 0; i < lines.length; i++) {
          var line = lines[i];
          var trimmed = line.trim();
          if (!trimmed || trimmed.charAt(0) === '#') continue;
          var eq = trimmed.indexOf('=');
          var where = ' (line ' + (i + 1) + ')';
          if (eq === -1) { items.push('<li class="warn">No "=" found' + where + ': <code>' + trimmed.slice(0, 40) + '</code></li>'); continue; }
          count++;
          var key = trimmed.slice(0, eq);
          var value = trimmed.slice(eq + 1);
          if (key !== key.trim() || value !== value.replace(/^\s+/, '')) items.push('<li class="warn">Whitespace around "=" breaks some parsers (docker compose, systemd)' + where + '.</li>');
          key = key.trim();
          if (seen[key] !== undefined) items.push('<li class="warn">Duplicate key <code>' + key + '</code>' + where + ' - last one usually wins, first one silently ignored.</li>');
          seen[key] = i;
          if (key !== key.toUpperCase()) items.push('<li class="warn">Key <code>' + key + '</code> is not UPPER_CASE' + where + ' - convention is uppercase with underscores.</li>');
          var v = value.trim().replace(/^["']|["']$/g, '');
          if (v === '') items.push('<li class="warn">Empty value for <code>' + key + '</code>' + where + '.</li>');
          else if (placeholderRe.test(v)) items.push('<li class="warn">Placeholder-looking value for <code>' + key + '</code>' + where + ' - did you forget the real one?</li>');
          else {
            for (var s = 0; s < secretRes.length; s++) {
              if (secretRes[s][0].test(v)) { items.push('<li class="warn">Real-looking ' + secretRes[s][1] + ' in <code>' + key + '</code>' + where + ' - make sure this file is gitignored and never pasted in chats or logs.</li>'); break; }
            }
          }
          if (/\s/.test(v) && !/^["']/.test(value.trim())) items.push('<li class="warn">Unquoted value with spaces for <code>' + key + '</code>' + where + ' - quote it.</li>');
        }
        if (!items.length) items.push('<li class="ok">No issues found across ' + count + ' variables. Clean file.</li>');
        else items.unshift('<li class="ok">Scanned ' + count + ' variables.</li>');
        document.getElementById('results').innerHTML = '<ul>' + items.join('') + '</ul>';
      }
    </script>
    """


def _docker_compose_tool() -> str:
    return r"""
    <section class="tool">
      <label for="input">Paste your docker-compose.yml (analyzed locally, never uploaded)</label>
      <textarea id="input" spellcheck="false" placeholder="services:&#10;  app:&#10;    image: node:20&#10;    env_file: .env"></textarea>
      <button type="button" onclick="checkCompose()">Check compose file</button>
      <div id="results" class="results" aria-live="polite"></div>
    </section>
    <script>
      function addResult(items, ok, text) {
        items.push('<li class="' + (ok ? 'ok' : 'warn') + '">' + text + '</li>');
      }
      function checkCompose() {
        var text = document.getElementById('input').value;
        var items = [];
        addResult(items, !/\t/.test(text), 'YAML indentation must use spaces - tabs found: ' + (/\t/.test(text) ? 'yes, fix them' : 'none') + '.');
        if (/^version\s*:/m.test(text)) addResult(items, false, 'Top-level "version:" is obsolete in Compose v2+ - safe to remove.');
        var unset = text.match(/\$\{[A-Z0-9_]+\}/g) || [];
        var withDefault = text.match(/\$\{[A-Z0-9_]+:-[^}]*\}/g) || [];
        addResult(items, unset.length === 0, unset.length + ' interpolated variable(s) like ${VAR} without a :-default - compose warns and substitutes empty string if unset. ' + (withDefault.length ? withDefault.length + ' already have defaults.' : ''));
        var envFiles = text.match(/env_file\s*:\s*\S+|env_file\s*:\s*\n(\s*-\s*\S+\n?)+/g) || [];
        addResult(items, true, envFiles.length ? ('References env_file ' + envFiles.length + ' time(s) - make sure those files exist and are gitignored.') : 'No env_file references - inline environment blocks only.');
        addResult(items, !/image\s*:\s*[^\s:]+\s*$/m.test(text), 'Images without an explicit tag default to :latest - pin versions for reproducible builds.');
        addResult(items, !/:latest\b/.test(text), ':latest tag found - pin a version to avoid surprise upgrades.');
        var plainSecrets = text.match(/^\s*-?\s*[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|API_KEY|PRIVATE_KEY)[A-Z0-9_]*\s*[:=]\s*\S+/gm) || [];
        addResult(items, plainSecrets.length === 0, plainSecrets.length ? (plainSecrets.length + ' hardcoded secret-looking value(s) in environment - move them to an env_file or docker secrets.') : 'No hardcoded secret-looking values in environment blocks.');
        addResult(items, /restart\s*:/.test(text), '"restart:" policy ' + (/restart\s*:/.test(text) ? 'present.' : 'missing - add restart: unless-stopped for long-running services.'));
        var ports = text.match(/^\s*-\s*\d+:\d+\s*$/gm) || [];
        if (ports.length) addResult(items, false, ports.length + ' unquoted port mapping(s) like 8080:80 - YAML can parse times like 22:22 as sexagesimal. Quote them: "8080:80".');
        document.getElementById('results').innerHTML = '<ul>' + items.join('') + '</ul>';
      }
    </script>
    """


def _openai_cost_tool() -> str:
    return r"""
    <section class="tool">
      <style>
        .calc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
        .calc-grid label { font-weight: 700; font-size: 0.9rem; }
        .calc-grid input, .calc-grid select { width: 100%; padding: 10px; border: 1px solid var(--line); border-radius: 8px; font-size: 0.95rem; }
        .cost-big { font-size: 1.6rem; font-weight: 700; color: var(--accent); }
      </style>
      <div class="calc-grid">
        <div><label for="preset">Preset (then verify current pricing)</label>
          <select id="preset" onchange="applyPreset()">
            <option value="0.15,0.60">gpt-4o-mini (example rates)</option>
            <option value="2.50,10.00">gpt-4o (example rates)</option>
            <option value="1.10,4.40">o3-mini (example rates)</option>
            <option value="custom" selected>Custom - enter your own</option>
          </select></div>
        <div><label for="pin">Input price ($ per 1M tokens)</label><input id="pin" type="number" step="0.01" value="0.15"></div>
        <div><label for="pout">Output price ($ per 1M tokens)</label><input id="pout" type="number" step="0.01" value="0.60"></div>
        <div><label for="tin">Input tokens per request</label><input id="tin" type="number" value="1500"></div>
        <div><label for="tout">Output tokens per request</label><input id="tout" type="number" value="500"></div>
        <div><label for="reqs">Requests per day</label><input id="reqs" type="number" value="1000"></div>
      </div>
      <button type="button" onclick="calculateCost()">Calculate cost</button>
      <div id="results" class="results" aria-live="polite"></div>
      <p>Prices change often - always verify current pricing on the provider's pricing page before budgeting. All math runs in your browser.</p>
    </section>
    <script>
      function applyPreset() {
        var v = document.getElementById('preset').value;
        if (v === 'custom') return;
        var parts = v.split(',');
        document.getElementById('pin').value = parts[0];
        document.getElementById('pout').value = parts[1];
        calculateCost();
      }
      function num(id) { return parseFloat(document.getElementById(id).value) || 0; }
      function fmt(x) { return x >= 100 ? x.toFixed(0) : x >= 1 ? x.toFixed(2) : x.toFixed(4); }
      function calculateCost() {
        var perRequest = (num('tin') / 1e6) * num('pin') + (num('tout') / 1e6) * num('pout');
        var daily = perRequest * num('reqs');
        document.getElementById('results').innerHTML =
          '<ul>' +
          '<li class="ok">Per request: <strong>$' + fmt(perRequest) + '</strong></li>' +
          '<li class="ok">Per day: <strong>$' + fmt(daily) + '</strong></li>' +
          '<li class="ok">Per month (30d): <span class="cost-big">$' + fmt(daily * 30) + '</span></li>' +
          '<li class="ok">Per year: <strong>$' + fmt(daily * 365) + '</strong></li>' +
          '</ul>';
      }
    </script>
    """


def _webhook_signature_tool() -> str:
    return r"""
    <section class="tool">
      <style>
        .sig-grid label { display: block; font-weight: 700; margin: 12px 0 6px; }
        .sig-grid input, .sig-grid select { width: 100%; padding: 10px; border: 1px solid var(--line); border-radius: 8px; font-family: Consolas, monospace; }
      </style>
      <div class="sig-grid">
        <label for="mode">Mode</label>
        <select id="mode">
          <option value="raw">Plain HMAC-SHA256 of body</option>
          <option value="stripe">Stripe style: HMAC-SHA256 of "timestamp.body"</option>
        </select>
        <label for="secret">Webhook secret (never leaves your browser - computed locally with WebCrypto)</label>
        <input id="secret" type="password" autocomplete="off" placeholder="whsec_...">
        <label for="ts">Timestamp (Stripe mode only)</label>
        <input id="ts" placeholder="1718000000">
        <label for="payload">Raw request body</label>
        <textarea id="payload" spellcheck="false" style="min-height:160px" placeholder='{"id":"evt_123","type":"checkout.session.completed"}'></textarea>
        <label for="expected">Expected signature (optional - paste to compare)</label>
        <input id="expected" autocomplete="off" placeholder="hex signature or v1=...">
      </div>
      <button type="button" onclick="computeSignature()">Compute HMAC signature</button>
      <div id="results" class="results" aria-live="polite"></div>
    </section>
    <script>
      async function computeSignature() {
        var out = document.getElementById('results');
        var secret = document.getElementById('secret').value;
        var payload = document.getElementById('payload').value;
        if (!secret || !payload) { out.innerHTML = '<ul><li class="warn">Secret and body are both required.</li></ul>'; return; }
        var mode = document.getElementById('mode').value;
        var message = payload;
        if (mode === 'stripe') {
          var ts = document.getElementById('ts').value.trim();
          if (!ts) { out.innerHTML = '<ul><li class="warn">Stripe mode needs the timestamp from the Stripe-Signature header (t=...).</li></ul>'; return; }
          message = ts + '.' + payload;
        }
        var enc = new TextEncoder();
        var key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
        var sigBuf = await crypto.subtle.sign('HMAC', key, enc.encode(message));
        var hex = Array.from(new Uint8Array(sigBuf)).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
        var items = ['<li class="ok">Computed HMAC-SHA256: <code style="word-break:break-all">' + hex + '</code></li>'];
        var expected = document.getElementById('expected').value.trim().replace(/^v1=/, '');
        if (expected) {
          var match = expected.toLowerCase() === hex;
          items.push('<li class="' + (match ? 'ok' : 'warn') + '">' + (match ? 'MATCH - the signature is valid for this secret and body.' : 'NO MATCH - check the exact raw body (whitespace matters), the secret, and the timestamp.') + '</li>');
        }
        out.innerHTML = '<ul>' + items.join('') + '</ul>';
      }
    </script>
    """


def _regex_tester_tool() -> str:
    return r"""
    <section class="tool">
      <style>
        .rx-grid label { display: block; font-weight: 700; margin: 12px 0 6px; }
        .rx-grid input { width: 100%; padding: 10px; border: 1px solid var(--line); border-radius: 8px; font-family: Consolas, monospace; }
        mark { background: #ffe9a8; padding: 0 1px; border-radius: 3px; }
      </style>
      <div class="rx-grid">
        <label for="pattern">Regex pattern (without slashes)</label>
        <input id="pattern" spellcheck="false" placeholder="\b[a-z]+@[a-z]+\.[a-z]{2,}\b">
        <label for="flags">Flags</label>
        <input id="flags" value="g" placeholder="gim">
        <label for="text">Test text</label>
        <textarea id="text" spellcheck="false" style="min-height:160px" placeholder="Paste sample text here"></textarea>
      </div>
      <button type="button" onclick="testRegex()">Test regex</button>
      <div id="results" class="results" aria-live="polite"></div>
    </section>
    <script>
      var TOKEN_NOTES = [
        ['\\d', 'digit 0-9'], ['\\w', 'word character (letter, digit, underscore)'], ['\\s', 'whitespace'],
        ['\\b', 'word boundary'], ['^', 'start of string (or line with m flag)'], ['$', 'end of string (or line with m flag)'],
        ['+', 'one or more of the previous token'], ['*', 'zero or more'], ['?', 'optional / lazy modifier'],
        ['(?:', 'non-capturing group'], ['(?=', 'lookahead'], ['(?<=', 'lookbehind'], ['[', 'character class'], ['|', 'alternation (OR)'],
        ['{', 'repetition count {n} or {n,m}']
      ];
      function escapeHtml(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
      function testRegex() {
        var out = document.getElementById('results');
        var pattern = document.getElementById('pattern').value;
        var flags = document.getElementById('flags').value;
        var text = document.getElementById('text').value;
        if (!pattern) { out.innerHTML = '<ul><li class="warn">Enter a pattern first.</li></ul>'; return; }
        var re;
        try { re = new RegExp(pattern, flags.indexOf('g') === -1 ? flags + 'g' : flags); }
        catch (e) { out.innerHTML = '<ul><li class="warn">Invalid regex: ' + escapeHtml(String(e.message)) + '</li></ul>'; return; }
        var items = [], highlighted = '', last = 0, m, count = 0;
        while ((m = re.exec(text)) !== null && count < 500) {
          count++;
          highlighted += escapeHtml(text.slice(last, m.index)) + '<mark>' + escapeHtml(m[0] === '' ? '(empty)' : m[0]) + '</mark>';
          last = m.index + m[0].length;
          var groups = m.slice(1).filter(function (g) { return g !== undefined; });
          items.push('<li class="ok">Match ' + count + ' at index ' + m.index + ': <code>' + escapeHtml(m[0]) + '</code>' + (groups.length ? ' - groups: ' + groups.map(function (g) { return '<code>' + escapeHtml(g) + '</code>'; }).join(', ') : '') + '</li>');
          if (m[0] === '') re.lastIndex++;
        }
        highlighted += escapeHtml(text.slice(last));
        var notes = TOKEN_NOTES.filter(function (t) { return pattern.indexOf(t[0]) !== -1; })
          .map(function (t) { return '<li class="ok"><code>' + escapeHtml(t[0]) + '</code> - ' + t[1] + '</li>'; });
        out.innerHTML = '<h3>' + count + ' matches</h3>' +
          (count ? '<p style="white-space:pre-wrap;font-family:Consolas,monospace;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px">' + highlighted + '</p>' : '') +
          '<ul>' + items.join('') + '</ul>' +
          (notes.length ? '<h3>Pattern breakdown</h3><ul>' + notes.join('') + '</ul>' : '');
      }
    </script>
    """


def _llmstxt_generator_tool() -> str:
    return r"""
    <section class="tool">
      <style>
        .llms-grid label { display: block; font-weight: 700; margin: 12px 0 6px; }
        .llms-grid input { width: 100%; padding: 10px; border: 1px solid var(--line); border-radius: 8px; }
        .llms-grid textarea { min-height: 110px; }
        pre.out { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 14px; white-space: pre-wrap; font-family: Consolas, monospace; }
      </style>
      <div class="llms-grid">
        <label for="site">Site name</label>
        <input id="site" placeholder="My Project">
        <label for="desc">One-line description (what should AI assistants know?)</label>
        <input id="desc" placeholder="Free developer tools for Supabase, GitHub Actions and automation.">
        <label for="docs">Key pages - one per line: Title | https://url | optional note</label>
        <textarea id="docs" spellcheck="false" placeholder="Getting started | https://example.com/start | setup guide&#10;Pricing | https://example.com/pricing"></textarea>
        <label for="optional">Secondary pages (same format, listed under Optional)</label>
        <textarea id="optional" spellcheck="false" placeholder="Changelog | https://example.com/changelog"></textarea>
      </div>
      <button type="button" onclick="generateLlms()">Generate llms.txt</button>
      <div id="results" class="results" aria-live="polite"></div>
      <p>llms.txt is a proposed standard: a markdown file at /llms.txt that tells AI assistants what your site is about and which pages matter. Everything runs in your browser.</p>
    </section>
    <script>
      function parseLines(id) {
        return document.getElementById(id).value.split('\n').map(function (l) { return l.trim(); }).filter(Boolean).map(function (l) {
          var parts = l.split('|').map(function (p) { return p.trim(); });
          return { title: parts[0] || 'Page', url: parts[1] || '', note: parts[2] || '' };
        });
      }
      function section(name, rows) {
        if (!rows.length) return '';
        return '\n## ' + name + '\n\n' + rows.map(function (r) {
          return '- [' + r.title + '](' + r.url + ')' + (r.note ? ': ' + r.note : '');
        }).join('\n') + '\n';
      }
      function generateLlms() {
        var site = document.getElementById('site').value.trim() || 'My Site';
        var desc = document.getElementById('desc').value.trim();
        var out = '# ' + site + '\n' + (desc ? '\n> ' + desc + '\n' : '') +
          section('Docs', parseLines('docs')) + section('Optional', parseLines('optional'));
        document.getElementById('results').innerHTML =
          '<p class="ok">Save this as <code>llms.txt</code> at the root of your site (https://yoursite.com/llms.txt):</p>' +
          '<pre class="out" id="llmsout"></pre><button type="button" onclick="copyLlms()">Copy to clipboard</button>';
        document.getElementById('llmsout').textContent = out;
      }
      function copyLlms() { navigator.clipboard.writeText(document.getElementById('llmsout').textContent); }
    </script>
    """


def _ai_robots_tool() -> str:
    return r"""
    <section class="tool">
      <style>
        .bots { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 8px; margin-bottom: 12px; }
        .bots label { display: flex; gap: 8px; align-items: center; font-weight: 400; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; }
        pre.out { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 14px; white-space: pre-wrap; font-family: Consolas, monospace; }
      </style>
      <p>Tick the AI crawlers you want to <strong>block</strong> in robots.txt. Unticked bots stay allowed.</p>
      <div class="bots" id="bots"></div>
      <button type="button" onclick="generateRobots()">Generate robots.txt rules</button>
      <button type="button" onclick="toggleAll()" style="background:var(--muted)">Toggle all</button>
      <div id="results" class="results" aria-live="polite"></div>
      <p>Blocking a bot here only affects crawlers that respect robots.txt. Training-data opt-out and search visibility are different trade-offs: blocking GPTBot or ClaudeBot also removes you from some AI answers. Runs fully in your browser.</p>
    </section>
    <script>
      var BOTS = [
        ['GPTBot', 'OpenAI - model training'],
        ['ChatGPT-User', 'OpenAI - live browsing for users'],
        ['OAI-SearchBot', 'OpenAI - search index'],
        ['ClaudeBot', 'Anthropic - crawling'],
        ['anthropic-ai', 'Anthropic - training (legacy token)'],
        ['Claude-Web', 'Anthropic - live browsing (legacy token)'],
        ['PerplexityBot', 'Perplexity - search index'],
        ['Perplexity-User', 'Perplexity - live browsing'],
        ['CCBot', 'Common Crawl - open dataset used for training'],
        ['Google-Extended', 'Google - Gemini training opt-out token'],
        ['Applebot-Extended', 'Apple - AI training opt-out token'],
        ['Bytespider', 'ByteDance - crawling'],
        ['Amazonbot', 'Amazon - Alexa and AI'],
        ['Meta-ExternalAgent', 'Meta - AI crawling']
      ];
      var grid = document.getElementById('bots');
      BOTS.forEach(function (b, i) {
        var l = document.createElement('label');
        l.innerHTML = '<input type="checkbox" id="bot' + i + '"> <span><strong>' + b[0] + '</strong><br><small>' + b[1] + '</small></span>';
        grid.appendChild(l);
      });
      function toggleAll() {
        var first = document.getElementById('bot0').checked;
        BOTS.forEach(function (_, i) { document.getElementById('bot' + i).checked = !first; });
      }
      function generateRobots() {
        var blocks = [];
        BOTS.forEach(function (b, i) {
          if (document.getElementById('bot' + i).checked) blocks.push('User-agent: ' + b[0] + '\nDisallow: /');
        });
        var out = blocks.length ? blocks.join('\n\n') + '\n' : '# No AI crawlers blocked - all allowed.\n';
        document.getElementById('results').innerHTML =
          '<p class="ok">' + (blocks.length ? blocks.length + ' crawler(s) blocked. Append this to your robots.txt:' : 'Nothing blocked yet - tick some bots above.') + '</p>' +
          '<pre class="out" id="robotsout"></pre>' + (blocks.length ? '<button type="button" onclick="copyRobots()">Copy to clipboard</button>' : '');
        document.getElementById('robotsout').textContent = out;
      }
      function copyRobots() { navigator.clipboard.writeText(document.getElementById('robotsout').textContent); }
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
