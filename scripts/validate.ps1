# ==============================================================================
# AEGIS Pre-Submission Windows PowerShell Validation Script
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  AEGIS Bharat Agentic 2026 Pre-Submission Validation" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Validate Agent Manifest
Write-Host "`n[Step 1/4] Validating Agent Manifest..." -ForegroundColor Yellow
python scripts/validate_manifest.py
if ($LASTEXITCODE -ne 0) { throw "Agent manifest validation failed!" }

# 2. Run Backend Tests
Write-Host "`n[Step 2/4] Executing Backend Test Suite..." -ForegroundColor Yellow
pytest backend/tests
if ($LASTEXITCODE -ne 0) { throw "Backend tests failed!" }

# 3. Build Frontend Production Bundle
Write-Host "`n[Step 3/4] Building Frontend Production Bundle..." -ForegroundColor Yellow
Push-Location frontend
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed!" }

    # 4. Lint Frontend Codebase
    Write-Host "`n[Step 4/4] Linting Frontend Codebase..." -ForegroundColor Yellow
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed!" }
}
finally {
    Pop-Location
}

Write-Host "`n========================================================================" -ForegroundColor Green
Write-Host "  [SUCCESS] All AEGIS pre-submission validations passed!" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
exit 0
