# Release Readiness Validation Script
# Validates that the project is ready for release before creating a tag

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "=== Release Readiness Validation ===" -ForegroundColor Cyan
Write-Host ""

# Get project root
$projectRoot = $PSScriptRoot | Split-Path -Parent
Set-Location $projectRoot

$errors = @()
$warnings = @()

# 1. Verify version format
Write-Host "1. Validating version format..." -ForegroundColor Cyan
$versionPattern = '^\d+\.\d+\.\d+$'
if ($Version -notmatch $versionPattern) {
    $errors += "Invalid version format. Expected X.Y.Z (e.g., 3.0.2)"
    Write-Host "  ❌ Invalid version format" -ForegroundColor Red
} else {
    Write-Host "  ✅ Version format valid" -ForegroundColor Green
}

# 2. Check version consistency
Write-Host "2. Checking version consistency..." -ForegroundColor Cyan
$pyprojectFile = Join-Path $projectRoot "pyproject.toml"
$initFile = Join-Path $projectRoot "tapps_agents\__init__.py"

if (-not (Test-Path $pyprojectFile)) {
    $errors += "pyproject.toml not found"
    Write-Host "  ❌ pyproject.toml not found" -ForegroundColor Red
} else {
    $pyprojectContent = Get-Content $pyprojectFile -Raw
    if ($pyprojectContent -match 'version\s*=\s*"(.*?)"') {
        $pyprojectVersion = $matches[1]
        if ($pyprojectVersion -eq $Version) {
            Write-Host "  ✅ pyproject.toml version matches" -ForegroundColor Green
        } else {
            $errors += "pyproject.toml version mismatch: $pyprojectVersion (expected: $Version)"
            Write-Host "  ❌ pyproject.toml version mismatch: $pyprojectVersion" -ForegroundColor Red
        }
    }
}

if (-not (Test-Path $initFile)) {
    $errors += "tapps_agents/__init__.py not found"
    Write-Host "  ❌ __init__.py not found" -ForegroundColor Red
} else {
    $initContent = Get-Content $initFile -Raw
    if ($initContent -match '__version__\s*=\s*"(.*?)"') {
        $initVersion = $matches[1]
        if ($initVersion -eq $Version) {
            Write-Host "  ✅ __init__.py version matches" -ForegroundColor Green
        } else {
            $errors += "__init__.py version mismatch: $initVersion (expected: $Version)"
            Write-Host "  ❌ __init__.py version mismatch: $initVersion" -ForegroundColor Red
        }
    }
}

# 3. Check CHANGELOG.md
Write-Host "3. Checking CHANGELOG.md..." -ForegroundColor Cyan
$changelogFile = Join-Path $projectRoot "CHANGELOG.md"
if (Test-Path $changelogFile) {
    $changelogContent = Get-Content $changelogFile -Raw
    if ($changelogContent -match "## \[$Version\]") {
        Write-Host "  ✅ CHANGELOG.md contains version $Version" -ForegroundColor Green
    } else {
        $warnings += "CHANGELOG.md does not contain section for version $Version"
        Write-Host "  ⚠️  CHANGELOG.md missing section for version $Version" -ForegroundColor Yellow
    }
} else {
    $warnings += "CHANGELOG.md not found"
    Write-Host "  ⚠️  CHANGELOG.md not found" -ForegroundColor Yellow
}

# 4. Check for uncommitted changes
Write-Host "4. Checking git status..." -ForegroundColor Cyan
$gitStatus = git status --porcelain 2>&1
if ($LASTEXITCODE -eq 0) {
    if ($gitStatus) {
        $warnings += "Uncommitted changes detected. Consider committing before release."
        Write-Host "  ⚠️  Uncommitted changes detected" -ForegroundColor Yellow
        Write-Host "     Run 'git status' to see changes" -ForegroundColor Gray
    } else {
        Write-Host "  ✅ No uncommitted changes" -ForegroundColor Green
    }
} else {
    $warnings += "Could not check git status (not a git repository?)"
    Write-Host "  ⚠️  Could not check git status" -ForegroundColor Yellow
}

# 5. Check if tag already exists
Write-Host "5. Checking for existing tag..." -ForegroundColor Cyan
$tag = "v$Version"
$tagExists = git tag -l $tag 2>&1
if ($LASTEXITCODE -eq 0 -and $tagExists) {
    $errors += "Tag $tag already exists. Delete it first or use a different version."
    Write-Host "  ❌ Tag $tag already exists" -ForegroundColor Red
} else {
    Write-Host "  ✅ Tag $tag does not exist" -ForegroundColor Green
}

# 6. Check if release already exists (requires gh CLI)
Write-Host "6. Checking for existing GitHub release..." -ForegroundColor Cyan
$ghAvailable = Get-Command gh -ErrorAction SilentlyContinue
if ($ghAvailable) {
    $authStatus = gh auth status 2>&1
    if ($LASTEXITCODE -eq 0) {
        $releaseExists = gh release view $tag 2>&1
        if ($LASTEXITCODE -eq 0) {
            $warnings += "GitHub release $tag already exists"
            Write-Host "  ⚠️  GitHub release $tag already exists" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ GitHub release $tag does not exist" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠️  GitHub CLI not authenticated (skipping release check)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  GitHub CLI not installed (skipping release check)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Validation Summary ===" -ForegroundColor Cyan
Write-Host ""

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ All checks passed! Ready for release." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Commit any pending changes" -ForegroundColor White
    Write-Host "  2. Create tag: git tag v$Version" -ForegroundColor White
    Write-Host "  3. Push tag: git push origin v$Version" -ForegroundColor White
    Write-Host "  4. GitHub Actions will automatically create the release" -ForegroundColor White
    exit 0
} else {
    if ($errors.Count -gt 0) {
        Write-Host "❌ ERRORS FOUND ($($errors.Count)):" -ForegroundColor Red
        foreach ($err in $errors) {
            Write-Host "  - $err" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "⚠️  WARNINGS ($($warnings.Count)):" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $warning" -ForegroundColor Gray
        }
        Write-Host ""
    }
    
    if ($errors.Count -gt 0) {
        Write-Host "❌ Release validation FAILED. Fix errors before proceeding." -ForegroundColor Red
        exit 1
    } else {
        Write-Host "⚠️  Release validation passed with warnings." -ForegroundColor Yellow
        Write-Host "   Review warnings and proceed if acceptable." -ForegroundColor Gray
        exit 0
    }
}

