from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_TAGS = "python;fastapi;supabase;openai-api"


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None
    supabase_key: str | None
    openai_api_key: str | None
    stackexchange_key: str | None
    tip_url: str
    tags: str = DEFAULT_TAGS
    target_usd: float = 15.0
    max_drafts: int = 3
    openai_model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            stackexchange_key=os.getenv("STACKEXCHANGE_KEY"),
            tip_url=os.getenv("TIP_URL", ""),
            tags=os.getenv("STACKEXCHANGE_TAGS", DEFAULT_TAGS),
            target_usd=float(os.getenv("TARGET_USD", "15")),
            max_drafts=int(os.getenv("MAX_DRAFTS_PER_RUN", "3")),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
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
