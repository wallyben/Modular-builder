# =============================================================================
# Modular AI Execution Engine — Phase 1 — PowerShell Setup Script
# Windows-compatible. Run from the project root.
# =============================================================================

Write-Host "=== Modular AI Execution Engine — Phase 1 Setup ===" -ForegroundColor Cyan

# 1. Create virtual environment
Write-Host "`n[1/5] Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create venv"; exit 1 }

# 2. Activate virtual environment
Write-Host "[2/5] Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip
Write-Host "[3/5] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# 4. Install dependencies
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install dependencies"; exit 1 }

# 5. Run tests
Write-Host "[5/5] Running pytest suite..." -ForegroundColor Yellow
pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[WARN] Some tests failed. Check output above." -ForegroundColor Red
} else {
    Write-Host "`n[OK] All tests passed." -ForegroundColor Green
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan
Write-Host "Run the engine:" -ForegroundColor White
Write-Host "  python main.py run `"Build simple test task`"" -ForegroundColor Green
Write-Host "  python main.py run `"My task`" --adapter anthropic" -ForegroundColor Green
Write-Host "  python main.py list-tools" -ForegroundColor Green
Write-Host "  python main.py list-adapters" -ForegroundColor Green
