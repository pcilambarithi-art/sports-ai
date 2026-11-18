# Launch ApexPulse AI-Powered Sports Coaching System locally
# Opens FastAPI Backend (port 8000, single worker for 2.93 GB model) and Vite Frontend (port 5173)

Write-Host "Starting ApexPulse Backend (FastAPI on http://localhost:8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\sports-coaching-system\backend'; .\.venv\Scripts\alembic.exe upgrade head; .\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --workers 1"

Write-Host "Starting ApexPulse Frontend (React + Vite on http://localhost:5173)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'D:\sports-coaching-system\frontend'; npm run dev"

Write-Host "`nBackend API Docs : http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend App     : http://localhost:5173" -ForegroundColor Yellow
Write-Host "Note: Your 2.93 GB trained model loads in the background (~90s); check the top-bar badge for readiness." -ForegroundColor Gray
