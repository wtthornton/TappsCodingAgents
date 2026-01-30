# PyPI Upload Script for TappsCodingAgents
# This script automates the upload process.
# Best practice (Context7 / python-dotenv): store token in .env (gitignored); see .env.example.

param(
    [Parameter(Mandatory=$false)]
    [string]$Token,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("pypi", "testpypi")]
    [string]$Repository = "testpypi",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipExisting,
    
    [Parameter(Mandatory=$false)]
    [switch]$ShowVerbose
)

Write-Host "=== PyPI Upload Script ===" -ForegroundColor Cyan
Write-Host ""

# Load .env if present (best practice: keep secrets out of repo; .env is gitignored)
$projectRoot = $PSScriptRoot | Split-Path -Parent
$envFile = Join-Path $projectRoot ".env"
if (-not (Test-Path $envFile) -and (Test-Path ".env")) { $envFile = (Get-Item ".env").FullName }
if (-not $Token -and -not $env:TWINE_PASSWORD -and (Test-Path $envFile)) {
    Get-Content $envFile -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            $key = $matches[1]
            $val = $matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "TWINE_PASSWORD" -or $key -eq "PYPI_API_TOKEN" -or $key -eq "PYPI_TOKEN") {
                Set-Item -Path "Env:$key" -Value $val -ErrorAction SilentlyContinue
            }
        }
    }
    if ($env:PYPI_API_TOKEN -and -not $env:TWINE_PASSWORD) { $env:TWINE_PASSWORD = $env:PYPI_API_TOKEN }
    if ($env:PYPI_TOKEN -and -not $env:TWINE_PASSWORD) { $env:TWINE_PASSWORD = $env:PYPI_TOKEN }
    if ($env:TWINE_PASSWORD) { Write-Host "Using token from .env ($envFile)" -ForegroundColor Green }
    elseif (Test-Path $envFile) { Write-Host "No TWINE_PASSWORD, PYPI_API_TOKEN, or PYPI_TOKEN in .env - add one (see .env.example)" -ForegroundColor Yellow }
}

# Check if dist folder exists and has files
if (-not (Test-Path "dist")) {
    Write-Host "ERROR: dist/ folder not found!" -ForegroundColor Red
    Write-Host "Run 'python setup.py sdist bdist_wheel' first to build packages." -ForegroundColor Yellow
    exit 1
}

$distFiles = Get-ChildItem -Path "dist" -File
if ($distFiles.Count -eq 0) {
    Write-Host "ERROR: No files found in dist/ folder!" -ForegroundColor Red
    Write-Host "Run 'python setup.py sdist bdist_wheel' first to build packages." -ForegroundColor Yellow
    exit 1
}

Write-Host "Found $($distFiles.Count) file(s) to upload:" -ForegroundColor Green
foreach ($file in $distFiles) {
    Write-Host "  - $($file.Name)" -ForegroundColor Gray
}
Write-Host ""

# Get token if not provided
if (-not $Token) {
    # Check environment variable first
    if ($env:TWINE_PASSWORD) {
        Write-Host "Using token from TWINE_PASSWORD environment variable" -ForegroundColor Green
        $Token = $env:TWINE_PASSWORD
    } else {
        Write-Host "PyPI API Token required." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Get your token from:" -ForegroundColor Cyan
        if ($Repository -eq "testpypi") {
            Write-Host "  https://test.pypi.org/manage/account/token/" -ForegroundColor White
        } else {
            Write-Host "  https://pypi.org/manage/account/token/" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "Then run:" -ForegroundColor Cyan
        Write-Host "  .\upload_to_pypi.ps1 -Token 'pypi-your-token-here'" -ForegroundColor White
        Write-Host ""
        Write-Host "OR set environment variable:" -ForegroundColor Cyan
        Write-Host "  `$env:TWINE_PASSWORD = 'pypi-your-token-here'" -ForegroundColor White
        Write-Host "  .\upload_to_pypi.ps1" -ForegroundColor White
        exit 1
    }
}

# Validate token format
if (-not $Token.StartsWith("pypi-")) {
    Write-Host "WARNING: Token should start with 'pypi-'. Continuing anyway..." -ForegroundColor Yellow
}

# Set environment variable for twine
$env:TWINE_PASSWORD = $Token

# Only upload package files (.whl and .tar.gz), not subdirs like dist/backup
$packageFiles = $distFiles | Where-Object { $_.Extension -eq ".whl" -or $_.Name -like "*.tar.gz" }
if ($packageFiles.Count -eq 0) {
    Write-Host "ERROR: No .whl or .tar.gz files in dist/" -ForegroundColor Red
    exit 1
}

# Build command
$uploadCmd = "python -m twine upload"
if ($Repository -eq "testpypi") {
    $uploadCmd += " --repository testpypi"
}
if ($SkipExisting) {
    $uploadCmd += " --skip-existing"
}
if ($ShowVerbose) {
    $uploadCmd += " --verbose"
}
$uploadCmd += " " + ($packageFiles.FullName -join " ")

Write-Host ""
Write-Host "Uploading to: $Repository" -ForegroundColor Cyan
Write-Host "Command: $uploadCmd" -ForegroundColor Gray
Write-Host ""

$twineArgs = @()
if ($Repository -eq "testpypi") { $twineArgs += "--repository", "testpypi" }
if ($SkipExisting) { $twineArgs += "--skip-existing" }
if ($ShowVerbose) { $twineArgs += "--verbose" }
$twineArgs += $packageFiles.FullName

# Execute upload
try {
    & python -m twine upload @twineArgs
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=== Upload Successful! ===" -ForegroundColor Green
        if ($Repository -eq "testpypi") {
            Write-Host ""
            Write-Host "Test installation with:" -ForegroundColor Cyan
            Write-Host "  pip install -i https://test.pypi.org/simple/ tapps-agents" -ForegroundColor White
        }
    } else {
        Write-Host ""
        Write-Host "=== Upload Failed ===" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Clear token from environment (security)
    Remove-Item Env:\TWINE_PASSWORD -ErrorAction SilentlyContinue
}

