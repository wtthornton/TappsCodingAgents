# Version Update Script
# Updates version number in pyproject.toml and tapps_agents/__init__.py

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

# Validate semantic versioning format (X.Y.Z)
$versionPattern = '^\d+\.\d+\.\d+$'
if ($Version -notmatch $versionPattern) {
    Write-Host "ERROR: Invalid version format. Expected format: X.Y.Z (e.g., 2.0.6)" -ForegroundColor Red
    Write-Host "Provided: $Version" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Version Update Script ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Updating version to: $Version" -ForegroundColor Green
Write-Host ""

# Get current directory (should be project root)
$projectRoot = $PSScriptRoot | Split-Path -Parent
Set-Location $projectRoot

# Files to update
$pyprojectFile = Join-Path $projectRoot "pyproject.toml"
$initFile = Join-Path $projectRoot "tapps_agents\__init__.py"

# Verify files exist
if (-not (Test-Path $pyprojectFile)) {
    Write-Host "ERROR: pyproject.toml not found at: $pyprojectFile" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $initFile)) {
    Write-Host "ERROR: tapps_agents/__init__.py not found at: $initFile" -ForegroundColor Red
    exit 1
}

# Read current versions
$pyprojectContent = Get-Content $pyprojectFile -Raw
$initContent = Get-Content $initFile -Raw

# Extract current version from pyproject.toml
$currentVersionPyproject = ""
if ($pyprojectContent -match 'version\s*=\s*"([^"]+)"') {
    $currentVersionPyproject = $matches[1]
}

# Extract current version from __init__.py
$currentVersionInit = ""
if ($initContent -match '__version__\s*=\s*"([^"]+)"') {
    $currentVersionInit = $matches[1]
}

Write-Host "Current versions:" -ForegroundColor Cyan
Write-Host "  pyproject.toml: $currentVersionPyproject" -ForegroundColor Gray
Write-Host "  __init__.py:    $currentVersionInit" -ForegroundColor Gray
Write-Host ""

# Check if versions match
if ($currentVersionPyproject -ne $currentVersionInit) {
    Write-Host "WARNING: Version mismatch detected!" -ForegroundColor Yellow
    Write-Host "  pyproject.toml: $currentVersionPyproject" -ForegroundColor Yellow
    Write-Host "  __init__.py:    $currentVersionInit" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue with update? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Update pyproject.toml
Write-Host "Updating pyproject.toml..." -ForegroundColor Cyan
$pyprojectContent = $pyprojectContent -replace 'version\s*=\s*"[^"]+"', "version = `"$Version`""
Set-Content -Path $pyprojectFile -Value $pyprojectContent -NoNewline

# Update __init__.py
Write-Host "Updating tapps_agents/__init__.py..." -ForegroundColor Cyan
$initContent = $initContent -replace '__version__\s*=\s*"[^"]+"', "__version__ = `"$Version`""
Set-Content -Path $initFile -Value $initContent -NoNewline

Write-Host ""
Write-Host "=== Version Update Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Updated files:" -ForegroundColor Cyan
Write-Host "  - pyproject.toml" -ForegroundColor Gray
Write-Host "  - tapps_agents/__init__.py" -ForegroundColor Gray
Write-Host ""
Write-Host "New version: $Version" -ForegroundColor Green
Write-Host ""

# Verify updates
$verifyPyproject = Get-Content $pyprojectFile -Raw
$verifyInit = Get-Content $initFile -Raw

$verifyVersionPyproject = ""
if ($verifyPyproject -match 'version\s*=\s*"([^"]+)"') {
    $verifyVersionPyproject = $matches[1]
}

$verifyVersionInit = ""
if ($verifyInit -match '__version__\s*=\s*"([^"]+)"') {
    $verifyVersionInit = $matches[1]
}

if ($verifyVersionPyproject -eq $Version -and $verifyVersionInit -eq $Version) {
    Write-Host "Verification: SUCCESS" -ForegroundColor Green
    Write-Host "  pyproject.toml: $verifyVersionPyproject" -ForegroundColor Gray
    Write-Host "  __init__.py:    $verifyVersionInit" -ForegroundColor Gray
} else {
    Write-Host "WARNING: Verification failed!" -ForegroundColor Yellow
    Write-Host "  pyproject.toml: $verifyVersionPyproject (expected: $Version)" -ForegroundColor Yellow
    Write-Host "  __init__.py:    $verifyVersionInit (expected: $Version)" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review the changes: git diff" -ForegroundColor White
Write-Host "  2. Build packages: python -m build" -ForegroundColor White
Write-Host "  3. Create release: .\scripts\create_github_release.ps1 -Version `"$Version`"" -ForegroundColor White

exit 0

