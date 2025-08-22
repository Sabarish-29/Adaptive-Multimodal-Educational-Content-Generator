<#
Start sessions service detached with proper env setup.
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/start_sessions_detached.ps1 -Port 8830 -FastTest -LogDir logs
#>
param(
  [int]$Port = 8830,
  [switch]$FastTest,
  [string]$LogDir = 'logs'
)
$root = (Resolve-Path "$PSScriptRoot\..\").Path
if(!(Test-Path $LogDir)){ New-Item -ItemType Directory -Path $LogDir | Out-Null }
$python = Join-Path $root '.venv/\Scripts/python.exe'
if(!(Test-Path $python)){ $python='python' }
$env:PYTHONPATH = "$root;$root\packages;$root\services"
if($FastTest){ $env:FAST_TEST_MODE='true' } else { $env:FAST_TEST_MODE='' }
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdout = Join-Path $LogDir "sessions_${Port}_${ts}.out.log"
$stderr = Join-Path $LogDir "sessions_${Port}_${ts}.err.log"
Write-Host "[start_sessions_detached] Launching sessions port=$Port FAST_TEST_MODE=$($env:FAST_TEST_MODE)" -ForegroundColor Cyan
Start-Process -FilePath $python -ArgumentList '-m','uvicorn','services.sessions.sessions.main:app','--host','127.0.0.1','--port',"$Port",'--log-level','info' -WorkingDirectory $root -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Minimized | Out-Null
Write-Host "[start_sessions_detached] STDOUT: $stdout" -ForegroundColor Yellow
Write-Host "[start_sessions_detached] STDERR: $stderr" -ForegroundColor Yellow
