@echo off
title ApexPulse AI Launcher
echo ============================================================
echo   Starting ApexPulse AI-Powered Sports Coaching System
echo ============================================================

start "ApexPulse Backend API (Port 8000)" cmd /k "cd /d D:\sports-coaching-system\backend && .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --workers 1"
timeout /t 3 /nobreak >nul

start "ApexPulse Frontend UI (Port 5173)" cmd /k "cd /d D:\sports-coaching-system\frontend && npm run dev -- --host 0.0.0.0 --port 5173"
timeout /t 3 /nobreak >nul

start "ApexPulse Public HTTPS Tunnel" cmd /k "powershell -ExecutionPolicy Bypass -File D:\sports-coaching-system\start-public-tunnel.ps1"

echo.
echo   Local App   : http://localhost:5173
echo   Backend API : http://localhost:8000/docs
echo   Public Link : Check the "ApexPulse Public HTTPS Tunnel" window!
echo ============================================================
pause
