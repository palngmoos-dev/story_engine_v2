# Atelier Master Startup Script (Portable Version)
# Created by Antigravity for 100% Sync PPTX Automation

$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$inputDir = Join-Path $baseDir "input_space"
$outputDir = Join-Path $baseDir "output_space"
$scriptPath = Join-Path $baseDir "system_core\run_harness_system.py"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🎨 ATELIER - 100% SYNC PPTX SYSTEM" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1. Place your .txt files in: $inputDir" -ForegroundColor Yellow
Write-Host "2. Your .pptx will appear in: $outputDir" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

# Check if input files exist
$inputFiles = Get-ChildItem -Path $inputDir -Filter *.txt
if ($inputFiles.Count -eq 0) {
    Write-Host "⏳ Waiting for input text files..." -ForegroundColor Magenta
}

# Run the master controller
python $scriptPath

Write-Host "`n✅ Process Complete. Check the output_space folder." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Pause
