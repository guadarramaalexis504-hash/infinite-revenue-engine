from __future__ import annotations

from pathlib import Path


REQUIRED_GITHUB_SECRETS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "OPENAI_API_KEY",
    "STACKEXCHANGE_KEY",
    "BUYMEACOFFEE_WEBHOOK_TOKEN",
    "TIP_URL",
]


def github_secret_names() -> list[str]:
    return list(REQUIRED_GITHUB_SECRETS)


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def missing_required_vars(env: dict[str, str], required: list[str] | None = None) -> list[str]:
    required_names = required or REQUIRED_GITHUB_SECRETS
    return [name for name in required_names if not env.get(name)]


def placeholder_vars(env: dict[str, str]) -> list[str]:
    placeholders: list[str] = []
    for name, value in env.items():
        normalized = value.strip().lower()
        if not normalized:
            continue
        if "your-" in normalized or normalized.startswith("sk-your-") or normalized.startswith("your_"):
            placeholders.append(name)
    return placeholders


def insecure_supabase_key_vars(env: dict[str, str]) -> list[str]:
    value = env.get("SUPABASE_KEY", "").strip()
    if not value:
        return []
    normalized = value.lower()
    if normalized.startswith("sb_publishable_") or normalized.startswith("eyj"):
        return ["SUPABASE_KEY"]
    return []
