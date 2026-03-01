# 🧹 Script for cleaning project before deployment (PowerShell)
# Usage: .\scripts\clean_before_deploy.ps1

Write-Host "🧹 Cleaning project before deployment..." -ForegroundColor Yellow

# Root directory
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $RootDir

Write-Host "`nCleaning Python artifacts..." -ForegroundColor Yellow
Get-ChildItem -Path $RootDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path $RootDir -Recurse -File -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -Path $RootDir -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path $RootDir -Recurse -Directory -Filter ".mypy_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path $RootDir -Recurse -File -Filter "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host "Cleaning Node.js artifacts..." -ForegroundColor Yellow
if (Test-Path "$RootDir\frontend\node_modules") {
    Remove-Item -Path "$RootDir\frontend\node_modules" -Recurse -Force
}
if (Test-Path "$RootDir\frontend\dist") {
    Remove-Item -Path "$RootDir\frontend\dist" -Recurse -Force
}

Write-Host "Cleaning test results..." -ForegroundColor Yellow
if (Test-Path "$RootDir\load_tests\results") {
    Remove-Item -Path "$RootDir\load_tests\results" -Recurse -Force
}
if (Test-Path "$RootDir\load_tests\__pycache__") {
    Remove-Item -Path "$RootDir\load_tests\__pycache__" -Recurse -Force
}

Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
if (Test-Path "$RootDir\-p") {
    Remove-Item -Path "$RootDir\-p" -Recurse -Force
}
if (Test-Path "$RootDir\trash_arizonalavka") {
    Remove-Item -Path "$RootDir\trash_arizonalavka" -Recurse -Force
}
if (Test-Path "$RootDir\backend\logs") {
    Remove-Item -Path "$RootDir\backend\logs" -Recurse -Force
}

Write-Host "Removing local environment files..." -ForegroundColor Yellow
if (Test-Path "$RootDir\frontend\.env.local") {
    Remove-Item -Path "$RootDir\frontend\.env.local" -Force
}
if (Test-Path "$RootDir\backend\.env") {
    Remove-Item -Path "$RootDir\backend\.env" -Force
}
if (Test-Path "$RootDir\backend\.python-version") {
    Remove-Item -Path "$RootDir\backend\.python-version" -Force
}

Write-Host "`n✅ Cleaning completed!" -ForegroundColor Green
Write-Host "`n📁 Files ready for deployment:" -ForegroundColor Cyan
Write-Host "  - backend/"
Write-Host "  - frontend/"
Write-Host "  - data/"
Write-Host "  - load_tests/"
Write-Host "  - docker-compose.yml"
Write-Host "  - .env.example"
Write-Host "`n⚠️  Don't forget to:" -ForegroundColor Yellow
Write-Host "  1. Create .env file from .env.example"
Write-Host "  2. Set JWT_SECRET_KEY to a secure random value"
Write-Host "  3. Set POSTGRES_PASSWORD to a secure random value"
Write-Host "  4. Update CORS_ORIGINS for production"
