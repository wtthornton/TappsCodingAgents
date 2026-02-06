# Package Verification Script
# Verifies that release packages contain only runtime files

param(
    [Parameter(Mandatory=$true)]
    [string]$PackagePath
)

Write-Host "=== Package Verification ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Package: $PackagePath" -ForegroundColor Green
Write-Host ""

# Verify package exists
if (-not (Test-Path $PackagePath)) {
    Write-Host "ERROR: Package not found: $PackagePath" -ForegroundColor Red
    exit 1
}

# Determine package type
$packageType = "unknown"
if ($PackagePath -like "*.whl") {
    $packageType = "wheel"
} elseif ($PackagePath -like "*.tar.gz" -or $PackagePath -like "*.tgz") {
    $packageType = "sdist"
} else {
    Write-Host "WARNING: Unknown package type. Expected .whl or .tar.gz" -ForegroundColor Yellow
}

Write-Host "Package type: $packageType" -ForegroundColor Cyan
Write-Host ""

# Create temporary extraction directory
$tempDir = Join-Path $env:TEMP "tapps_verify_$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

try {
    Write-Host "Extracting package..." -ForegroundColor Cyan
    
    if ($packageType -eq "wheel") {
        # Wheels are ZIP files, but PowerShell doesn't recognize .whl extension
        # Copy to .zip temporarily for extraction
        $zipPath = Join-Path $tempDir "package.zip"
        Copy-Item -Path $PackagePath -Destination $zipPath -Force
        Expand-Archive -Path $zipPath -DestinationPath $tempDir -Force
        Remove-Item -Path $zipPath -Force
        $extractRoot = $tempDir
    } elseif ($packageType -eq "sdist") {
        # Source distributions are tar.gz
        # Use tar if available (Windows 10+)
        $tarAvailable = Get-Command tar -ErrorAction SilentlyContinue
        if ($tarAvailable) {
            New-Item -ItemType Directory -Path "$tempDir\extract" -Force | Out-Null
            tar -xzf $PackagePath -C "$tempDir\extract"
            $extractRoot = "$tempDir\extract"
            # Find the actual package directory (usually tapps-agents-X.Y.Z)
            $packageDirs = Get-ChildItem -Path $extractRoot -Directory
            if ($packageDirs.Count -eq 1) {
                $extractRoot = $packageDirs[0].FullName
            }
        } else {
            Write-Host "ERROR: 'tar' command not available. Cannot extract .tar.gz on this system." -ForegroundColor Red
            Write-Host "Install 7-Zip or use a system with tar support." -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "ERROR: Cannot extract unknown package type" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Extracted to: $extractRoot" -ForegroundColor Gray
    Write-Host ""
    
    # Define required files/directories
    $requiredItems = @(
        "tapps_agents",
        "pyproject.toml"
    )
    
    # Define excluded patterns (should NOT be in package)
    $excludedPatterns = @(
        "tests\*",
        "docs\*",
        "examples\*",
        "scripts\*",
        "workflows\*",
        "requirements\*",
        "templates\*",
        ".claude\*",
        ".cursor\*",
        ".bmad-core\*",
        ".git\*",
        ".github\*",
        ".tapps-agents\*",
        "billstest\*",
        "reports\*",
        "htmlcov\*",
        ".pytest_cache\*",
        ".mypy_cache\*",
        ".ruff_cache\*",
        "*.egg-info\*",
        "build\*",
        "dist\*",
        ".cursorignore",
        ".cursorrules",
        ".env",
        ".env.*",
        ".gitignore"
    )
    
    # Check required items
    Write-Host "Checking required files/directories..." -ForegroundColor Cyan
    $missingItems = @()
    foreach ($item in $requiredItems) {
        $itemPath = Join-Path $extractRoot $item
        if (-not (Test-Path $itemPath)) {
            $missingItems += $item
            Write-Host "  MISSING: $item" -ForegroundColor Red
        } else {
            Write-Host "  FOUND:   $item" -ForegroundColor Green
        }
    }
    
    if ($missingItems.Count -gt 0) {
        Write-Host ""
        Write-Host "ERROR: Required items missing from package!" -ForegroundColor Red
        Write-Host "Missing: $($missingItems -join ', ')" -ForegroundColor Yellow
    }
    
    Write-Host ""
    
    # Check for excluded items
    Write-Host "Checking for excluded files/directories..." -ForegroundColor Cyan
    $foundExcluded = @()
    
    foreach ($pattern in $excludedPatterns) {
        $searchPath = Join-Path $extractRoot ($pattern -replace '\\', '\')
        $matches = Get-ChildItem -Path $extractRoot -Recurse -ErrorAction SilentlyContinue | 
            Where-Object { $_.FullName -like "*$($pattern -replace '\*', '*')*" }
        
        if ($matches) {
            foreach ($match in $matches) {
                $relativePath = $match.FullName.Replace($extractRoot, "").TrimStart('\')
                $foundExcluded += $relativePath
                Write-Host "  EXCLUDED FOUND: $relativePath" -ForegroundColor Yellow
            }
        }
    }
    
    # Also check for common excluded directory names
    $excludedDirs = @("tests", "docs", "examples", "scripts", "workflows", "requirements", 
                      "templates", ".claude", ".cursor", ".bmad-core", 
                      ".git", ".github", ".tapps-agents", "billstest", "reports", "htmlcov", 
                      ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist")
    
    foreach ($dir in $excludedDirs) {
        $dirPath = Join-Path $extractRoot $dir
        if (Test-Path $dirPath) {
            $relativePath = $dirPath.Replace($extractRoot, "").TrimStart('\')
            if ($foundExcluded -notcontains $relativePath) {
                $foundExcluded += $relativePath
                Write-Host "  EXCLUDED FOUND: $relativePath" -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host ""
    
    # Check for tapps_agents/resources (should be included)
    $resourcesPath = Join-Path $extractRoot "tapps_agents\resources"
    if (Test-Path $resourcesPath) {
        Write-Host "  FOUND:   tapps_agents/resources (required for runtime)" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: tapps_agents/resources (required for runtime)" -ForegroundColor Red
        $missingItems += "tapps_agents/resources"
    }
    
    Write-Host ""
    
    # Summary
    Write-Host "=== Verification Summary ===" -ForegroundColor Cyan
    Write-Host ""
    
    if ($missingItems.Count -eq 0 -and $foundExcluded.Count -eq 0) {
        Write-Host "RESULT: PASS" -ForegroundColor Green
        Write-Host ""
        Write-Host "Package contains:" -ForegroundColor Green
        Write-Host "  - All required runtime files" -ForegroundColor Gray
        Write-Host "  - No excluded development files" -ForegroundColor Gray
        Write-Host "  - Resources directory included" -ForegroundColor Gray
        exit 0
    } else {
        Write-Host "RESULT: FAIL" -ForegroundColor Red
        Write-Host ""
        
        if ($missingItems.Count -gt 0) {
            Write-Host "Missing required items:" -ForegroundColor Red
            foreach ($item in $missingItems) {
                Write-Host "  - $item" -ForegroundColor Yellow
            }
            Write-Host ""
        }
        
        if ($foundExcluded.Count -gt 0) {
            Write-Host "Found excluded items:" -ForegroundColor Red
            foreach ($item in $foundExcluded) {
                Write-Host "  - $item" -ForegroundColor Yellow
            }
            Write-Host ""
        }
        
        Write-Host "Review MANIFEST.in and RELEASE_INCLUDES.md for correct inclusion/exclusion rules." -ForegroundColor Yellow
        exit 1
    }
    
} finally {
    # Cleanup
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

