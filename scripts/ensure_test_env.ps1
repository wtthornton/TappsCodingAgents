# Ensure a .venv exists with Python 3.13 and project + dev deps so tests can run.
# Run from repo root: .\scripts\ensure_test_env.ps1
# If you see "file is being used by another process" during pip, close Cursor/IDE and re-run.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$venv = Join-Path $root ".venv"
$py = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "Creating .venv with Python 3.13..."
    py -3.13 -m venv .venv
    if (-not (Test-Path $py)) { Write-Error ".venv\Scripts\python.exe not found after venv create" }
}

Write-Host "Installing project and [dev] deps (pytest, etc.)..."
& $py -m pip install -e ".[dev]" 2>&1 | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "If the error was 'The process cannot access the file because it is being used by another process',"
    Write-Host "close Cursor/IDE (to release .venv), then run: .\scripts\ensure_test_env.ps1"
    exit $LASTEXITCODE
}

Write-Host "Verifying: python -c 'import tapps_agents; import pytest'"
& $py -c "import tapps_agents; import pytest; print('OK')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Test env ready. Run: .\scripts\run_integration_tests.ps1  or  .venv\Scripts\python -m pytest -m integration tests\integration\beads\ -v"
