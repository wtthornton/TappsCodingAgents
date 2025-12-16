# Billstest Setup Verification Script
# Run this script to verify the TappsCodingAgents project is ready for testing

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Billstest Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# 1. Check Python version
Write-Host "[1/8] Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
    if ($pythonVersion -notmatch "Python 3\.(1[3-9]|[2-9][0-9])") {
        Write-Host "  ⚠ Warning: Python 3.13+ recommended" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "  ✗ Python not found!" -ForegroundColor Red
    $errors++
}

# 2. Check framework installation
Write-Host "[2/8] Checking TappsCodingAgents framework..." -ForegroundColor Yellow
try {
    $version = python -c "import tapps_agents; print(tapps_agents.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Framework installed: $version" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Framework not installed!" -ForegroundColor Red
        Write-Host "    Run: pip install -e . (from root directory)" -ForegroundColor Yellow
        $errors++
    }
} catch {
    Write-Host "  ✗ Framework not installed!" -ForegroundColor Red
    Write-Host "    Run: pip install -e . (from root directory)" -ForegroundColor Yellow
    $errors++
}

# 3. Check configuration files
Write-Host "[3/8] Checking configuration files..." -ForegroundColor Yellow
$rootDir = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $rootDir ".tapps-agents\config.yaml"
$cursorRulesPath = Join-Path $rootDir ".cursor\rules"

if (Test-Path $configPath) {
    Write-Host "  ✓ Config file exists: .tapps-agents\config.yaml" -ForegroundColor Green
} else {
    Write-Host "  ✗ Config file missing!" -ForegroundColor Red
    Write-Host "    Run: python -m tapps_agents.cli init (from root directory)" -ForegroundColor Yellow
    $errors++
}

if (Test-Path $cursorRulesPath) {
    Write-Host "  ✓ Cursor Rules exist: .cursor\rules\" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Cursor Rules missing (optional)" -ForegroundColor Yellow
    Write-Host "    Run: python -m tapps_agents.cli init (from root directory)" -ForegroundColor Yellow
    $warnings++
}

# 4. Check pytest installation
Write-Host "[4/8] Checking pytest..." -ForegroundColor Yellow
try {
    $pytestVersion = python -m pytest --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $pytestVersion" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Pytest not installed!" -ForegroundColor Red
        Write-Host "    Run: pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-timeout" -ForegroundColor Yellow
        $errors++
    }
} catch {
    Write-Host "  ✗ Pytest not installed!" -ForegroundColor Red
    $errors++
}

# 5. Check test dependencies
Write-Host "[5/8] Checking test dependencies..." -ForegroundColor Yellow
$requiredPackages = @("pytest", "pytest-asyncio", "httpx", "pydantic", "aiohttp")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $result = pip show $package 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -eq 0) {
    Write-Host "  ✓ All required packages installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Missing packages: $($missingPackages -join ', ')" -ForegroundColor Red
    Write-Host "    Run: pip install -r requirements.txt" -ForegroundColor Yellow
    $errors++
}

# 6. Check test discovery
Write-Host "[6/8] Checking test discovery..." -ForegroundColor Yellow
try {
    $testCount = python -m pytest --collect-only -q 2>&1 | Select-String -Pattern "test session starts|collected|error"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Tests can be discovered" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Test discovery failed!" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Test discovery failed!" -ForegroundColor Red
    $errors++
}

# 7. Run a sample test
Write-Host "[7/8] Running sample test..." -ForegroundColor Yellow
try {
    $testResult = python -m pytest tests/unit/test_analyst_agent.py::TestAnalystAgent::test_help -v 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Sample test passed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Sample test failed!" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Could not run sample test!" -ForegroundColor Red
    $errors++
}

# 8. Check optional LLM services
Write-Host "[8/8] Checking optional LLM services..." -ForegroundColor Yellow
$llmAvailable = $false

# Check Ollama
try {
    $ollamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($ollamaCheck.StatusCode -eq 200) {
        Write-Host "  ✓ Ollama is running" -ForegroundColor Green
        $llmAvailable = $true
    }
} catch {
    # Ollama not available, check API keys
}

# Check API keys
if ($env:ANTHROPIC_API_KEY) {
    Write-Host "  ✓ Anthropic API key set" -ForegroundColor Green
    $llmAvailable = $true
}

if ($env:OPENAI_API_KEY) {
    Write-Host "  ✓ OpenAI API key set" -ForegroundColor Green
    $llmAvailable = $true
}

if (-not $llmAvailable) {
    Write-Host "  ⚠ No LLM service available (optional for unit tests)" -ForegroundColor Yellow
    Write-Host "    Integration tests will be skipped" -ForegroundColor Yellow
    $warnings++
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "✓ All checks passed! Ready to run tests." -ForegroundColor Green
    Write-Host ""
    Write-Host "Quick start:" -ForegroundColor Cyan
    Write-Host "  pytest tests/unit/ -v              # Run all unit tests" -ForegroundColor White
    Write-Host "  pytest tests/integration/ -v        # Run integration tests" -ForegroundColor White
    exit 0
} elseif ($errors -eq 0) {
    Write-Host "✓ Core setup complete ($warnings warning(s))" -ForegroundColor Green
    Write-Host "  You can run unit tests, but some features may be limited." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "✗ Setup incomplete ($errors error(s), $warnings warning(s))" -ForegroundColor Red
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    if ($errors -gt 0) {
        Write-Host "  1. Fix the errors above" -ForegroundColor Yellow
        Write-Host "  2. Re-run this script to verify" -ForegroundColor Yellow
    }
    exit 1
}

