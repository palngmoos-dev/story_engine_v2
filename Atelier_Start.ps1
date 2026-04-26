# Atelier Master Startup Script
# Created by Antigravity

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 GRAND ATELIER - SYSTEM ACTIVATION" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$baseDir = "D:\아름다운 여행 4.25\Atelier"

# 1. Start Ollama (if not running)
if (-not (Get-Process | Where-Object {$_.ProcessName -like "*ollama*"})) {
    Write-Host "🧊 Starting Ollama Service..." -ForegroundColor Yellow
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 2. Start Telegram Bot
Write-Host "🤖 Starting Telegram Bot (Antigravity)..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/c cd /d `"$baseDir`" && run_antigravity.bat"

# 3. Start Harness UI
Write-Host "🎨 Starting Harness UI (Vite Server)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$baseDir\storytable_-the-atelier`"; npm run dev"

Write-Host "`n✅ All essential systems have been activated." -ForegroundColor Green
Write-Host "- Telegram Bot: Running in WSL"
Write-Host "- Harness UI: http://localhost:3000"
Write-Host "- Memory: Linked to Obsidian PARA folders"
Write-Host "==========================================" -ForegroundColor Cyan
