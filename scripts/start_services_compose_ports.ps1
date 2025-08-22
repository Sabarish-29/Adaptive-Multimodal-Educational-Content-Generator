<#
Starts core microservices using the same port mapping as docker-compose.dev.yml so that
integration_smoke.py works without Docker:
  profiles    :8000
  adaptation  :8001
  sessions    :8002
  contentgen  :8003
  rag         :8005 (optional via -IncludeRag)

Usage:
  powershell -ExecutionPolicy Bypass -File .\scripts\start_services_compose_ports.ps1 -FastTest

Params:
  -FastTest     Sets FAST_TEST_MODE=true (sessions synthetic SSE + faster timeouts)
  -NoReload     Omit --reload for slightly lower CPU usage
  -IncludeRag   Also start rag service on :8005
  -MongoUri     Override Mongo URI (default mongodb://localhost:27017/edu)
  -RedisUrl     Override Redis URL (default redis://localhost:6379/0)

Each service launched in its own minimized PowerShell window.
#>
param(
  [switch]$FastTest,
  [switch]$NoReload,
  [switch]$IncludeRag,
  [string]$MongoUri = 'mongodb://localhost:27017/edu',
  [string]$MongoDb  = 'edu',
  [string]$RedisUrl = 'redis://localhost:6379/0'
)
$root = (Resolve-Path "$PSScriptRoot\..\").Path
$python = Join-Path $root '.venv/\Scripts/python.exe'
if(!(Test-Path $python)){ Write-Error "Virtual env python not found ($python). Run bootstrap_env.ps1 first."; exit 1 }
$pyPath = "$root;$root\packages;$root\services"

function Launch {
  param([string]$Title,[string]$Module,[int]$Port,[hashtable]$ExtraEnv)
  $assignments = @("`$env:PYTHONPATH='$pyPath'","`$env:MONGODB_URI='$MongoUri'","`$env:MONGODB_DB='$MongoDb'")
  if($ExtraEnv){ foreach($k in $ExtraEnv.Keys){ $val = $ExtraEnv[$k]; $assignments += ("`$env:$k='" + $val + "'") } }
  $reload = if($NoReload){ '' } else { '--reload' }
  $envPrefix = ($assignments -join '; ') + '; '
  $cmd = "$envPrefix & '$python' -m uvicorn $Module --host 127.0.0.1 --port $Port $reload"
  Start-Process powershell -ArgumentList '-NoExit','-Command', $cmd -WindowStyle Minimized -WorkingDirectory $root | Out-Null
  Write-Host ("Started {0} on :{1}" -f $Title,$Port)
}

Write-Host "[compose-ports] Launching services (FastTest=$FastTest)..." -ForegroundColor Cyan
if($FastTest){ $env:FAST_TEST_MODE='true' }

# Profiles (8000)
Launch -Title 'profiles' -Module 'services.profiles.profiles.main:app' -Port 8000 -ExtraEnv @{}
# Adaptation (8001)
Launch -Title 'adaptation' -Module 'services.adaptation.adaptation.main:app' -Port 8001 -ExtraEnv @{ REDIS_URL=$RedisUrl }
# Sessions (8002) depends adaptation
$extraSess = @{ ADAPTATION_URL='http://localhost:8001'; REDIS_URL=$RedisUrl }
if($FastTest){ $extraSess['FAST_TEST_MODE']='true' }
Launch -Title 'sessions' -Module 'services.sessions.sessions.main:app' -Port 8002 -ExtraEnv $extraSess
# ContentGen (8003)
Launch -Title 'contentgen' -Module 'services.contentgen.contentgen.main:app' -Port 8003 -ExtraEnv @{}
if($IncludeRag){ Launch -Title 'rag' -Module 'services.rag.rag.main:app' -Port 8005 -ExtraEnv @{} }

Write-Host "[compose-ports] Done. Run: powershell -ExecutionPolicy Bypass -File .\\scripts\\health_check.ps1 -Ports 8000,8001,8002,8003" -ForegroundColor Green
