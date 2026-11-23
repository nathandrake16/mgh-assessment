# MGH Freight Visibility Dashboard Launcher (Unified Single-Host)
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  MGH Freight Visibility Dashboard (Unified Single-Host)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

if (-not (Test-Path "frontend\dist\index.html")) {
    Write-Host "[1/2] Building React frontend static bundle..." -ForegroundColor Yellow
    Push-Location frontend
    npm run build
    Pop-Location
} else {
    Write-Host "[1/2] Found existing frontend production build in frontend\dist" -ForegroundColor Green
}

Write-Host "[2/2] Starting Unified Server (FastAPI + React SPA) on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 3
Start-Process "http://localhost:8000"

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "  Unified Dashboard : http://localhost:8000" -ForegroundColor Green
Write-Host "  FastAPI Swagger UI: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  FastAPI ReDoc     : http://localhost:8000/redoc" -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Green
