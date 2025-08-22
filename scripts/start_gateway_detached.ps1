<#
Detached gateway launcher.
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/start_gateway_detached.ps1 -Port 9000 -SessionsUrl http://localhost:8830 -LogDir logs
#>
param(
  [int]$Port = 9000,
  [string]$SessionsUrl = 'http://localhost:8003',
  [string]$LogDir = 'logs'
)
$root = (Resolve-Path "$PSScriptRoot\..\").Path
if(!(Test-Path $LogDir)){ New-Item -ItemType Directory -Path $LogDir | Out-Null }
$python = Join-Path $root '.venv/\Scripts/python.exe'
if(!(Test-Path $python)){ $python='python' }
$env:PYTHONPATH = "$root;$root\packages;$root\services"
$env:SESSIONS_URL = $SessionsUrl
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdout = Join-Path $LogDir "gateway_${Port}_${ts}.out.log"
$stderr = Join-Path $LogDir "gateway_${Port}_${ts}.err.log"
Write-Host "[start_gateway_detached] Launching gateway port=$Port SESSIONS_URL=$SessionsUrl" -ForegroundColor Cyan
Start-Process -FilePath $python -ArgumentList '-m','uvicorn','apps.api-gateway.main:app','--host','127.0.0.1','--port',"$Port",'--log-level','info' -WorkingDirectory $root -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Minimized | Out-Null
Write-Host "[start_gateway_detached] STDOUT: $stdout" -ForegroundColor Yellow
Write-Host "[start_gateway_detached] STDERR: $stderr" -ForegroundColor Yellow
