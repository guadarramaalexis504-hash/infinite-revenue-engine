from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_GITHUB_SECRETS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "OPENAI_API_KEY",
    "STACKEXCHANGE_KEY",
    "BUYMEACOFFEE_WEBHOOK_TOKEN",
    "TIP_URL",
]

OPTIONAL_GITHUB_SECRETS = [
    "CLICK_REDIRECT_URL",
    "CONVERSION_WEBHOOK_TOKEN",
    "SERVICE_INTAKE_URL",
    "SITE_BASE_URL",
]


def github_secret_names() -> list[str]:
    return list(REQUIRED_GITHUB_SECRETS)


def optional_github_secret_names() -> list[str]:
    return list(OPTIONAL_GITHUB_SECRETS)


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
        if (
            "your-" in normalized
            or "your_" in normalized
            or "example.com" in normalized
            or "optional_for_" in normalized
            or normalized.startswith("sk-your-")
        ):
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


def build_activation_report(
    *,
    env: dict[str, str],
    env_exists: bool,
    schema_exists: bool,
    farm_workflow_exists: bool,
    pages_workflow_exists: bool,
    git_remote_exists: bool,
    gh_installed: bool,
    gh_authenticated: bool,
) -> dict:
    checks: list[dict[str, str]] = []
    next_actions: list[str] = []

    def add_check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if env_exists:
        add_check("env_file", "pass", ".env exists")
    else:
        add_check("env_file", "fail", ".env not found")
        next_actions.append("Run scripts/bootstrap.ps1, then fill .env with real credentials")

    missing = missing_required_vars(env)
    if missing:
        add_check("required_env", "fail", "Missing: " + ", ".join(missing))
        next_actions.append("Fill required .env values: " + ", ".join(missing))
    else:
        add_check("required_env", "pass", "Required runtime values are present")

    placeholders = placeholder_vars(env)
    if placeholders:
        add_check("placeholders", "fail", "Still placeholder-like: " + ", ".join(placeholders))
        next_actions.append("Replace placeholder .env values: " + ", ".join(placeholders))
    else:
        add_check("placeholders", "pass", "No placeholder-like .env values detected")

    insecure_keys = insecure_supabase_key_vars(env)
    if insecure_keys:
        add_check("supabase_key_type", "fail", "SUPABASE_KEY looks public/anon, not server-side")
        next_actions.append("Use a Supabase secret/service-role key server-side, not anon or publishable")
    else:
        add_check("supabase_key_type", "pass", "Supabase key does not look public")

    add_check(
        "supabase_schema",
        "pass" if schema_exists else "fail",
        "supabase/schema.sql found" if schema_exists else "supabase/schema.sql missing",
    )
    if not schema_exists:
        next_actions.append("Restore supabase/schema.sql before applying the database schema")

    add_check(
        "farm_workflow",
        "pass" if farm_workflow_exists else "fail",
        ".github/workflows/farm-loop.yml found" if farm_workflow_exists else "farm-loop.yml missing",
    )
    if not farm_workflow_exists:
        next_actions.append("Restore .github/workflows/farm-loop.yml")

    add_check(
        "pages_workflow",
        "pass" if pages_workflow_exists else "fail",
        ".github/workflows/pages-site.yml found" if pages_workflow_exists else "pages-site.yml missing",
    )
    if not pages_workflow_exists:
        next_actions.append("Restore .github/workflows/pages-site.yml")

    add_check(
        "git_remote",
        "pass" if git_remote_exists else "fail",
        "Git remote is configured" if git_remote_exists else "No git remote configured",
    )
    if not git_remote_exists:
        next_actions.append("Add git remote origin")

    add_check(
        "gh_cli",
        "pass" if gh_installed else "fail",
        "GitHub CLI is installed" if gh_installed else "GitHub CLI is not installed",
    )
    if not gh_installed:
        next_actions.append("Install GitHub CLI")

    add_check(
        "gh_auth",
        "pass" if gh_authenticated else "fail",
        "GitHub CLI is authenticated" if gh_authenticated else "GitHub CLI is not authenticated",
    )
    if not gh_authenticated:
        next_actions.append("Run gh auth login")

    ready = not any(check["status"] == "fail" for check in checks)
    return {
        "ready": ready,
        "checks": checks,
        "next_actions": _unique(next_actions),
    }


def collect_activation_report(root: str | Path = ".", env_file: str | Path = ".env") -> dict:
    root_path = Path(root)
    env_path = Path(env_file)
    if not env_path.is_absolute():
        env_path = root_path / env_path

    env_exists = env_path.exists()
    env = load_env_file(env_path)
    gh_installed = shutil.which("gh") is not None
    return build_activation_report(
        env=env,
        env_exists=env_exists,
        schema_exists=(root_path / "supabase" / "schema.sql").exists(),
        farm_workflow_exists=(root_path / ".github" / "workflows" / "farm-loop.yml").exists(),
        pages_workflow_exists=(root_path / ".github" / "workflows" / "pages-site.yml").exists(),
        git_remote_exists=_git_remote_exists(root_path),
        gh_installed=gh_installed,
        gh_authenticated=_gh_authenticated(root_path) if gh_installed else False,
    )


def format_activation_report(report: dict) -> str:
    lines = ["Infinite Revenue Engine activation preflight:"]
    for check in report["checks"]:
        marker = "OK" if check["status"] == "pass" else "FAIL"
        lines.append(f"- [{marker}] {check['name']}: {check['detail']}")
    if report["ready"]:
        lines.append("Ready: yes. You can run scripts/configure-github.ps1 -RunWorkflow.")
    else:
        lines.append("Ready: no. Next actions:")
        for action in report["next_actions"]:
            lines.append(f"- {action}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check whether Infinite Revenue Engine can run live.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--env-file", default=".env", help="Environment file to inspect.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    report = collect_activation_report(root=args.root, env_file=args.env_file)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_activation_report(report))
    return 0 if report["ready"] else 1


def _git_remote_exists(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "remote"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def _gh_authenticated(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
