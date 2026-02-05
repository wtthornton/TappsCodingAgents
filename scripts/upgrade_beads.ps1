#Requires -Version 5.1
<#
.SYNOPSIS
  Download and install Beads (bd) v0.49.0 into tools\bd.

.DESCRIPTION
  Downloads the official Windows AMD64 binary from GitHub releases,
  extracts bd.exe to tools\bd, and optionally runs doctor to verify.
  Use -DryRun to only print what would be done.

.PARAMETER Version
  Beads version to install (default: 0.49.0).

.PARAMETER DryRun
  Print URL and target path only; do not download or overwrite.

.PARAMETER Verify
  After install, run tapps-agents doctor to verify (default: true when not -DryRun).

.EXAMPLE
  .\scripts\upgrade_beads.ps1

.EXAMPLE
  .\scripts\upgrade_beads.ps1 -DryRun
#>
param(
    [string]$Version = "0.49.0",
    [switch]$DryRun,
    [switch]$Verify = $true
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$bdDir = Join-Path $projectRoot "tools\bd"
$bdExe = Join-Path $bdDir "bd.exe"

# Windows AMD64 (adjust if building on ARM64)
$arch = "windows_amd64"
$ext = "zip"
$baseName = "beads_${Version}_${arch}"
$url = "https://github.com/steveyegge/beads/releases/download/v${Version}/${baseName}.${ext}"

if (-not (Test-Path $bdDir)) {
    New-Item -ItemType Directory -Path $bdDir -Force | Out-Null
}

if ($DryRun) {
    Write-Host "Would download: $url"
    Write-Host "Would extract bd.exe to: $bdExe"
    exit 0
}

$tempDir = Join-Path $env:TEMP "beads-upgrade-$Version"
$zipPath = Join-Path $tempDir "$baseName.$ext"

try {
    Write-Host "Downloading Beads v$Version ($arch)..."
    if (-not (Test-Path $tempDir)) { New-Item -ItemType Directory -Path $tempDir -Force | Out-Null }
    Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing

    Write-Host "Extracting..."
    Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force

    # Zip may contain bd.exe at root or in a subfolder
    $extractedExe = Join-Path $tempDir "bd.exe"
    if (-not (Test-Path $extractedExe)) {
        $sub = Get-ChildItem -Path $tempDir -Recurse -Filter "bd.exe" | Select-Object -First 1
        if ($sub) { $extractedExe = $sub.FullName } else { throw "bd.exe not found in archive" }
    }

    $copyDone = $false
    try {
        Copy-Item -Path $extractedExe -Destination $bdExe -Force
        $copyDone = $true
        Write-Host "[OK] Installed bd.exe to $bdDir" -ForegroundColor Green
    } catch [System.IO.IOException] {
        $bdExeNew = Join-Path $bdDir "bd.exe.new"
        Copy-Item -Path $extractedExe -Destination $bdExeNew -Force
        Write-Host "[WARN] bd.exe is in use; new binary saved as bd.exe.new" -ForegroundColor Yellow
        Write-Host "  Close any process using bd (Cursor, terminals), then run:" -ForegroundColor Yellow
        Write-Host "  Remove-Item -Force $bdExe; Move-Item -Force $bdExeNew $bdExe" -ForegroundColor Cyan
    }

    if ($copyDone -and $Verify) {
        Write-Host "Running tapps-agents doctor to verify..."
        & $projectRoot\.venv\Scripts\python.exe -m tapps_agents.cli doctor --format text 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "[WARN] Doctor exited with $LASTEXITCODE" -ForegroundColor Yellow }
    }
} finally {
    if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue }
}
