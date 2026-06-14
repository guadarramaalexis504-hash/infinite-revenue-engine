"""Programmatic SEO: a static page per common cron schedule.

Each page targets a real long-tail query ("cron every 5 minutes", "github
actions every monday at 9am") with the expression, a plain-English
explanation, the next computed run times, and a copy-paste GitHub Actions
snippet — then funnels the dev reader toward the interactive tools and offers.
Hundreds of indexable pages, generated deterministically and for free.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

from .seo_head import head_meta


@dataclass(frozen=True)
class CronPreset:
    slug: str
    label: str
    expression: str
    description: str
    category: str


# ---------------------------------------------------------------------------
# Cron matching / next runs
# ---------------------------------------------------------------------------

def _parse_field(spec: str, lo: int, hi: int) -> set[int]:
    allowed: set[int] = set()
    for part in spec.split(","):
        step = 1
        rng = part
        if "/" in part:
            rng, step_s = part.split("/", 1)
            step = int(step_s)
            if step < 1:
                raise ValueError("step must be >= 1")
        if rng == "*":
            start, end = lo, hi
        elif "-" in rng:
            a, b = rng.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(rng)
        if start < lo or end > hi or start > end:
            raise ValueError("field value out of range")
        for value in range(start, end + 1, step):
            allowed.add(value)
    if not allowed:
        raise ValueError("empty field")
    return allowed


def _cron_dow(dt: datetime) -> int:
    # cron: 0=Sunday..6=Saturday; python weekday(): Monday=0..Sunday=6.
    return (dt.weekday() + 1) % 7


def next_runs(expression: str, *, count: int = 5, now: datetime | None = None) -> list[datetime]:
    now = now or datetime.now(timezone.utc)
    fields = expression.split()
    if len(fields) != 5:
        return []
    try:
        minutes = sorted(_parse_field(fields[0], 0, 59))
        hours = sorted(_parse_field(fields[1], 0, 23))
        dom = _parse_field(fields[2], 1, 31)
        month = _parse_field(fields[3], 1, 12)
        dow_raw = _parse_field(fields[4], 0, 7)
    except ValueError:
        return []
    dow = {0 if value == 7 else value for value in dow_raw}
    dom_restricted = fields[2] != "*"
    dow_restricted = fields[4] != "*"

    threshold = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day = threshold.replace(hour=0, minute=0)
    runs: list[datetime] = []
    # Iterate day by day (cheap) and only build datetimes on matching days.
    for _ in range(1200):
        if len(runs) >= count:
            break
        if day.month in month:
            dom_ok = day.day in dom
            dow_ok = _cron_dow(day) in dow
            if dom_restricted and dow_restricted:
                day_ok = dom_ok or dow_ok
            elif dom_restricted:
                day_ok = dom_ok
            elif dow_restricted:
                day_ok = dow_ok
            else:
                day_ok = True
            if day_ok:
                for hour in hours:
                    for minute in minutes:
                        candidate = day.replace(hour=hour, minute=minute)
                        if candidate >= threshold:
                            runs.append(candidate)
                            if len(runs) >= count:
                                break
                    if len(runs) >= count:
                        break
        day += timedelta(days=1)
    return runs


# ---------------------------------------------------------------------------
# Preset catalog
# ---------------------------------------------------------------------------

_DAYS = [
    ("sunday", 0),
    ("monday", 1),
    ("tuesday", 2),
    ("wednesday", 3),
    ("thursday", 4),
    ("friday", 5),
    ("saturday", 6),
]


def _time_label(hour: int, minute: int) -> tuple[str, str]:
    if hour == 0 and minute == 0:
        return "midnight", "midnight"
    if hour == 12 and minute == 0:
        return "noon", "noon"
    suffix = "am" if hour < 12 else "pm"
    h12 = hour % 12
    if h12 == 0:
        h12 = 12
    if minute == 0:
        return f"{h12}{suffix}", f"{h12}{suffix}"
    return f"{h12}-{minute:02d}{suffix}", f"{h12}:{minute:02d}{suffix}"


def build_cron_presets() -> list[CronPreset]:
    presets: list[CronPreset] = []
    seen: set[str] = set()

    def add(slug: str, label: str, expression: str, description: str, category: str) -> None:
        if slug in seen:
            return
        seen.add(slug)
        presets.append(CronPreset(slug, label, expression, description, category))

    # Every N minutes
    for n in [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 45]:
        expr = "* * * * *" if n == 1 else f"*/{n} * * * *"
        slug = "every-minute" if n == 1 else f"every-{n}-minutes"
        label = "every minute" if n == 1 else f"every {n} minutes"
        add(slug, label, expr, f"Runs {label} of every hour, all day, every day.", "minutes")

    # Every N hours
    for n in [1, 2, 3, 4, 6, 8, 12]:
        expr = "0 * * * *" if n == 1 else f"0 */{n} * * *"
        slug = "every-hour" if n == 1 else f"every-{n}-hours"
        label = "every hour" if n == 1 else f"every {n} hours"
        add(slug, label, expr, f"Runs at minute 0, {label}.", "hours")

    # Every day at HH:00 and HH:30
    for hour in range(24):
        for minute in (0, 30):
            tslug, tlabel = _time_label(hour, minute)
            add(
                f"every-day-at-{tslug}",
                f"every day at {tlabel}",
                f"{minute} {hour} * * *",
                f"Runs once a day at {tlabel} (server time, UTC on GitHub Actions).",
                "daily",
            )

    # Weekly: each day at a few common times
    for day_name, dow in _DAYS:
        for hour in (0, 8, 9, 12, 18, 21):
            tslug, tlabel = _time_label(hour, 0)
            add(
                f"every-{day_name}-at-{tslug}",
                f"every {day_name} at {tlabel}",
                f"0 {hour} * * {dow}",
                f"Runs once a week, every {day_name.title()} at {tlabel}.",
                "weekly",
            )

    # Weekdays (Mon-Fri) and weekends (Sat-Sun)
    for hour in (0, 9, 12, 18):
        tslug, tlabel = _time_label(hour, 0)
        add(
            f"every-weekday-at-{tslug}",
            f"every weekday at {tlabel}",
            f"0 {hour} * * 1-5",
            f"Runs Monday through Friday at {tlabel}.",
            "weekday",
        )
    for hour in (0, 10):
        tslug, tlabel = _time_label(hour, 0)
        add(
            f"every-weekend-day-at-{tslug}",
            f"every weekend day at {tlabel}",
            f"0 {hour} * * 6,0",
            f"Runs Saturday and Sunday at {tlabel}.",
            "weekend",
        )

    # Monthly
    for dom, dom_label in [(1, "first day"), (15, "15th"), (28, "28th")]:
        for hour in (0, 9):
            tslug, tlabel = _time_label(hour, 0)
            add(
                f"on-the-{dom}-of-every-month-at-{tslug}",
                f"on the {dom_label} of every month at {tlabel}",
                f"0 {hour} {dom} * *",
                f"Runs once a month, on the {dom_label} at {tlabel}.",
                "monthly",
            )

    return presets


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------

_CATEGORY_TITLES = {
    "minutes": "Every N minutes",
    "hours": "Every N hours",
    "daily": "Daily",
    "weekly": "Weekly",
    "weekday": "Weekdays",
    "weekend": "Weekends",
    "monthly": "Monthly",
}


class CronPagesExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        now: datetime | None = None,
        site_base_url: str = "",
        tools_path: str = "",
        offers_path: str = "",
        runs_per_page: int = 5,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.now = now or datetime.now(timezone.utc)
        self.site_base_url = site_base_url.rstrip("/")
        self.tools_path = tools_path
        self.offers_path = offers_path
        self.runs_per_page = runs_per_page

    def export(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        presets = build_cron_presets()
        written: list[str] = []

        for index, preset in enumerate(presets):
            related = [presets[(index + offset) % len(presets)] for offset in (1, 2, 3, 4)]
            page_dir = self.output_dir / preset.slug
            page_dir.mkdir(parents=True, exist_ok=True)
            page_path = page_dir / "index.html"
            page_path.write_text(self._preset_page(preset, related), encoding="utf-8")
            written.append(str(page_path))

        index_path = self.output_dir / "index.html"
        index_path.write_text(self._index_page(presets), encoding="utf-8")

        sitemap_path = self.output_dir / "sitemap.xml"
        sitemap_path.write_text(self._sitemap(presets), encoding="utf-8")

        return [str(index_path), str(sitemap_path), *written]

    def _preset_page(self, preset: CronPreset, related: list[CronPreset]) -> str:
        runs = next_runs(preset.expression, count=self.runs_per_page, now=self.now)
        runs_html = "".join(
            f"<li>{escape(r.strftime('%Y-%m-%d %H:%M'))} UTC</li>" for r in runs
        ) or "<li>No upcoming run found.</li>"
        yaml = (
            "on:\n  schedule:\n    - cron: \"" + preset.expression + "\""
        )
        crontab = f"{preset.expression} /path/to/your/command"
        related_html = "".join(
            f'<li><a href="../{escape(p.slug)}/">cron {escape(p.label)}</a></li>' for p in related
        )
        nav = self._nav(prefix="../")
        return self._page(
            f"Cron: {preset.label} — expression, schedule and next runs",
            f"""
            <main class="shell">
              <header class="topbar"><a href="../">Cron schedule reference</a>{nav}</header>
              <article class="detail">
                <p class="channel">cron schedule</p>
                <h1>Cron {escape(preset.label)}</h1>
                <p class="lead">{escape(preset.description)}</p>
                <h2>Cron expression</h2>
                <pre class="expr">{escape(preset.expression)}</pre>
                <h2>GitHub Actions</h2>
                <pre>{escape(yaml)}</pre>
                <p>GitHub Actions schedules always run in UTC and may be delayed a few minutes under load.</p>
                <h2>crontab line</h2>
                <pre>{escape(crontab)}</pre>
                <h2>Next runs (UTC)</h2>
                <ul class="runs">{runs_html}</ul>
                <p class="notice">Need to build or debug a schedule?
                  {self._tools_cta()}</p>
                <h2>Related schedules</h2>
                <ul class="related">{related_html}</ul>
              </article>
            </main>
            """,
            description=preset.description,
            canonical=self._absolute_url(f"{preset.slug}/"),
            og_type="article",
        )

    def _index_page(self, presets: list[CronPreset]) -> str:
        by_category: dict[str, list[CronPreset]] = {}
        for preset in presets:
            by_category.setdefault(preset.category, []).append(preset)
        sections = []
        for category, title in _CATEGORY_TITLES.items():
            items = by_category.get(category, [])
            if not items:
                continue
            links = "".join(
                f'<li><a href="{escape(p.slug)}/">cron {escape(p.label)}</a> <code>{escape(p.expression)}</code></li>'
                for p in items
            )
            sections.append(f"<section><h2>{escape(title)}</h2><ul class='list'>{links}</ul></section>")
        nav = self._nav(prefix="")
        return self._page(
            "Cron schedule reference — every common cron expression",
            f"""
            <main class="shell">
              <header class="topbar"><strong>Cron schedule reference</strong>{nav}</header>
              <section class="hero"><div>
                <h1>Every common cron expression</h1>
                <p>{len(presets)} ready-to-copy cron schedules with GitHub Actions snippets and the next run times for each.</p>
              </div></section>
              {''.join(sections)}
            </main>
            """,
            description=f"{len(presets)} ready-to-copy cron schedules with GitHub Actions snippets and the next run times for each.",
            canonical=self._absolute_url(""),
            og_type="website",
        )

    def _nav(self, *, prefix: str) -> str:
        links = ['<a class="nav-link" href="' + prefix + '../">Home</a>'] if prefix else []
        if self.tools_path:
            links.append(f'<a class="nav-link" href="{escape(prefix + self.tools_path.lstrip("/"))}">Tools</a>')
        if self.offers_path:
            links.append(f'<a class="nav-link" href="{escape(prefix + self.offers_path.lstrip("/"))}">Offers</a>')
        return "".join(links)

    def _tools_cta(self) -> str:
        parts = []
        if self.tools_path:
            parts.append(f'<a href="../{escape(self.tools_path.lstrip("/"))}">Try the interactive cron tools</a>')
        if self.offers_path:
            parts.append(f'<a href="../{escape(self.offers_path.lstrip("/"))}">see setup offers</a>')
        return " or ".join(parts) if parts else "Explore the rest of the site."

    def _sitemap(self, presets: list[CronPreset]) -> str:
        paths = [""] + [f"{p.slug}/" for p in presets]
        urls = "\n".join(f"  <url><loc>{escape(self._absolute_url(path))}</loc></url>" for path in paths)
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

    def _page(self, title: str, body: str, *, description: str = "", canonical: str = "", og_type: str = "article") -> str:
        head = head_meta(title=title, description=description, canonical=canonical, og_type=og_type)
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
{head}
  <style>
    :root {{ color-scheme: light; --bg:#f7f7f3; --ink:#17201b; --muted:#5c665f; --line:#d8ddd5; --surface:#fff; --accent:#116a5b; --accent-soft:#e2f3ee; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Arial,Helvetica,sans-serif; line-height:1.5; }}
    a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
    .shell {{ max-width:1000px; margin:0 auto; padding:24px 20px 56px; }}
    .topbar {{ display:flex; gap:16px; flex-wrap:wrap; padding:12px 0 24px; color:var(--muted); }}
    .nav-link {{ margin-left:auto; }}
    .hero {{ padding:40px 0 28px; border-top:1px solid var(--line); }}
    h1 {{ margin:0; font-size:clamp(1.8rem,4vw,3.2rem); line-height:1.02; }}
    .lead {{ color:var(--muted); font-size:1.05rem; max-width:720px; }}
    .detail {{ background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:26px; }}
    pre {{ background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:14px; white-space:pre-wrap; font-family:Consolas,monospace; }}
    pre.expr {{ font-size:1.3rem; font-weight:700; color:var(--accent); }}
    .channel {{ margin:0 0 8px; color:var(--accent); text-transform:uppercase; font-size:.78rem; font-weight:700; }}
    .runs, .related, .list {{ padding-left:20px; }}
    .list {{ columns:2; }} .list code {{ color:var(--muted); font-size:.82rem; }}
    .notice {{ background:var(--accent-soft); border:1px solid #b6dbd2; border-radius:8px; padding:14px 16px; }}
    section {{ margin-top:26px; }}
    @media (max-width:640px) {{ .list {{ columns:1; }} }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
