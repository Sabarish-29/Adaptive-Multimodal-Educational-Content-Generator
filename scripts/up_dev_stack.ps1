param(
  [switch]$Rebuild
)

function Wait-Docker {
  Write-Host "[wait] Checking Docker daemon..." -ForegroundColor Cyan
  $retries = 20
  for ($i=0; $i -lt $retries; $i++) {
    $info = docker info 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "[wait] Docker is up" -ForegroundColor Green; return }
    Start-Sleep -Seconds 2
  }
  throw "Docker daemon not reachable after timeout"
}

function Ensure-DockerDesktopService {
  $svc = Get-Service -Name com.docker.service -ErrorAction SilentlyContinue
  if (-not $svc) { Write-Warning "Docker Desktop service not installed. Please install/start Docker Desktop manually."; return }
  if ($svc.Status -ne 'Running') {
    Write-Host "[svc] Starting Docker Desktop service..." -ForegroundColor Yellow
    try { Start-Service -Name com.docker.service -ErrorAction Stop } catch { Write-Warning "Failed to start Docker Desktop service: $($_.Exception.Message)" }
  }
}

$composeFile = "infra/compose/docker-compose.dev.yml"

Ensure-DockerDesktopService
Wait-Docker

$cmd = "docker compose -f `"$composeFile`" up -d"
if ($Rebuild) { $cmd += " --build" }
Write-Host "[up] $cmd" -ForegroundColor Cyan
Invoke-Expression $cmd

if ($LASTEXITCODE -ne 0) { throw "Compose up failed ($LASTEXITCODE)" }

Write-Host "[ps] Containers:" -ForegroundColor Cyan
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
