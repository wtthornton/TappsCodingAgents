#Requires -Version 5.1
<#
.SYNOPSIS
  Set CONTEXT7_API_KEY at User level so Cursor's Context7 MCP server can start.

.DESCRIPTION
  The Context7 MCP server reads CONTEXT7_API_KEY from the environment. Cursor
  spawns it as a subprocess, so the key must be set for the Cursor process
  (User or System) before Cursor starts. This script sets it at User level.

.PARAMETER Key
  Your Context7 API key from https://context7.com

.EXAMPLE
  .\scripts\set_context7_env.ps1 -Key "your-api-key-here"

.EXAMPLE
  .\scripts\set_context7_env.ps1 -Key "ctx7_..."
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Key
)

$Key = $Key.Trim()
if ([string]::IsNullOrWhiteSpace($Key)) {
    Write-Error "Key cannot be empty."
    exit 1
}

[System.Environment]::SetEnvironmentVariable('CONTEXT7_API_KEY', $Key, 'User')
$check = [System.Environment]::GetEnvironmentVariable('CONTEXT7_API_KEY', 'User')
if ($check -eq $Key) {
    Write-Host "[OK] CONTEXT7_API_KEY set at User level." -ForegroundColor Green
} else {
    Write-Host "[WARN] SetEnvironmentVariable returned but verification read differs." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Fully quit Cursor (File > Exit or close all windows)."
Write-Host "  2. Reopen Cursor and open this project."
Write-Host "  3. In Settings > Tools & MCP:"
Write-Host "     - Turn the Playwright toggle ON."
Write-Host "     - Set Browser Automation to On (if you use it)."
Write-Host "  4. Context7 should then start without 'Error - Show Output'."
Write-Host ""
