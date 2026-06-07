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
    buymeacoffee_webhook_token: str | None = None
    conversion_webhook_token: str | None = None
    click_allowed_hosts: str = "buymeacoffee.com,www.buymeacoffee.com"
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
    site_output_dir: str | None = None
    site_base_url: str | None = None
    click_redirect_url: str | None = None
    service_intake_url: str | None = None
    offer_payment_urls: str = ""
    launch_queue_output_dir: str | None = None
    microtool_output_dir: str | None = None
    offer_output_dir: str | None = None
    checkout_setup_output_dir: str | None = None
    conversion_webhook_base_url: str | None = None
    tracking_deploy_output_dir: str | None = None
    tracking_public_base_url: str | None = None
    lead_magnet_output_dir: str | None = None
    lead_capture_url: str | None = None
    digital_product_output_dir: str | None = None
    service_package_output_dir: str | None = None
    niche_report_output_dir: str | None = None
    affiliate_article_output_dir: str | None = None
    affiliate_urls: str = ""
    sponsor_repo_output_dir: str | None = None
    sponsor_urls: str = ""
    roadmap_output_dir: str | None = None
    activation_manifest_output_dir: str | None = None
    revenue_forecast_output_dir: str | None = None
    offer_ladder_output_dir: str | None = None
    launch_sprint_output_dir: str | None = None
    traffic_plan_output_dir: str | None = None
    all_ideas_output_dir: str | None = None
    bundle_output_dir: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            stackexchange_key=os.getenv("STACKEXCHANGE_KEY"),
            github_token=os.getenv("GITHUB_TOKEN"),
            tip_url=os.getenv("TIP_URL", ""),
            buymeacoffee_webhook_token=os.getenv("BUYMEACOFFEE_WEBHOOK_TOKEN"),
            conversion_webhook_token=os.getenv("CONVERSION_WEBHOOK_TOKEN"),
            click_allowed_hosts=os.getenv("CLICK_ALLOWED_HOSTS", "buymeacoffee.com,www.buymeacoffee.com"),
            tags=os.getenv("STACKEXCHANGE_TAGS", DEFAULT_TAGS),
            target_usd=float(os.getenv("TARGET_USD", "15")),
            revenue_milestones=_parse_milestones(os.getenv("REVENUE_MILESTONES", "15,200,1000,20000")),
            max_drafts=int(os.getenv("MAX_DRAFTS_PER_RUN", "3")),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            stop_after_target=_env_bool("STOP_AFTER_TARGET", False),
            keyword_csv_path=os.getenv("KEYWORD_CSV_PATH", "data/revenue_keywords.csv"),
            idea_catalog_path=os.getenv("IDEA_CATALOG_PATH", "data/revenue_ideas.json"),
            asset_output_dir=os.getenv("ASSET_OUTPUT_DIR"),
            site_output_dir=os.getenv("SITE_OUTPUT_DIR"),
            site_base_url=os.getenv("SITE_BASE_URL"),
            click_redirect_url=os.getenv("CLICK_REDIRECT_URL"),
            service_intake_url=os.getenv("SERVICE_INTAKE_URL"),
            offer_payment_urls=os.getenv("OFFER_PAYMENT_URLS", ""),
            launch_queue_output_dir=os.getenv("LAUNCH_QUEUE_OUTPUT_DIR"),
            microtool_output_dir=os.getenv("MICROTOOL_OUTPUT_DIR"),
            offer_output_dir=os.getenv("OFFER_OUTPUT_DIR"),
            checkout_setup_output_dir=os.getenv("CHECKOUT_SETUP_OUTPUT_DIR"),
            conversion_webhook_base_url=os.getenv("CONVERSION_WEBHOOK_BASE_URL"),
            tracking_deploy_output_dir=os.getenv("TRACKING_DEPLOY_OUTPUT_DIR"),
            tracking_public_base_url=os.getenv("TRACKING_PUBLIC_BASE_URL"),
            lead_magnet_output_dir=os.getenv("LEAD_MAGNET_OUTPUT_DIR"),
            lead_capture_url=os.getenv("LEAD_CAPTURE_URL"),
            digital_product_output_dir=os.getenv("DIGITAL_PRODUCT_OUTPUT_DIR"),
            service_package_output_dir=os.getenv("SERVICE_PACKAGE_OUTPUT_DIR"),
            niche_report_output_dir=os.getenv("NICHE_REPORT_OUTPUT_DIR"),
            affiliate_article_output_dir=os.getenv("AFFILIATE_ARTICLE_OUTPUT_DIR"),
            affiliate_urls=os.getenv("AFFILIATE_URLS", ""),
            sponsor_repo_output_dir=os.getenv("SPONSOR_REPO_OUTPUT_DIR"),
            sponsor_urls=os.getenv("SPONSOR_URLS", ""),
            roadmap_output_dir=os.getenv("ROADMAP_OUTPUT_DIR"),
            activation_manifest_output_dir=os.getenv("ACTIVATION_MANIFEST_OUTPUT_DIR"),
            revenue_forecast_output_dir=os.getenv("REVENUE_FORECAST_OUTPUT_DIR"),
            offer_ladder_output_dir=os.getenv("OFFER_LADDER_OUTPUT_DIR"),
            launch_sprint_output_dir=os.getenv("LAUNCH_SPRINT_OUTPUT_DIR"),
            traffic_plan_output_dir=os.getenv("TRAFFIC_PLAN_OUTPUT_DIR"),
            all_ideas_output_dir=os.getenv("ALL_IDEAS_OUTPUT_DIR"),
            bundle_output_dir=os.getenv("BUNDLE_OUTPUT_DIR"),
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
