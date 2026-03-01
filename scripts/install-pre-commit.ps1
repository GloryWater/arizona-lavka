# =============================================================================
# ARIZONA LAVKA MARKETPLACE - INSTALL PRE-COMMIT HOOKS (PowerShell)
# =============================================================================
# This script installs pre-commit hooks for the project
# Usage: .\scripts\install-pre-commit.ps1
# =============================================================================

Write-Host "🔧 Installing pre-commit hooks for Arizona Lavka Marketplace..." -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
} catch {
    try {
        $pythonCmd = Get-Command python3 -ErrorAction Stop
    } catch {
        Write-Host "❌ Python is not installed. Please install Python 3.12+ first." -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Found Python: $(& $pythonCmd --version)" -ForegroundColor Green

# Check if pre-commit is installed
try {
    $preCommitCmd = Get-Command pre-commit -ErrorAction Stop
    Write-Host "✅ Found pre-commit: $(pre-commit --version)" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing pre-commit..." -ForegroundColor Yellow
    & $pythonCmd -m pip install pre-commit
    Write-Host "✅ pre-commit installed" -ForegroundColor Green
}

# Install pre-commit hooks
Write-Host "🔗 Installing git hooks..." -ForegroundColor Cyan
pre-commit install

Write-Host ""
Write-Host "✅ Pre-commit hooks installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 To run pre-commit manually:" -ForegroundColor Cyan
Write-Host "   pre-commit run --all-files"
Write-Host ""
Write-Host "📝 To run pre-commit on all files with verbose output:" -ForegroundColor Cyan
Write-Host "   pre-commit run --all-files --verbose"
Write-Host ""
Write-Host "📝 To run a specific hook:" -ForegroundColor Cyan
Write-Host "   pre-commit run ruff --all-files"
Write-Host ""
Write-Host "📝 To uninstall pre-commit:" -ForegroundColor Cyan
Write-Host "   pre-commit uninstall"
Write-Host ""
