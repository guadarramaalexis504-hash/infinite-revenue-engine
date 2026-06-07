from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .revenue_scoring import RevenueOpportunity


def build_tracking_url(
    base_url: str,
    opportunity: RevenueOpportunity,
    *,
    content: str,
    offer_key: str | None = None,
) -> str:
    parts = urlsplit(base_url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.extend(_attribution_pairs(opportunity, content=content, offer_key=offer_key))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def build_click_redirect_url(
    click_endpoint_url: str,
    opportunity: RevenueOpportunity,
    *,
    target_url: str,
    content: str,
    offer_key: str | None = None,
) -> str:
    tracked_target = build_tracking_url(target_url, opportunity, content=content, offer_key=offer_key)
    parts = urlsplit(click_endpoint_url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.extend(
        [
            ("target", tracked_target),
            ("opportunity_source", opportunity.source),
            ("opportunity_external_id", opportunity.external_id),
            ("channel", opportunity.channel),
            ("content", content),
        ]
    )
    if offer_key:
        query.append(("offer_key", offer_key))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def build_click_event_payload(
    opportunity: RevenueOpportunity,
    *,
    target_url: str,
    content: str,
    offer_id: str | None = None,
    offer_key: str | None = None,
) -> dict:
    payload = {
        "opportunity_source": opportunity.source,
        "opportunity_external_id": opportunity.external_id,
        "channel": opportunity.channel,
        "target_url": target_url,
        "content": content,
        "utm_source": "revenue_site",
        "utm_medium": opportunity.channel,
        "utm_campaign": opportunity.external_id,
        "utm_content": content,
    }
    if offer_key:
        payload["offer_key"] = offer_key
    return {"offer_id": offer_id, "source": "revenue_site", "payload": payload}


def _attribution_pairs(
    opportunity: RevenueOpportunity,
    *,
    content: str,
    offer_key: str | None = None,
) -> list[tuple[str, str]]:
    pairs = [
        ("utm_source", "revenue_site"),
        ("utm_medium", opportunity.channel),
        ("utm_campaign", opportunity.external_id),
        ("utm_content", content),
        ("ire_source", opportunity.source),
        ("ire_external_id", opportunity.external_id),
    ]
    if offer_key:
        pairs.append(("ire_offer_key", offer_key))
    return pairs
