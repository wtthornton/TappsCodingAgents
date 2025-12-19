# GitHub Release Creation Script
# Creates a GitHub release with built packages attached
# This script:
#   1. Updates version numbers in pyproject.toml and __init__.py
#   2. Cleans previous build artifacts
#   3. Builds distribution packages (sdist + wheel)
#   4. Verifies package contents
#   5. Creates GitHub release with built packages

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
    [switch]$SkipVersionUpdate,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [string]$Repo = "wtthornton/TappsCodingAgents"
)

# Get project root
$projectRoot = $PSScriptRoot | Split-Path -Parent
Set-Location $projectRoot

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
        # Try to extract from CHANGELOG.md
        $changelogFile = Join-Path $projectRoot "CHANGELOG.md"
        if (Test-Path $changelogFile) {
            $changelogContent = Get-Content $changelogFile -Raw
            if ($changelogContent -match "## \[$Version\][\s\S]*?## \[") {
                $ReleaseNotes = $matches[0] -replace "## \[.*?\]", ""
            } elseif ($changelogContent -match "## \[$Version\][\s\S]*$") {
                $ReleaseNotes = $matches[0] -replace "## \[.*?\]", ""
            }
        }
        if (-not $ReleaseNotes -or $ReleaseNotes.Trim() -eq "") {
            $ReleaseNotes = "Release $Tag"
        }
    }
}

Write-Host "=== GitHub Release Creator ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Version: $Version" -ForegroundColor Green
Write-Host "Tag: $Tag" -ForegroundColor Green
Write-Host "Title: $Title" -ForegroundColor Green
Write-Host "Repository: $Repo" -ForegroundColor Green
Write-Host ""

# Step 1: Update version numbers
if (-not $SkipVersionUpdate) {
    Write-Host "Step 1: Updating version numbers..." -ForegroundColor Cyan
    $updateVersionScript = Join-Path $PSScriptRoot "update_version.ps1"
    if (-not (Test-Path $updateVersionScript)) {
        Write-Host "ERROR: update_version.ps1 not found at: $updateVersionScript" -ForegroundColor Red
        exit 1
    }
    
    & $updateVersionScript -Version $Version
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Version update failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "Step 1: Skipping version update (--SkipVersionUpdate)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Clean build artifacts
Write-Host "Step 2: Cleaning build artifacts..." -ForegroundColor Cyan
$buildDirs = @("dist", "build")
$eggInfoDirs = Get-ChildItem -Path $projectRoot -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue

foreach ($dir in $buildDirs) {
    $dirPath = Join-Path $projectRoot $dir
    if (Test-Path $dirPath) {
        Write-Host "  Removing: $dir" -ForegroundColor Gray
        Remove-Item -Path $dirPath -Recurse -Force -ErrorAction SilentlyContinue
    }
}

foreach ($dir in $eggInfoDirs) {
    Write-Host "  Removing: $($dir.Name)" -ForegroundColor Gray
    Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "  Clean complete" -ForegroundColor Green
Write-Host ""

# Step 3: Build distribution packages
if (-not $SkipBuild) {
    Write-Host "Step 3: Building distribution packages..." -ForegroundColor Cyan
    
    # Check for build tool
    $buildAvailable = Get-Command python -ErrorAction SilentlyContinue
    if (-not $buildAvailable) {
        Write-Host "ERROR: Python not found!" -ForegroundColor Red
        exit 1
    }
    
    # Try using 'build' module (recommended)
    $buildModule = python -m build --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Using 'build' module..." -ForegroundColor Gray
        python -m build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Build failed!" -ForegroundColor Red
            exit 1
        }
    } else {
        # Fallback to setuptools
        Write-Host "  Using setuptools (fallback)..." -ForegroundColor Gray
        Write-Host "  WARNING: Consider installing 'build' module: pip install build" -ForegroundColor Yellow
        python setup.py sdist bdist_wheel
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERROR: Build failed!" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "  Build complete" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Step 3: Skipping build (--SkipBuild)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 4: Verify packages exist
Write-Host "Step 4: Verifying packages..." -ForegroundColor Cyan
if (-not (Test-Path "dist")) {
    Write-Host "ERROR: dist/ folder not found after build!" -ForegroundColor Red
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

# Verify we have both sdist and wheel
$sdistFiles = $distFiles | Where-Object { $_.Extension -eq ".gz" -or $_.Name -like "*.tar.gz" }
$wheelFiles = $distFiles | Where-Object { $_.Extension -eq ".whl" }

Write-Host "Files to attach:" -ForegroundColor Green
foreach ($file in $distFiles) {
    $sizeKB = [math]::Round($file.Length/1KB, 2)
    Write-Host "  - $($file.Name) ($sizeKB KB)" -ForegroundColor Gray
}

if ($sdistFiles.Count -eq 0) {
    Write-Host "WARNING: No source distribution (.tar.gz) found" -ForegroundColor Yellow
}
if ($wheelFiles.Count -eq 0) {
    Write-Host "WARNING: No wheel distribution (.whl) found" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Verify package contents (optional verification script)
$verifyScript = Join-Path $PSScriptRoot "verify_release_package.ps1"
if (Test-Path $verifyScript) {
    Write-Host "Step 5: Verifying package contents..." -ForegroundColor Cyan
    & $verifyScript -PackagePath $distFiles[0].FullName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Package verification found issues (continuing anyway)" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Step 6: Create GitHub release
Write-Host "Step 6: Creating GitHub release..." -ForegroundColor Cyan

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
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Verify the release on GitHub" -ForegroundColor White
        Write-Host "  2. Test installation: pip install tapps-agents==$Version" -ForegroundColor White
        Write-Host "  3. Update CHANGELOG.md if not already done" -ForegroundColor White
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

