# Startup Script for Enterprise AI CRM Demo
Write-Host "--- Starting Enterprise AI CRM Backend ---" -ForegroundColor Cyan

# 1. Start FastAPI Server
Write-Host "Launching FastAPI on http://localhost:8000..." -ForegroundColor Yellow
cd server
python -m uvicorn main:app --reload --port 8000 &

# 2. Reminder for Ngrok
Write-Host ""
Write-Host "IMPORTANT: To make this public for Edward, run the following command in a NEW terminal:" -ForegroundColor Green
Write-Host "ngrok http 8000" -ForegroundColor White
Write-Host ""
Write-Host "Dashboard will be available at: http://localhost:5173 (if running npm run dev in client)" -ForegroundColor Gray
