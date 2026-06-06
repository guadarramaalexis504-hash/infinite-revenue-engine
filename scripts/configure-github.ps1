param(
    [switch]$RunWorkflow,
    [string]$Repo
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required. Install it and run gh auth login first."
}

gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run gh auth login first."
}

if ([string]::IsNullOrWhiteSpace($Repo)) {
    $remotes = git remote
    if (-not $remotes) {
        throw "No git remote found. Add git remote origin or pass -Repo owner/name."
    }
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

$optionalSecretNames = @(
    "CLICK_REDIRECT_URL",
    "CONVERSION_WEBHOOK_TOKEN",
    "SERVICE_INTAKE_URL",
    "SITE_BASE_URL"
)

$envMap = @{}
Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $parts = $line -split "=", 2
        $envMap[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
}

function Test-PlaceholderValue {
    param([string]$Value)

    $lower = $Value.ToLowerInvariant()
    return (
        $lower.Contains("your-") -or
        $lower.Contains("your_") -or
        $lower.Contains("example.com") -or
        $lower.Contains("optional_for_") -or
        $lower.StartsWith("sk-your-")
    )
}

foreach ($name in $secretNames) {
    if (-not $envMap.ContainsKey($name) -or [string]::IsNullOrWhiteSpace($envMap[$name])) {
        throw "Missing $name in .env"
    }
    $value = $envMap[$name].ToLowerInvariant()
    if (Test-PlaceholderValue $value) {
        throw "$name still looks like a placeholder. Fill .env with the real value before configuring GitHub."
    }
    if ($name -eq "SUPABASE_KEY" -and ($value.StartsWith("sb_publishable_") -or $value.StartsWith("eyj"))) {
        throw "SUPABASE_KEY must be a Supabase secret/service-role key for this server-side workflow, not anon or publishable."
    }
}

$secretsToSet = @()
foreach ($name in $secretNames) {
    $secretsToSet += $name
}

foreach ($name in $optionalSecretNames) {
    if ($envMap.ContainsKey($name) -and -not [string]::IsNullOrWhiteSpace($envMap[$name])) {
        if (Test-PlaceholderValue $envMap[$name]) {
            Write-Host "Skipping optional placeholder secret: $name"
        } else {
            $secretsToSet += $name
        }
    }
}

$repoArgs = @()
if (-not [string]::IsNullOrWhiteSpace($Repo)) {
    $repoArgs = @("--repo", $Repo)
}

foreach ($name in $secretsToSet) {
    $envMap[$name] | gh secret set $name --app actions @repoArgs
    Write-Host "Set GitHub secret: $name"
}

if ($RunWorkflow) {
    gh workflow run farm-loop.yml @repoArgs
    Write-Host "Triggered farm-loop.yml"
}

Write-Host "GitHub automation configured."
