from __future__ import annotations

import json
import re
from pathlib import Path

from .assets import AssetDraft
from .revenue_scoring import RevenueOpportunity


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "asset"


class LocalAssetExporter:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export_opportunity(self, opportunity: RevenueOpportunity, assets: list[AssetDraft]) -> list[str]:
        opportunity_dir = self.output_dir / self._opportunity_slug(opportunity)
        opportunity_dir.mkdir(parents=True, exist_ok=True)

        asset_files: list[str] = []
        written: list[str] = []
        for index, asset in enumerate(assets, start=1):
            filename = f"{index:02d}-{slugify(asset.asset_type)}.md"
            path = opportunity_dir / filename
            path.write_text(asset.body_markdown + "\n", encoding="utf-8")
            asset_files.append(filename)
            written.append(str(path))

        manifest = {
            "publication_mode": "manual_review",
            "opportunity": opportunity.to_payload(),
            "asset_files": asset_files,
        }
        manifest_path = opportunity_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return [str(manifest_path), *written]

    def _opportunity_slug(self, opportunity: RevenueOpportunity) -> str:
        source = slugify(opportunity.source)
        external_id = slugify(opportunity.external_id)
        return f"{source}-{external_id}"
