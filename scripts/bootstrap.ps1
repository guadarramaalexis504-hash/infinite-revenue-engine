param(
    [switch]$ApplySchema,
    [switch]$SkipDryRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Fill the real values before running live automation."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v

if ($ApplySchema) {
    $envValues = Get-Content ".env" | Where-Object { $_ -match "^\s*DATABASE_URL\s*=" }
    if (-not $envValues) {
        throw "DATABASE_URL is required in .env when using -ApplySchema."
    }
    $databaseUrl = ($envValues[0] -split "=", 2)[1].Trim().Trim('"').Trim("'")
    if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
        throw "psql is required to apply supabase/schema.sql automatically."
    }
    psql $databaseUrl -f "supabase/schema.sql"
}

if (-not $SkipDryRun) {
    & ".\.venv\Scripts\python.exe" -m farm_loop.main --once --dry-run
}

Write-Host "Bootstrap complete."
