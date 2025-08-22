<#
Start API gateway pointing to existing sessions service.
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/start_gateway.ps1 -SessionsUrl http://localhost:8830 -Port 9000
#>
param(
  [string]$SessionsUrl = 'http://localhost:8003',
  [int]$Port = 9000
)
$root = (Resolve-Path "$PSScriptRoot\..\").Path
$python = Join-Path $root '.venv/\Scripts/python.exe'
if(!(Test-Path $python)){ $python='python' }
$env:PYTHONPATH = "$root;$root\packages;$root\services"
$env:SESSIONS_URL = $SessionsUrl
Write-Host "[start_gateway] SESSIONS_URL=$SessionsUrl port=$Port" -ForegroundColor Cyan
& $python -m uvicorn apps.api-gateway.main:app --host 127.0.0.1 --port $Port --log-level info
