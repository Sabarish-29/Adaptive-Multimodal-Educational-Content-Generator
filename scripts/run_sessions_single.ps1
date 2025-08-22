<#
Run sessions service on specified port without --reload (single process) and optional FAST_TEST_MODE.
Usage:
  powershell -ExecutionPolicy Bypass -File .\scripts\run_sessions_single.ps1 -Port 8103 -FastTest
#>
param(
  [int]$Port = 8003,
  [string]$BindHost = '127.0.0.1',
  [switch]$FastTest,
  [switch]$Detach,
  [string]$LogFile
)
$root = (Resolve-Path "$PSScriptRoot\..\").Path
$python = Join-Path $root '.venv/\Scripts/python.exe'
if(!(Test-Path $python)){ $python='python' }
$env:PYTHONPATH = "$root;$root\packages;$root\services"
if($FastTest){ $env:FAST_TEST_MODE='true' }
Write-Host "[run_sessions_single] Starting sessions on port $Port (FAST_TEST_MODE=$($env:FAST_TEST_MODE)) Detach=$Detach" -ForegroundColor Cyan
# Build argument list (avoids Invoke-Expression parsing issues)
$argsList = @('-m','uvicorn','services.sessions.sessions.main:app','--host', $BindHost,'--port', $Port,'--log-level','info')
if($Detach){
  if($LogFile){
    $logPath = (Resolve-Path -LiteralPath $LogFile -ErrorAction SilentlyContinue)
    if(-not $logPath){ $logPath = (Join-Path (Get-Location) $LogFile) }
    Write-Host "[run_sessions_single] Logging to $logPath" -ForegroundColor Yellow
    Start-Process -FilePath $python -ArgumentList $argsList -WorkingDirectory $root -RedirectStandardOutput $logPath -RedirectStandardError $logPath -WindowStyle Minimized | Out-Null
  } else {
    Start-Process -FilePath $python -ArgumentList $argsList -WorkingDirectory $root -WindowStyle Minimized | Out-Null
  }
  Write-Host "[run_sessions_single] Launched detached process." -ForegroundColor Green
} else {
  & $python @argsList
}
