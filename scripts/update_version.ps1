# Version Update Script
# Updates version number in pyproject.toml, tapps_agents/__init__.py, and all documentation files

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDocs = $false
)

# Set error action preference
$ErrorActionPreference = 'Stop'

Write-Host "=== Version Update Script ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Updating version to: $Version" -ForegroundColor Green
if ($SkipDocs) {
    Write-Host "Skipping documentation updates (core files only)" -ForegroundColor Yellow
}
Write-Host ""

# Get current directory (should be project root)
$projectRoot = $PSScriptRoot | Split-Path -Parent
Set-Location $projectRoot

# Core files to update
$pyprojectFile = Join-Path $projectRoot "pyproject.toml"
$initFile = Join-Path $projectRoot "tapps_agents\__init__.py"

# Verify core files exist
try {
    if (-not (Test-Path $pyprojectFile)) {
        Write-Error -Message "pyproject.toml not found at: $pyprojectFile" `
            -Category ObjectNotFound `
            -ErrorId "FileNotFound" `
            -TargetObject $pyprojectFile
    }

    if (-not (Test-Path $initFile)) {
        Write-Error -Message "tapps_agents/__init__.py not found at: $initFile" `
            -Category ObjectNotFound `
            -ErrorId "FileNotFound" `
            -TargetObject $initFile
    }
} catch {
    Write-Error -Message "Failed to verify core files: $_" `
        -Category InvalidOperation `
        -ErrorId "FileVerificationFailed"
    exit 1
}

