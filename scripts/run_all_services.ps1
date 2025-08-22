param(
  [int]$BasePort = 8001,
  [string]$MongoUri = 'mongodb://localhost:27017/edu',
  [string]$MongoDb = 'edu',
  [string]$RedisUrl = 'redis://localhost:6379/0',
  [string]$AdaptationUrl = 'http://localhost:8001',
  [switch]$NoBrowser
)

# Ensure PYTHONPATH includes repo root and packages for monorepo imports (common_utils, etc.)
$repoRoot = (Get-Location).Path
$pyPath = "$repoRoot;$repoRoot\packages;$repoRoot\packages\common_utils;$repoRoot\packages\common_utils\common_utils"
Write-Host "[env] PYTHONPATH=$pyPath"
${env:PYTHONPATH} = $pyPath

$services = @(
  @{ Name='adaptation'; Module='adaptation.main:app' ; Path='services/adaptation/adaptation' }
  @{ Name='contentgen'; Module='contentgen.main:app' ; Path='services/contentgen/contentgen' }
  @{ Name='sessions'; Module='sessions.main:app' ; Path='services/sessions/sessions' }
  @{ Name='profiles'; Module='profiles.main:app' ; Path='services/profiles/profiles' }
  @{ Name='rag'; Module='rag.main:app' ; Path='services/rag/rag' }
)

$index = 0
foreach ($svc in $services) {
  $port = $BasePort + $index
  $name = $svc.Name
  Write-Host "[run] Starting $name on :$port"
  # Build command with env vars per service
  $envCmd = @(
    "$env:MONGODB_URI='$MongoUri'",
    "$env:MONGODB_DB='$MongoDb'"
  )
  if ($name -in 'sessions','adaptation','contentgen') { $envCmd += "$env:REDIS_URL='$RedisUrl'" }
  if ($name -eq 'sessions') { $envCmd += "$env:ADAPTATION_URL='$AdaptationUrl'" }
  $full = ". .\\.venv\\Scripts\\Activate.ps1; $env:PYTHONPATH='$pyPath'; " + ($envCmd -join '; ') + "; uvicorn $($svc.Module) --reload --port $port --app-dir $($svc.Path)"
  Start-Process powershell -ArgumentList "-NoLogo","-NoProfile","-Command",$full -WindowStyle Minimized
  $index++
}
Write-Host "All services launched."
