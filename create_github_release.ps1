# GitHub Release Creation Script
# Creates a GitHub release with built packages attached

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Tag = $null,
    
    [Parameter(Mandatory=$false)]
    [string]$Title = $null,
    
    [Parameter(Mandatory=$false)]
    [string]$ReleaseNotes = $null,
    
    [Parameter(Mandatory=$false)]
    [switch]$Draft,
    
    [Parameter(Mandatory=$false)]
    [switch]$Prerelease,
    
    [Parameter(Mandatory=$false)]
    [string]$Repo = "wtthornton/TappsCodingAgents"
)

# Set defaults
if (-not $Tag) {
    $Tag = "v$Version"
}
if (-not $Title) {
    $Title = "Release $Tag"
}
if (-not $ReleaseNotes) {
    $ReleaseNotesFile = "RELEASE_NOTES_v$Version.md"
    if (Test-Path $ReleaseNotesFile) {
        $ReleaseNotes = Get-Content $ReleaseNotesFile -Raw
    } else {
        $ReleaseNotes = "Release $Tag"
    }
}

Write-Host "=== GitHub Release Creator ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Version: $Version" -ForegroundColor Green
Write-Host "Tag: $Tag" -ForegroundColor Green
Write-Host "Title: $Title" -ForegroundColor Green
Write-Host "Repository: $Repo" -ForegroundColor Green
Write-Host ""

# Check if dist folder exists
if (-not (Test-Path "dist")) {
    Write-Host "ERROR: dist/ folder not found!" -ForegroundColor Red
    Write-Host "Run 'python setup.py sdist bdist_wheel' first to build packages." -ForegroundColor Yellow
    exit 1
}

$distFiles = Get-ChildItem -Path "dist" -File | Where-Object { $_.Name -like "*$Version*" }
if ($distFiles.Count -eq 0) {
    Write-Host "WARNING: No files found in dist/ matching version $Version" -ForegroundColor Yellow
    Write-Host "Files in dist/:" -ForegroundColor Gray
    Get-ChildItem -Path "dist" -File | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
    $distFiles = Get-ChildItem -Path "dist" -File
}

Write-Host "Files to attach:" -ForegroundColor Green
foreach ($file in $distFiles) {
    Write-Host "  - $($file.Name) ($([math]::Round($file.Length/1KB, 2)) KB)" -ForegroundColor Gray
}
Write-Host ""

# Check for GitHub CLI
$ghAvailable = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghAvailable) {
    Write-Host "GitHub CLI (gh) not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install GitHub CLI:" -ForegroundColor Yellow
    Write-Host "  winget install --id GitHub.cli" -ForegroundColor White
    Write-Host "  OR download from: https://cli.github.com/" -ForegroundColor White
    Write-Host ""
    Write-Host "After installation, authenticate:" -ForegroundColor Yellow
    Write-Host "  gh auth login" -ForegroundColor White
    Write-Host ""
    Write-Host "Alternative: Use GitHub web interface or API directly" -ForegroundColor Cyan
    exit 1
}

# Check authentication
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not authenticated with GitHub!" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

Write-Host "Creating release..." -ForegroundColor Cyan

# Build gh release create command
$releaseCmd = "gh release create $Tag"
$releaseCmd += " --title `"$Title`""
$releaseCmd += " --notes `"$ReleaseNotes`""

if ($Draft) {
    $releaseCmd += " --draft"
}
if ($Prerelease) {
    $releaseCmd += " --prerelease"
}

# Add files
foreach ($file in $distFiles) {
    $releaseCmd += " `"dist/$($file.Name)`""
}

Write-Host "Command: $releaseCmd" -ForegroundColor Gray
Write-Host ""

# Execute
try {
    Invoke-Expression $releaseCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=== Release Created Successfully! ===" -ForegroundColor Green
        Write-Host ""
        Write-Host "View release at:" -ForegroundColor Cyan
        Write-Host "  https://github.com/$Repo/releases/tag/$Tag" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "=== Release Creation Failed ===" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

