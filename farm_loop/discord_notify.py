"""Post Revenue Engine activity to a Discord channel via an incoming webhook.

No bot, no login, no gateway: a webhook URL is the only credential. The engine
POSTs a JSON body and Discord renders it in the channel. Safe by design — the
notifier never includes secrets, and it degrades to a no-op when the webhook
URL is missing or still a placeholder.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Callable

DISCORD_CONTENT_LIMIT = 2000

# Opener signature mirrors urllib.request.urlopen(req, timeout=...).
Opener = Callable[[urllib.request.Request, float], object]


def _looks_real(url: str | None) -> bool:
    if not url:
        return False
    url = url.strip()
    if "discord.com/api/webhooks/" not in url and "discordapp.com/api/webhooks/" not in url:
        return False
    lowered = url.lower()
    placeholders = ("your-webhook", "your_webhook", "xxxx", "<", "example")
    return not any(token in lowered for token in placeholders)


class DiscordNotifier:
    def __init__(self, webhook_url: str | None, *, opener: Opener | None = None, timeout: float = 10.0) -> None:
        self.webhook_url = (webhook_url or "").strip()
        self._opener = opener or (lambda req, timeout: urllib.request.urlopen(req, timeout=timeout))
        self._timeout = timeout

    @property
    def enabled(self) -> bool:
        return _looks_real(self.webhook_url)

    def send(self, content: str, *, username: str = "Revenue Engine") -> bool:
        if not self.enabled:
            return False
        body = {
            "content": content[:DISCORD_CONTENT_LIMIT],
            "username": username,
            # Never let @everyone/@here in generated text actually ping anyone.
            "allowed_mentions": {"parse": []},
        }
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "infinite-revenue-engine"},
            method="POST",
        )
        try:
            with self._opener(request, self._timeout):
                return True
        except Exception:
            # Notifications must never break the pipeline.
            return False


def _fmt_money(value: float) -> str:
    value = float(value or 0)
    return f"${value:,.2f}".rstrip("0").rstrip(".") if value % 1 else f"${value:,.0f}"


def build_daily_summary_message(snapshot: dict) -> str:
    revenue = _fmt_money(snapshot.get("revenue_usd", 0))
    lines = [
        "**📊 Resumen diario — Infinite Revenue Engine**",
        f"• Oportunidades: **{snapshot.get('opportunities', 0)}**",
        f"• Assets generados: **{snapshot.get('assets', 0)}**",
        f"• Ofertas vivas: **{snapshot.get('offers', 0)}**",
        f"• Clicks: **{snapshot.get('clicks', 0)}** · Conversiones: **{snapshot.get('conversions', 0)}**",
        f"• Ingreso registrado: **{revenue}**",
    ]
    site = snapshot.get("site_url")
    if site:
        lines.append(f"🔗 {site}")
    return "\n".join(lines)


def build_conversion_message(*, amount_usd: float, source: str, offer_key: str | None) -> str:
    amount = _fmt_money(amount_usd)
    parts = [f"**💰 Nueva conversión: {amount}**", f"Fuente: `{source}`"]
    if offer_key:
        parts.append(f"Oferta: `{offer_key}`")
    return "\n".join(parts)


def build_error_message(*, phase: str, detail: str) -> str:
    return f"**⚠️ Error en fase `{phase}`**\n```\n{detail[:1500]}\n```"


def build_ideas_message(titles: list[str], *, total: int) -> str:
    shown = titles[:15]
    body = "\n".join(f"{i}. {t}" for i, t in enumerate(shown, 1))
    header = f"**💡 {total} ideas en el banco — top {len(shown)}:**"
    return f"{header}\n{body}"
