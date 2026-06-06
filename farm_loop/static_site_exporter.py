from __future__ import annotations

from html import escape
from pathlib import Path

from .asset_exporter import slugify
from .assets import AssetDraft
from .offers import OfferDraft, generate_offers
from .revenue_scoring import RevenueOpportunity
from .tracking import build_click_redirect_url, build_tracking_url


class StaticSiteExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        tip_url: str = "",
        click_redirect_url: str = "",
        tools_path: str = "",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.tip_url = tip_url
        self.click_redirect_url = click_redirect_url
        self.tools_path = tools_path

    def export_portfolio(self, opportunities_with_assets: list[tuple[RevenueOpportunity, list[AssetDraft]]]) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        opportunities = [item[0] for item in opportunities_with_assets]

        for opportunity, assets in opportunities_with_assets:
            page_dir = self.output_dir / slugify(opportunity.external_id)
            page_dir.mkdir(parents=True, exist_ok=True)
            page_path = page_dir / "index.html"
            page_path.write_text(self._opportunity_page(opportunity, assets), encoding="utf-8")
            written.append(str(page_path))

        offers_dir = self.output_dir / "offers"
        offers_dir.mkdir(parents=True, exist_ok=True)
        offers_path = offers_dir / "index.html"
        offers_path.write_text(self._offers_page(opportunities), encoding="utf-8")

        index_path = self.output_dir / "index.html"
        index_path.write_text(self._index_page(opportunities), encoding="utf-8")
        return [str(index_path), str(offers_path), *written]

    def _index_page(self, opportunities: list[RevenueOpportunity]) -> str:
        cards = "\n".join(self._opportunity_card(opportunity) for opportunity in opportunities)
        tools_link = self._tools_link(prefix="")
        return self._page(
            "Infinite Revenue Engine",
            f"""
            <main class="shell">
              <header class="topbar">
                <strong>Infinite Revenue Engine</strong>
                <span>Owned static site</span>
                <a class="nav-link" href="offers/">Offers</a>
                {tools_link}
              </header>
              <section class="hero">
                <div>
                  <h1>Small useful tools and setup offers</h1>
                  <p>Reviewable opportunities generated from the portfolio engine. Publish only after manual review, proof, and channel checks.</p>
                </div>
              </section>
              <section class="grid" aria-label="Revenue opportunities">
                {cards}
              </section>
            </main>
            """,
        )

    def _opportunity_card(self, opportunity: RevenueOpportunity) -> str:
        path = f"{slugify(opportunity.external_id)}/"
        tags = ", ".join(escape(tag) for tag in opportunity.tags[:4])
        return f"""
        <article class="card">
          <p class="channel">{escape(opportunity.channel.replace("_", " "))}</p>
          <h2><a href="{escape(path)}">{escape(opportunity.title)}</a></h2>
          <p>{escape(opportunity.problem)}</p>
          <dl>
            <div><dt>Expected value</dt><dd>${opportunity.expected_value_usd:.2f}</dd></div>
            <div><dt>Build time</dt><dd>{opportunity.build_minutes} min</dd></div>
          </dl>
          <p class="tags">{tags}</p>
        </article>
        """

    def _opportunity_page(self, opportunity: RevenueOpportunity, assets: list[AssetDraft]) -> str:
        asset_sections = "\n".join(self._asset_section(asset) for asset in assets)
        cta = self._support_cta(opportunity)
        offers = self._offer_section(opportunity)
        tools_link = self._tools_link(prefix="../")
        return self._page(
            opportunity.title,
            f"""
            <main class="shell">
              <header class="topbar">
                <a href="../">Infinite Revenue Engine</a>
                <span>manual review</span>
                <a class="nav-link" href="../offers/">Offers</a>
                {tools_link}
              </header>
              <article class="detail">
                <p class="channel">{escape(opportunity.channel.replace("_", " "))}</p>
                <h1>{escape(opportunity.title)}</h1>
                <p class="lead">{escape(opportunity.problem)}</p>
                <dl class="metrics">
                  <div><dt>Expected value</dt><dd>${opportunity.expected_value_usd:.2f}</dd></div>
                  <div><dt>Estimated payout</dt><dd>${opportunity.payout_estimate_usd:.2f}</dd></div>
                  <div><dt>Build time</dt><dd>{opportunity.build_minutes} min</dd></div>
                </dl>
                {cta}
                {offers}
                <section class="asset-list" aria-label="Review drafts">
                  <h2>Review drafts</h2>
                  {asset_sections}
                </section>
              </article>
            </main>
            """,
        )

    def _offers_page(self, opportunities: list[RevenueOpportunity]) -> str:
        cards = "\n".join(
            self._catalog_offer_card(opportunity, offer)
            for opportunity in opportunities
            for offer in generate_offers(opportunity)
        )
        return self._page(
            "Offer Catalog",
            f"""
            <main class="shell">
              <header class="topbar">
                <a href="../">Infinite Revenue Engine</a>
                <span>owned offer catalog</span>
              </header>
              <section class="hero">
                <div>
                  <h1>Offer Catalog</h1>
                  <p>Reviewable services, support CTAs, and digital product offers from the current revenue portfolio.</p>
                </div>
              </section>
              <section class="offer-grid" aria-label="Monetizable offers">
                {cards}
              </section>
            </main>
            """,
        )

    def _catalog_offer_card(self, opportunity: RevenueOpportunity, offer: OfferDraft) -> str:
        detail_path = f"../{slugify(opportunity.external_id)}/"
        if self.tip_url:
            url = build_tracking_url(self.tip_url, opportunity, content=offer.offer_type)
            action = f'<a href="{escape(url)}">{escape(offer.cta_label)}</a>'
        else:
            action = "Configure TIP_URL before publishing offer CTAs."
        return f"""
        <article class="offer">
          <p class="channel">{escape(offer.channel.replace("_", " "))} / {escape(offer.offer_type.replace("_", " "))}</p>
          <h2>{escape(offer.title)}</h2>
          <strong>${offer.price_usd:.2f}</strong>
          <p>{escape(offer.description)}</p>
          <p><a href="{escape(detail_path)}">View opportunity</a></p>
          <p class="offer-action">{action}</p>
        </article>
        """

    def _asset_section(self, asset: AssetDraft) -> str:
        return f"""
        <section class="asset">
          <h3>{escape(asset.title)}</h3>
          <pre>{escape(asset.body_markdown)}</pre>
        </section>
        """

    def _support_cta(self, opportunity: RevenueOpportunity) -> str:
        if not self.tip_url:
            return '<p class="notice">Configure TIP_URL before publishing a support CTA.</p>'
        if self.click_redirect_url:
            url = build_click_redirect_url(
                self.click_redirect_url,
                opportunity,
                target_url=self.tip_url,
                content="support_cta",
            )
        else:
            url = build_tracking_url(self.tip_url, opportunity, content="support_cta")
        return f'<p class="notice">Useful? <a href="{escape(url)}">Support this work</a>.</p>'

    def _offer_section(self, opportunity: RevenueOpportunity) -> str:
        cards = "\n".join(self._offer_card(opportunity, offer) for offer in generate_offers(opportunity))
        return f"""
        <section class="offer-list" aria-label="Ways to work with this">
          <h2>Ways to work with this</h2>
          <div class="offer-grid">{cards}</div>
        </section>
        """

    def _offer_card(self, opportunity: RevenueOpportunity, offer: OfferDraft) -> str:
        if self.tip_url:
            url = build_tracking_url(self.tip_url, opportunity, content=offer.offer_type)
            action = f'<a href="{escape(url)}">{escape(offer.cta_label)}</a>'
        else:
            action = "Configure TIP_URL before publishing offer CTAs."
        return f"""
        <article class="offer">
          <p class="channel">{escape(offer.offer_type.replace("_", " "))}</p>
          <h3>{escape(offer.title)}</h3>
          <strong>${offer.price_usd:.2f}</strong>
          <p>{escape(offer.description)}</p>
          <p class="offer-action">{action}</p>
        </article>
        """

    def _tools_link(self, *, prefix: str) -> str:
        if not self.tools_path:
            return ""
        path = f"{prefix}{self.tools_path.lstrip('/')}"
        return f'<a class="nav-link" href="{escape(path)}">Interactive tools</a>'

    def _page(self, title: str, body: str) -> str:
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
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.5;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .shell {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 56px; }}
    .topbar {{ display: flex; justify-content: space-between; gap: 16px; padding: 12px 0 28px; color: var(--muted); }}
    .hero {{ display: grid; grid-template-columns: minmax(0, 720px); gap: 20px; padding: 56px 0 40px; border-top: 1px solid var(--line); }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4.5rem); line-height: 0.96; letter-spacing: 0; }}
    h2, h3 {{ letter-spacing: 0; }}
    .hero p, .lead {{ max-width: 760px; color: var(--muted); font-size: 1.08rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .card, .asset, .detail, .offer {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }}
    .card {{ padding: 18px; min-height: 260px; display: flex; flex-direction: column; gap: 10px; }}
    .card h2 {{ margin: 0; font-size: 1.25rem; }}
    .card p {{ margin: 0; color: var(--muted); }}
    .channel {{ margin: 0 0 8px; color: var(--accent); text-transform: uppercase; font-size: 0.78rem; font-weight: 700; }}
    dl {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: auto 0 0; }}
    dt {{ color: var(--muted); font-size: 0.76rem; }}
    dd {{ margin: 0; font-weight: 700; }}
    .tags {{ font-size: 0.86rem; }}
    .detail {{ padding: 28px; }}
    .metrics {{ max-width: 720px; margin: 26px 0; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }}
    .notice {{ background: var(--accent-soft); border: 1px solid #b6dbd2; border-radius: 8px; padding: 14px 16px; }}
    .asset-list {{ margin-top: 32px; display: grid; gap: 14px; }}
    .offer-list {{ margin-top: 28px; }}
    .offer-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
    .offer {{ padding: 16px; }}
    .offer strong {{ display: block; margin: 8px 0; font-size: 1.2rem; }}
    .offer-action {{ font-weight: 700; }}
    .asset {{ padding: 18px; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; margin: 0; color: var(--muted); font-family: Consolas, monospace; font-size: 0.9rem; }}
    @media (max-width: 640px) {{
      .topbar {{ display: grid; }}
      .detail {{ padding: 20px; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
