# Belot Online — launch backend + frontend with one command.
#   Usage:  .\start.ps1
# Opens two windows (backend :8000, frontend :3000) and the browser.

$root = $PSScriptRoot

# Backend (FastAPI + WebSockets) in its own window.
Start-Process powershell -ArgumentList @(
  '-NoExit', '-Command',
  "Set-Location '$root\backend'; python -m uvicorn app.main:app --reload --port 8000"
)

# Frontend (Vite). Install deps first only if needed.
Start-Process powershell -ArgumentList @(
  '-NoExit', '-Command',
  "Set-Location '$root\frontend'; if (-not (Test-Path node_modules)) { npm install }; npm run dev"
)

Write-Host ""
Write-Host "Belot Online starting..." -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "  Backend:  http://localhost:8000/docs"
Write-Host ""
Write-Host "Open http://localhost:3000 in THREE browser windows to play 3-player."
Start-Sleep -Seconds 4
Start-Process "http://localhost:3000"
