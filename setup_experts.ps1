# Expert Setup Script for TappsCodingAgents
# Helps initialize or update expert configuration

param(
    [Parameter(Mandatory=$false)]
    [switch]$Init,
    
    [Parameter(Mandatory=$false)]
    [switch]$FromTemplate,
    
    [Parameter(Mandatory=$false)]
    [switch]$ShowCurrent
)

$expertsDir = ".tapps-agents"
$expertsFile = "$expertsDir/experts.yaml"
$templateFile = "templates/experts.yaml.template"
$exampleFile = "examples/experts/experts.yaml"

Write-Host "=== TappsCodingAgents Expert Setup ===" -ForegroundColor Cyan
Write-Host ""

# Show current configuration
if ($ShowCurrent) {
    if (Test-Path $expertsFile) {
        Write-Host "Current expert configuration:" -ForegroundColor Green
        Write-Host ""
        Get-Content $expertsFile
        exit 0
    } else {
        Write-Host "No expert configuration found at: $expertsFile" -ForegroundColor Yellow
        Write-Host "Run with -Init to create one." -ForegroundColor Yellow
        exit 1
    }
}

# Initialize from template
if ($Init -or $FromTemplate) {
    # Create .tapps-agents directory if it doesn't exist
    if (-not (Test-Path $expertsDir)) {
        Write-Host "Creating $expertsDir directory..." -ForegroundColor Green
        New-Item -ItemType Directory -Path $expertsDir -Force | Out-Null
    }
    
    # Check if experts.yaml already exists
    if (Test-Path $expertsFile) {
        Write-Host "WARNING: $expertsFile already exists!" -ForegroundColor Yellow
        $overwrite = Read-Host "Overwrite? (y/n)"
        if ($overwrite -ne "y") {
            Write-Host "Cancelled." -ForegroundColor Gray
            exit 0
        }
        Write-Host "Backing up existing file..." -ForegroundColor Gray
        Copy-Item $expertsFile "$expertsFile.backup" -Force
    }
    
    # Choose source
    if ($FromTemplate -and (Test-Path $templateFile)) {
        Write-Host "Copying from template: $templateFile" -ForegroundColor Green
        Copy-Item $templateFile $expertsFile -Force
    } elseif (Test-Path $exampleFile) {
        Write-Host "Copying from example: $exampleFile" -ForegroundColor Green
        Copy-Item $exampleFile $expertsFile -Force
    } else {
        Write-Host "Creating basic experts.yaml..." -ForegroundColor Green
        $basicConfig = @"
# TappsCodingAgents Industry Experts Configuration
# .tapps-agents/experts.yaml

experts:
  # Example Expert Configuration
  # Replace with your actual domain experts
  - expert_id: expert-example
    expert_name: Example Expert
    primary_domain: example-domain
    rag_enabled: true
    fine_tuned: false
"@
        Set-Content -Path $expertsFile -Value $basicConfig
    }
    
    Write-Host ""
    Write-Host "✅ Expert configuration created: $expertsFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Edit $expertsFile to match your domains" -ForegroundColor White
    Write-Host "2. Ensure expert_id matches primary_expert_id in .tapps-agents/domains.md" -ForegroundColor White
    Write-Host "3. Add knowledge base files to .tapps-agents/knowledge/{domain}/ if using RAG" -ForegroundColor White
    Write-Host ""
    exit 0
}

# Default: Show help
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  .\setup_experts.ps1 -Init              # Initialize from example" -ForegroundColor White
Write-Host "  .\setup_experts.ps1 -FromTemplate       # Initialize from template" -ForegroundColor White
Write-Host "  .\setup_experts.ps1 -ShowCurrent        # Show current configuration" -ForegroundColor White
Write-Host ""
Write-Host "Expert Configuration:" -ForegroundColor Cyan
Write-Host "  Location: $expertsFile" -ForegroundColor White
Write-Host "  Template: $templateFile" -ForegroundColor White
Write-Host "  Example:  $exampleFile" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  See: docs/EXPERT_CONFIG_GUIDE.md" -ForegroundColor White

