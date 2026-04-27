# 한글 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# free 4.27 폴더의 설정을 읽어와서 OpenRouter 무료 모델로 Claude를 실행하는 스크립트입니다.
$configPath = ".\free 4.27\.claude\settings.local.json"

if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    
    # 환경 변수 설정
    $env:ANTHROPIC_AUTH_TOKEN = $config.env.ANTHROPIC_AUTH_TOKEN
    $env:ANTHROPIC_BASE_URL = $config.env.ANTHROPIC_BASE_URL
    
    # 사용할 모델 결정 (Sonnet 설정을 우선 사용)
    $targetModel = $config.env.ANTHROPIC_DEFAULT_SONNET_MODEL
    
    Write-Host "--------------------------------------------------" -ForegroundColor Yellow
    Write-Host "OpenRouter 무료 모델 설정을 로드했습니다." -ForegroundColor Cyan
    Write-Host "Base URL: $($env:ANTHROPIC_BASE_URL)"
    Write-Host "Target Model: $targetModel"
    Write-Host "--------------------------------------------------" -ForegroundColor Yellow
    
    # Claude 실행 시 --model 플래그를 사용하여 명시적으로 무료 모델을 지정합니다.
    claude --model "$targetModel"
} else {
    Write-Error "설정 파일을 찾을 수 없습니다: $configPath"
}
