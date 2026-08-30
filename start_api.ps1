$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SourceDirectory = Join-Path $ProjectRoot "src"

if (-not (Test-Path $Python)) {
    Write-Error "没有找到虚拟环境中的 Python：$Python"
    exit 1
}

$ProxyUrl = $env:ECOM_AGENT_PROXY

if ($ProxyUrl) {
    $env:HTTP_PROXY = $ProxyUrl
    $env:HTTPS_PROXY = $ProxyUrl
    $env:NO_PROXY = "127.0.0.1,localhost"
} else {
    Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
    Remove-Item Env:ALL_PROXY -ErrorAction SilentlyContinue
    $env:NO_PROXY = "*"
}
$env:PYTHONUTF8 = "1"

Set-Location $ProjectRoot

Write-Host "正在启动 FastAPI：http://127.0.0.1:8000"
Write-Host "API 文档：http://127.0.0.1:8000/docs"

& $Python -m uvicorn `
    ecom_agent.api.main:app `
    --app-dir $SourceDirectory `
    --host 127.0.0.1 `
    --port 8000