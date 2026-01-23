# Load MCP API Keys from Encrypted Storage
# Run this script before starting Cursor, or add it to your PowerShell profile

$ErrorActionPreference = "Stop"

# Get project root (assuming script is in scripts/)
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Set PYTHONPATH if needed
$env:PYTHONPATH = "$ProjectRoot"

# Load keys using Python
$context7_key = python -c "import sys; sys.path.insert(0, '$ProjectRoot'); from tapps_agents.context7.security import APIKeyManager; from pathlib import Path; km = APIKeyManager(Path('$ProjectRoot') / '.tapps-agents'); key = km.load_api_key('context7'); print(key if key else '')" 2>$null
if ($context7_key) {
    $env:CONTEXT7_API_KEY = $context7_key
    Write-Host "[OK] Loaded Context7 API key" -ForegroundColor Green
}

$github_key = python -c "import sys; sys.path.insert(0, '$ProjectRoot'); from tapps_agents.context7.security import APIKeyManager; from pathlib import Path; km = APIKeyManager(Path('$ProjectRoot') / '.tapps-agents'); key = km.load_api_key('github'); print(key if key else '')" 2>$null
if ($github_key) {
    $env:GITHUB_PERSONAL_ACCESS_TOKEN = $github_key
    Write-Host "[OK] Loaded GitHub API key" -ForegroundColor Green
}

Write-Host ""
Write-Host "Environment variables set. You can now start Cursor." -ForegroundColor Cyan
Write-Host "To make this permanent, add this script to your PowerShell profile:" -ForegroundColor Yellow
Write-Host "  . $ps_script" -ForegroundColor Yellow
