#!/usr/bin/env bash
# ==============================================================================
# AEGIS Pre-Submission CI Validation Script
# Runs backend tests, frontend build, linter, and manifest validation.
# ==============================================================================

set -euo pipefail

echo "========================================================================"
echo "  AEGIS Bharat Agentic 2026 Pre-Submission Validation"
echo "========================================================================"

# 1. Validate Agent Manifest
echo ""
echo "[Step 1/4] Validating Agent Manifest..."
python scripts/validate_manifest.py

# 2. Run Backend Tests
echo ""
echo "[Step 2/4] Executing Backend Test Suite..."
pytest backend/tests -v

# 3. Build Frontend Production Bundle
echo ""
echo "[Step 3/4] Building Frontend Production Bundle..."
(cd frontend && npm run build)

# 4. Lint Frontend Codebase
echo ""
echo "[Step 4/4] Linting Frontend Codebase..."
(cd frontend && npm run lint)

echo ""
echo "========================================================================"
echo "  [SUCCESS] All AEGIS pre-submission validations passed!"
echo "========================================================================"
exit 0
