param(
    [int]$IntervalSeconds = 300
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (Test-Path ".venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" -m farm_loop.main --loop --interval-seconds $IntervalSeconds
} else {
    python -m farm_loop.main --loop --interval-seconds $IntervalSeconds
}
