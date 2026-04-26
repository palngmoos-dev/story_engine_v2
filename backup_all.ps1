# Grand Atelier Master Backup Script
# Created by Antigravity

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$repoDir = "D:\아름다운 여행 4.25"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 STARTING MASTER GITHUB BACKUP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Set-Location $repoDir

# 1. Git Status Check
Write-Host "🔍 Checking for changes..." -ForegroundColor Yellow
git add .

# 2. Commit
Write-Host "📝 Committing changes..." -ForegroundColor Yellow
$commitMsg = "Master Backup: $timestamp"
git commit -m $commitMsg

# 3. Push to GitHub
Write-Host "☁️ Pushing to GitHub (moosking_abc.git)..." -ForegroundColor Magenta
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ SUCCESS: All data backed up to GitHub." -ForegroundColor Green
} else {
    Write-Host "`n❌ FAILED: GitHub backup encountered an error." -ForegroundColor Red
}

Write-Host "==========================================" -ForegroundColor Cyan
