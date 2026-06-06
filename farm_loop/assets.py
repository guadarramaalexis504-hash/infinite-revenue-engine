from __future__ import annotations

from dataclasses import dataclass

from .revenue_scoring import RevenueOpportunity


ASSET_TYPES = [
    "microtool_spec",
    "article_outline",
    "github_patch_plan",
    "product_listing",
    "landing_page_copy",
    "support_offer",
]

BLOCKED_PUBLICATION_RULES = {
    ("stackoverflow", "ai_generated_answer"),
    ("stackexchange", "ai_generated_answer"),
}


@dataclass(frozen=True)
class AssetDraft:
    asset_type: str
    title: str
    body_markdown: str
    status: str = "draft"
    publication_mode: str = "manual_review"

    def to_payload(self, opportunity_id: str | None, opportunity: RevenueOpportunity) -> dict:
        return {
            "opportunity_id": opportunity_id,
            "asset_type": self.asset_type,
            "title": self.title,
            "body_markdown": self.body_markdown,
            "status": self.status,
            "publication_mode": self.publication_mode,
            "channel": opportunity.channel,
        }


def is_publication_allowed(channel: str, asset_type: str) -> bool:
    return (channel.lower(), asset_type.lower()) not in BLOCKED_PUBLICATION_RULES


class AssetGenerator:
    def generate_all(self, opportunity: RevenueOpportunity) -> list[AssetDraft]:
        return [self.generate(asset_type, opportunity) for asset_type in ASSET_TYPES]

    def generate(self, asset_type: str, opportunity: RevenueOpportunity) -> AssetDraft:
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Unsupported asset type: {asset_type}")
        title = f"{self._label(asset_type)}: {opportunity.title}"
        body = "\n".join(
            [
                f"# {title}",
                "",
                f"Problem: {opportunity.problem}",
                f"Channel: {opportunity.channel}",
                f"Tags: {', '.join(opportunity.tags)}",
                f"Expected value: ${opportunity.expected_value_usd:.2f}",
                "",
                "Next manual step: review accuracy, add proof, then publish only on owned or explicitly permitted channels.",
            ]
        )
        return AssetDraft(asset_type=asset_type, title=title, body_markdown=body)

    def _label(self, asset_type: str) -> str:
        return asset_type.replace("_", " ").title()
