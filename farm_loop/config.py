from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_TAGS = "python;fastapi;supabase;openai-api"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None
    supabase_key: str | None
    openai_api_key: str | None
    stackexchange_key: str | None
    tip_url: str
    github_token: str | None = None
    tags: str = DEFAULT_TAGS
    target_usd: float = 15.0
    revenue_milestones: list[float] | None = None
    max_drafts: int = 3
    openai_model: str = "gpt-4o-mini"
    stop_after_target: bool = False
    keyword_csv_path: str = "data/revenue_keywords.csv"
    idea_catalog_path: str = "data/revenue_ideas.json"
    asset_output_dir: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            stackexchange_key=os.getenv("STACKEXCHANGE_KEY"),
            github_token=os.getenv("GITHUB_TOKEN"),
            tip_url=os.getenv("TIP_URL", ""),
            tags=os.getenv("STACKEXCHANGE_TAGS", DEFAULT_TAGS),
            target_usd=float(os.getenv("TARGET_USD", "15")),
            revenue_milestones=_parse_milestones(os.getenv("REVENUE_MILESTONES", "15,200,1000,20000")),
            max_drafts=int(os.getenv("MAX_DRAFTS_PER_RUN", "3")),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            stop_after_target=_env_bool("STOP_AFTER_TARGET", False),
            keyword_csv_path=os.getenv("KEYWORD_CSV_PATH", "data/revenue_keywords.csv"),
            idea_catalog_path=os.getenv("IDEA_CATALOG_PATH", "data/revenue_ideas.json"),
            asset_output_dir=os.getenv("ASSET_OUTPUT_DIR"),
        )

    def require_runtime_secrets(self, dry_run: bool) -> None:
        if dry_run:
            return
        missing = []
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_key:
            missing.append("SUPABASE_KEY")
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.tip_url:
            missing.append("TIP_URL")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def _parse_milestones(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]
