"""Shared <head> SEO meta builder.

Emits a consistent block of meta description, canonical, Open Graph, Twitter
card, robots, and JSON-LD across every static-site exporter so all page types
ship valid, complete metadata instead of a bare <title>.
"""
from __future__ import annotations

import json
from html import escape
from typing import Any


def meta_description(text: str, *, limit: int = 155) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:")
    return f"{clipped}…"


def head_meta(
    *,
    title: str,
    description: str = "",
    canonical: str = "",
    og_type: str = "article",
    jsonld: dict[str, Any] | list[dict[str, Any]] | None = None,
    noindex: bool = False,
) -> str:
    """Return an indented block of <head> meta tags (no surrounding whitespace)."""
    desc = description or title
    lines: list[str] = [f'  <meta name="description" content="{escape(desc)}">']
    if noindex:
        lines.append('  <meta name="robots" content="noindex, follow">')
    if canonical:
        lines.append(f'  <link rel="canonical" href="{escape(canonical)}">')
        lines.append(f'  <meta property="og:url" content="{escape(canonical)}">')
    lines.append(f'  <meta property="og:type" content="{escape(og_type)}">')
    lines.append(f'  <meta property="og:title" content="{escape(title)}">')
    lines.append(f'  <meta property="og:description" content="{escape(desc)}">')
    lines.append('  <meta name="twitter:card" content="summary">')
    if jsonld is None:
        jsonld = {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc}
        if canonical:
            jsonld["url"] = canonical
    # Escape "<" so a stray "</script>" in data can't break out of the block.
    ld_json = json.dumps(jsonld, ensure_ascii=False).replace("<", "\\u003c")
    lines.append(f'  <script type="application/ld+json">{ld_json}</script>')
    return "\n".join(lines)
