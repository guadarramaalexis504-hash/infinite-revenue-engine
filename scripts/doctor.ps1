param(
    [string]$EnvFile = ".env",
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$python = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $python = ".\.venv\Scripts\python.exe"
}

$args = @("-m", "farm_loop.automation", "--env-file", $EnvFile)
if ($Json) {
    $args += "--json"
}

& $python @args
exit $LASTEXITCODE