# Read current versions
try {
    $pyprojectContent = Get-Content $pyprojectFile -Raw -ErrorAction Stop
    $initContent = Get-Content $initFile -Raw -ErrorAction Stop
} catch {
    Write-Error -Message "Failed to read version files: $_" `
        -Category ReadError `
        -ErrorId "FileReadError" `
        -TargetObject $_.TargetObject
    exit 1
}

# Extract current version from pyproject.toml [project] section only
$currentVersionPyproject = ""
$pyprojectLines = $pyprojectContent -split "`r?`n"
$inProjectSection = $false
foreach ($line in $pyprojectLines) {
    if ($line -match '^\s*\[project\]\s*$') {
        $inProjectSection = $true
    } elseif ($line -match '^\s*\[.*?\]\s*$') {
        $inProjectSection = $false
    } elseif ($inProjectSection -and $line -match '^\s*version\s*=\s*"(.*?)"\s*$') {
        $currentVersionPyproject = $matches[1]
        break
    }
}

# Extract current version from __init__.py
$currentVersionInit = ""
$versionPattern2 = '__version__\s*=\s*"(.*?)"'
if ($initContent -match $versionPattern2) {
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
try {
    Write-Host "Updating pyproject.toml..." -ForegroundColor Cyan
    # Only update version in [project] section to avoid updating tool config versions
    # Process line by line, tracking when we're in [project] section
    $lines = $pyprojectContent -split "`r?`n"
    $inProjectSection = $false
    $updated = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s*\[project\]\s*$') {
            $inProjectSection = $true
        } elseif ($lines[$i] -match '^\s*\[.*?\]\s*$') {
            # We've entered a new section, so we're no longer in [project] section
            $inProjectSection = $false
        } elseif ($inProjectSection -and $lines[$i] -match '^(\s*)version\s*=\s*".*?"(\s*)$') {
            # This is the version line in [project] section (not target-version or python_version)
            $lines[$i] = $lines[$i] -replace 'version\s*=\s*".*?"', "version = `"$Version`""
            $updated = $true
        }
    }
    if (-not $updated) {
        Write-Warning "Warning: Could not find version in [project] section to update"
    }
    $pyprojectContent = $lines -join "`n"
    Set-Content -Path $pyprojectFile -Value $pyprojectContent -NoNewline -ErrorAction Stop
} catch {
    Write-Error -Message "Failed to update pyproject.toml: $_" `
        -Category WriteError `
        -ErrorId "FileUpdateError" `
        -TargetObject $pyprojectFile
    exit 1
}

# Update __init__.py
try {
    Write-Host "Updating tapps_agents/__init__.py..." -ForegroundColor Cyan
    $replacePattern2 = '__version__\s*=\s*".*?"'
    $replaceValue2 = "__version__ = `"$Version`""
    $initContent = $initContent -replace $replacePattern2, $replaceValue2
    Set-Content -Path $initFile -Value $initContent -NoNewline -ErrorAction Stop
} catch {
    Write-Error -Message "Failed to update __init__.py: $_" `
        -Category WriteError `
        -ErrorId "FileUpdateError" `
        -TargetObject $initFile
    exit 1
}

$updatedFiles = @("pyproject.toml", "tapps_agents/__init__.py")

# Update documentation files if not skipped
if (-not $SkipDocs) {
    Write-Host ""
    Write-Host "Updating documentation files..." -ForegroundColor Cyan
    
    # Define documentation files and their update patterns
    $docFiles = @(
        @{
            Path = "README.md"
            Patterns = @(
                @{ Pattern = '\[!\[Version\]\(https://img\.shields\.io/badge/version-([\d\.]+)-blue\.svg\)\]'; Replacement = "[![Version](https://img.shields.io/badge/version-$Version-blue.svg)]" }
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "PROJECT_ANALYSIS_2026.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "docs/ARCHITECTURE.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "docs/API.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "docs/DEPLOYMENT.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "docs/TROUBLESHOOTING.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "docs/RUNBOOKS.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "docs/QUICK_START_OPTIMIZATIONS.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)\+'; Replacement = "**Version**: $Version+" }
            )
        },
        @{
            Path = "docs/HARDWARE_RECOMMENDATIONS.md"
            Patterns = @(
                @{ Pattern = '\*\*Project Version\*\*:\s*([\d\.]+)'; Replacement = "**Project Version**: $Version" }
            )
        },
        @{
            Path = "docs/README.md"
            Patterns = @(
                @{ Pattern = '\*\*Documentation Version\*\*:\s*([\d\.]+)'; Replacement = "**Documentation Version**: $Version" }
            )
        },
        @{
            Path = "docs/PROJECT_CONTEXT.md"
            Patterns = @(
                @{ Pattern = '\*\*Framework version\*\*:\s*([\d\.]+)'; Replacement = "**Framework version**: $Version" }
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        },
        @{
            Path = "requirements/TECH_STACK.md"
            Patterns = @(
                @{ Pattern = '\*\*Version\*\*:\s*([\d\.]+)'; Replacement = "**Version**: $Version" }
            )
        }
    )
    
    # Update JSON metadata files
    $jsonFiles = @(
        @{
            Path = "implementation/IMPROVEMENT_PLAN.json"
            Pattern = '"version"\s*:\s*"([\d\.]+)"'
            Replacement = '"version": "' + $Version + '"'
        }
    )
    
    foreach ($jsonFile in $jsonFiles) {
        $filePath = Join-Path $projectRoot $jsonFile.Path
        if (Test-Path $filePath) {
            $content = Get-Content $filePath -Raw
            if ($content -match $jsonFile.Pattern) {
                try {
                    $content = $content -replace $jsonFile.Pattern, $jsonFile.Replacement
                    Set-Content -Path $filePath -Value $content -NoNewline -ErrorAction Stop
                    $updatedFiles += $jsonFile.Path
                    Write-Host "  ✓ Updated: $($jsonFile.Path)" -ForegroundColor Gray
                } catch {
                    Write-Warning "Failed to update $($jsonFile.Path): $_"
                }
            }
        } else {
            Write-Host "  ⚠ Skipped (not found): $($jsonFile.Path)" -ForegroundColor Yellow
        }
    }
    
    foreach ($docFile in $docFiles) {
        $filePath = Join-Path $projectRoot $docFile.Path
        if (Test-Path $filePath) {
            $content = Get-Content $filePath -Raw
            $originalContent = $content
            $updated = $false
            
            foreach ($patternInfo in $docFile.Patterns) {
                if ($content -match $patternInfo.Pattern) {
                    $content = $content -replace $patternInfo.Pattern, $patternInfo.Replacement
                    $updated = $true
                }
            }
            
            if ($updated) {
                try {
                    Set-Content -Path $filePath -Value $content -NoNewline -ErrorAction Stop
                    $updatedFiles += $docFile.Path
                    Write-Host "  ✓ Updated: $($docFile.Path)" -ForegroundColor Gray
                } catch {
                    Write-Warning "Failed to update $($docFile.Path): $_"
                }
            }
        } else {
            Write-Host "  ⚠ Skipped (not found): $($docFile.Path)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=== Version Update Complete ===" -ForegroundColor Green
Write-Host ""
$fileCount = $updatedFiles.Count
Write-Host "Updated files: $fileCount total" -ForegroundColor Cyan
foreach ($file in $updatedFiles) {
    Write-Host "  - $file" -ForegroundColor Gray
}
Write-Host ""
Write-Host "New version: $Version" -ForegroundColor Green
Write-Host ""

# Verify core file updates
$verifyPyproject = Get-Content $pyprojectFile -Raw
$verifyInit = Get-Content $initFile -Raw

$verifyVersionPyproject = ""
# Only match version in [project] section for verification
$verifyLines = $verifyPyproject -split "`r?`n"
$inProjectSection = $false
foreach ($line in $verifyLines) {
    if ($line -match '^\s*\[project\]\s*$') {
        $inProjectSection = $true
    } elseif ($line -match '^\s*\[.*?\]\s*$') {
        $inProjectSection = $false
    } elseif ($inProjectSection -and $line -match '^\s*version\s*=\s*"(.*?)"\s*$') {
        $verifyVersionPyproject = $matches[1]
        break
    }
}

$verifyVersionInit = ""
$verifyInitPattern = '__version__\s*=\s*"(.*?)"'
if ($verifyInit -match $verifyInitPattern) {
    $verifyVersionInit = $matches[1]
}

if ($verifyVersionPyproject -eq $Version -and $verifyVersionInit -eq $Version) {
    Write-Host "Verification: SUCCESS" -ForegroundColor Green
    Write-Host "  pyproject.toml: $verifyVersionPyproject" -ForegroundColor Gray
    Write-Host "  __init__.py:    $verifyVersionInit" -ForegroundColor Gray
} else {
    Write-Error -Message "Verification failed! Version mismatch detected." `
        -Category InvalidResult `
        -ErrorId "VerificationFailed" `
        -RecommendedAction "Check that version updates were applied correctly. pyproject.toml: $verifyVersionPyproject (expected: $Version), __init__.py: $verifyVersionInit (expected: $Version)"
    exit 1
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review the changes: git diff" -ForegroundColor White
Write-Host "  2. Update CHANGELOG.md with release notes for version $Version" -ForegroundColor White
Write-Host "  3. Build packages: python -m build" -ForegroundColor White
$releaseCmd = '.\scripts\create_github_release.ps1 -Version ' + $Version
Write-Host "  4. Create release: $releaseCmd" -ForegroundColor White

exit 0
