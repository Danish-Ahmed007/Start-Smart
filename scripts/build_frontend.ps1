# Build and Deploy Script for StartSmart Frontend (Windows PowerShell)
# This script builds the Flutter web app and injects the API key

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting StartSmart Frontend Build Process..." -ForegroundColor Cyan

# Get script directory and navigate to frontend
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $projectRoot "frontend"

Set-Location $frontendDir

Write-Host ""
Write-Host "📦 Step 1: Building Flutter web app..." -ForegroundColor Yellow
flutter build web --release

Write-Host ""
Write-Host "🔑 Step 2: Injecting Google Maps API key..." -ForegroundColor Yellow
Set-Location $projectRoot
python scripts/inject_api_key.py

Write-Host ""
Write-Host "✅ Build complete!" -ForegroundColor Green
Write-Host "📁 Build output: frontend/build/web/" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 To deploy:" -ForegroundColor Cyan
Write-Host "   - Upload frontend/build/web/ to your hosting provider"
Write-Host "   - Make sure backend is deployed with correct .env configuration"
Write-Host ""
Write-Host "⚠️  Remember: Never commit the build/ directory!" -ForegroundColor Red
