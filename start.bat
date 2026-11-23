@echo off
echo ========================================================
echo   MGH Freight Visibility Dashboard (Unified Single-Host)
echo ========================================================
echo.

if not exist "frontend\dist\index.html" (
    echo [1/2] Building React frontend static bundle...
    cd frontend && call npm run build && cd ..
) else (
    echo [1/2] Found existing frontend production build in frontend\dist
)

echo [2/2] Starting Unified Server (FastAPI + React SPA) on port 8000...
start "MGH Dashboard Server" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 >nul
start http://localhost:8000

echo.
echo ========================================================
echo   Unified Dashboard : http://localhost:8000
echo   FastAPI Swagger UI: http://localhost:8000/docs
echo   FastAPI ReDoc     : http://localhost:8000/redoc
echo ========================================================
