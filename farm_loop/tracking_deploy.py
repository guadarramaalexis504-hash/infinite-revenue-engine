from __future__ import annotations

import json
from pathlib import Path


CONVERSION_PROVIDERS = ["stripe", "gumroad", "lemon_squeezy", "manual"]
REQUIRED_ENV = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "BUYMEACOFFEE_WEBHOOK_TOKEN",
    "CONVERSION_WEBHOOK_TOKEN",
]
OPTIONAL_ENV = [
    "TIP_URL",
    "SERVICE_INTAKE_URL",
    "CLICK_ALLOWED_HOSTS",
]


def build_tracking_deploy_manifest(
    *,
    public_base_url: str = "",
    output_dir: str = "out/tracking-deploy",
    image_name: str = "infinite-revenue-tracker",
) -> dict:
    base_url = public_base_url.rstrip("/")
    return {
        "required_env": list(REQUIRED_ENV),
        "optional_env": list(OPTIONAL_ENV),
        "endpoints": {
            "health": _url(base_url, "/health"),
            "click": _url(base_url, "/click"),
            "buymeacoffee_webhook": _url(base_url, "/webhooks/buymeacoffee"),
            "conversion_webhook_base": _url(base_url, "/webhooks/conversion"),
        },
        "provider_webhooks": {
            provider: _url(base_url, f"/webhooks/conversion/{provider}") for provider in CONVERSION_PROVIDERS
        },
        "docker": {
            "image_name": image_name,
            "build_command": f"docker build -f {output_dir.rstrip('/')}/Dockerfile -t {image_name} .",
            "run_command": f"docker run --env-file {output_dir.rstrip('/')}/.env.tracking.example -p 8080:8080 {image_name}",
        },
    }


class TrackingDeployExporter:
    def __init__(
        self,
        output_dir: str | Path,
        *,
        public_base_url: str = "",
        image_name: str = "infinite-revenue-tracker",
    ):
        self.output_dir = Path(output_dir)
        self.public_base_url = public_base_url
        self.image_name = image_name

    def export(self) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        manifest = build_tracking_deploy_manifest(
            public_base_url=self.public_base_url,
            output_dir=self.output_dir.as_posix(),
            image_name=self.image_name,
        )
        files = {
            "Dockerfile": _dockerfile(),
            ".env.tracking.example": _env_example(),
            "tracking_deploy.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            "DEPLOY_TRACKING_APP.md": _markdown(manifest),
        }
        paths: list[Path] = []
        for filename, body in files.items():
            path = self.output_dir / filename
            path.write_text(body, encoding="utf-8")
            paths.append(path)
        return paths


def _url(base_url: str, path: str) -> str:
    if not base_url:
        return path
    return f"{base_url}{path}"


def _dockerfile() -> str:
    return """FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY farm_loop ./farm_loop
EXPOSE 8080
CMD python -m farm_loop.http_app --host 0.0.0.0 --port ${PORT:-8080}
"""


def _env_example() -> str:
    return """SUPABASE_URL=
SUPABASE_KEY=
BUYMEACOFFEE_WEBHOOK_TOKEN=
CONVERSION_WEBHOOK_TOKEN=
CLICK_ALLOWED_HOSTS=buymeacoffee.com,www.buymeacoffee.com
TIP_URL=
SERVICE_INTAKE_URL=
"""


def _markdown(manifest: dict) -> str:
    lines = [
        "# Tracking App Deploy",
        "",
        "Build this from the repository root so Docker can copy `farm_loop/` and `requirements.txt`:",
        "",
        "```powershell",
        manifest["docker"]["build_command"],
        manifest["docker"]["run_command"],
        "```",
        "",
        "Set these as server-side environment variables on the host. Do not put `SUPABASE_KEY` in browser JavaScript.",
        "",
        "Required environment variables:",
    ]
    lines.extend(f"- {name}" for name in manifest["required_env"])
    lines.extend(["", "Optional environment variables:"])
    lines.extend(f"- {name}" for name in manifest["optional_env"])
    lines.extend(
        [
            "",
            "Public endpoints:",
            f"- health: {manifest['endpoints']['health']}",
            f"- click redirect: {manifest['endpoints']['click']}",
            f"- Buy Me a Coffee webhook: {manifest['endpoints']['buymeacoffee_webhook']}",
            f"- conversion webhook base: {manifest['endpoints']['conversion_webhook_base']}",
            "",
            "Provider webhook URLs:",
        ]
    )
    for provider, url in manifest["provider_webhooks"].items():
        lines.append(f"- {provider}: {url}")
    lines.extend(
        [
            "",
            "After deploy, set `CLICK_REDIRECT_URL` to the public `/click` URL and `CONVERSION_WEBHOOK_BASE_URL` to the public `/webhooks/conversion` URL before regenerating the revenue bundle.",
            "",
        ]
    )
    return "\n".join(lines)
