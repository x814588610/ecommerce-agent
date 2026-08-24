$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$WebApplication = Join-Path $ProjectRoot "web\app.py"

if (-not (Test-Path $Python)) {
    Write-Error "没有找到虚拟环境中的 Python：$Python"
    exit 1
}

Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:ALL_PROXY -ErrorAction SilentlyContinue

$env:NO_PROXY = "*"
$env:PYTHONUTF8 = "1"

Set-Location $ProjectRoot

Write-Host "正在启动 Streamlit：http://127.0.0.1:8501"

& $Python -m streamlit run $WebApplication `
    --server.address 127.0.0.1 `
    --server.port 8501