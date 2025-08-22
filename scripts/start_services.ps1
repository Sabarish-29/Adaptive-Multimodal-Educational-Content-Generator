<#
Starts core microservices (adaptation, contentgen, sessions, profiles) and the API gateway
each in its own PowerShell window so they remain running concurrently.

Usage (from repo root, venv created already):
  powershell -ExecutionPolicy Bypass -File .\scripts\start_services.ps1

Customize ports by setting env vars before calling (optional):
  $env:ADAPTATION_PORT=8101
#>
param(
  [int]$AdaptationPort = [int]($env:ADAPTATION_PORT | ForEach-Object { if($_){$_} else {8001} }),
  [int]$ContentPort    = [int]($env:CONTENTGEN_PORT | ForEach-Object { if($_){$_} else {8002} }),
  [int]$SessionsPort   = [int]($env:SESSIONS_PORT | ForEach-Object { if($_){$_} else {8003} }),
  [int]$ProfilesPort   = [int]($env:PROFILES_PORT | ForEach-Object { if($_){$_} else {8004} }),
  [int]$GatewayPort    = [int]($env:GATEWAY_PORT | ForEach-Object { if($_){$_} else {9000} }),
  [switch]$NoReload,
  [switch]$FastTestSessions
)
$root = (Resolve-Path "$PSScriptRoot\..\").Path
$python = Join-Path $root '.venv/\Scripts/python.exe'
if(!(Test-Path $python)){ Write-Error "Virtual env python not found at $python"; exit 1 }
$pyPath = "$root;$root\packages;$root\services"
function Start-ServiceWindow {
  param([string]$Title,[string]$Command)
  $full = "`$env:PYTHONPATH='$pyPath'; Set-Location '$root'; $Command"
  Start-Process powershell -ArgumentList '-NoExit','-Command', $full -WindowStyle Minimized -WorkingDirectory $root | Out-Null
  Write-Host "Started: $Title"
}
if($NoReload){ $reloadFlag = '' } else { $reloadFlag='--reload' }
$sessionsEnvPrefix = if($FastTestSessions){ "`$env:FAST_TEST_MODE='true'; " } else { '' }
Start-ServiceWindow -Title "adaptation:$AdaptationPort" -Command "& '$python' -m uvicorn services.adaptation.adaptation.main:app --port $AdaptationPort $reloadFlag"
Start-ServiceWindow -Title "contentgen:$ContentPort" -Command "& '$python' -m uvicorn services.contentgen.contentgen.main:app --port $ContentPort $reloadFlag"
Start-ServiceWindow -Title "sessions:$SessionsPort" -Command "${sessionsEnvPrefix}& '$python' -m uvicorn services.sessions.sessions.main:app --port $SessionsPort $reloadFlag"
Start-ServiceWindow -Title "profiles:$ProfilesPort" -Command "& '$python' -m uvicorn services.profiles.profiles.main:app --port $ProfilesPort $reloadFlag"
# Propagate overridden sessions base to gateway if changed
$gwEnvPrefix = "`$env:SESSIONS_URL='http://localhost:$SessionsPort'; "
Start-ServiceWindow -Title "gateway:$GatewayPort" -Command "$gwEnvPrefix & '$python' -m uvicorn apps.api-gateway.main:app --port $GatewayPort $reloadFlag"
Write-Host "All service windows launched. Run .\\scripts\\health_check.ps1 after a few seconds."
