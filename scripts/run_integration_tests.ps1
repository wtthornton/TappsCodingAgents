# Run Beads integration tests. Requires .venv and bd in tools/bd or on PATH.
# Run from repo root: .\scripts\run_integration_tests.ps1
# To set up .venv first: .\scripts\ensure_test_env.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "No .venv. Run: .\scripts\ensure_test_env.ps1"
}

& $py -m pytest -m integration tests\integration\beads\ -v
