@echo off
echo ============================================
echo  Chart2Code — Starting SaaS Server
echo ============================================

REM Load .env file nếu có
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" set %%a=%%b
    )
    echo [OK] Loaded .env
)

REM Check venv
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [OK] Virtual env activated
) else (
    echo [WARN] No .venv found - using system Python
)

REM Install backend deps nếu chưa có
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing backend dependencies...
    pip install -r backend\requirements_backend.txt
)

echo.
echo [START] Server running at: http://localhost:8000
echo [START] Landing page:      http://localhost:8000/index.html
echo [START] App:               http://localhost:8000/app.html
echo.
echo Press Ctrl+C to stop.
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
