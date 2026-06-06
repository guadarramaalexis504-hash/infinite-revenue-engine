from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .revenue_scoring import RevenueOpportunity


def build_tracking_url(base_url: str, opportunity: RevenueOpportunity, *, content: str) -> str:
    parts = urlsplit(base_url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.extend(
        [
            ("utm_source", "revenue_site"),
            ("utm_medium", opportunity.channel),
            ("utm_campaign", opportunity.external_id),
            ("utm_content", content),
            ("ire_source", opportunity.source),
            ("ire_external_id", opportunity.external_id),
        ]
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def build_click_redirect_url(
    click_endpoint_url: str,
    opportunity: RevenueOpportunity,
    *,
    target_url: str,
    content: str,
) -> str:
    tracked_target = build_tracking_url(target_url, opportunity, content=content)
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
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def build_click_event_payload(
    opportunity: RevenueOpportunity,
    *,
    target_url: str,
    content: str,
    offer_id: str | None = None,
) -> dict:
    return {
        "offer_id": offer_id,
        "source": "revenue_site",
        "payload": {
            "opportunity_source": opportunity.source,
            "opportunity_external_id": opportunity.external_id,
            "channel": opportunity.channel,
            "target_url": target_url,
            "content": content,
            "utm_source": "revenue_site",
            "utm_medium": opportunity.channel,
            "utm_campaign": opportunity.external_id,
            "utm_content": content,
        },
    }
