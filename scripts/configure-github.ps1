param(
    [switch]$RunWorkflow
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required. Install it and run gh auth login first."
}

if (-not (Test-Path ".env")) {
    throw ".env not found. Run scripts/bootstrap.ps1 first, then fill real values."
}

$secretNames = @(
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "OPENAI_API_KEY",
    "STACKEXCHANGE_KEY",
    "BUYMEACOFFEE_WEBHOOK_TOKEN",
    "TIP_URL"
)

$envMap = @{}
Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $parts = $line -split "=", 2
        $envMap[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
}

foreach ($name in $secretNames) {
    if (-not $envMap.ContainsKey($name) -or [string]::IsNullOrWhiteSpace($envMap[$name])) {
        throw "Missing $name in .env"
    }
    $value = $envMap[$name].ToLowerInvariant()
    if ($value.Contains("your-") -or $value.StartsWith("sk-your-") -or $value.StartsWith("your_")) {
        throw "$name still looks like a placeholder. Fill .env with the real value before configuring GitHub."
    }
    if ($name -eq "SUPABASE_KEY" -and ($value.StartsWith("sb_publishable_") -or $value.StartsWith("eyj"))) {
        throw "SUPABASE_KEY must be a Supabase secret/service-role key for this server-side workflow, not anon or publishable."
    }
}

foreach ($name in $secretNames) {
    $envMap[$name] | gh secret set $name --app actions
    Write-Host "Set GitHub secret: $name"
}

if ($RunWorkflow) {
    gh workflow run farm-loop.yml
    Write-Host "Triggered farm-loop.yml"
}

Write-Host "GitHub automation configured."
