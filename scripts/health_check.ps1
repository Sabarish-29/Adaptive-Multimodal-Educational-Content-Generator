<#
Health check script for core services + gateway.
Usage:
  powershell -ExecutionPolicy Bypass -File .\scripts\health_check.ps1
#>
param(
  [int[]]$Ports = @(8000,8001,8002,8003,8005,8006,8007,8008),
  [int]$GatewayPort = 9000,
  [switch]$SkipGateway
)
Write-Host "Checking health endpoints..." -ForegroundColor Cyan
foreach($p in $Ports){
  try { $resp = Invoke-WebRequest "http://localhost:$p/healthz" -UseBasicParsing -TimeoutSec 3; $code=$resp.StatusCode }
  catch { $code='ERR' }
  Write-Host ("{0}`t-> {1}" -f $p,$code)
}
if (-not $SkipGateway) {
  try { $gw = Invoke-WebRequest "http://localhost:$GatewayPort/healthz" -UseBasicParsing -TimeoutSec 3; $gwc=$gw.StatusCode }
  catch { $gwc='ERR' }
  Write-Host ("{0}`t-> {1}" -f $GatewayPort,$gwc)
} else {
  Write-Host ("{0}`t-> skipped" -f $GatewayPort)
}
Write-Host "Done." -ForegroundColor Green
