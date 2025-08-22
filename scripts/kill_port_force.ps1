<#
Force kill any processes listening on a given TCP port using netstat + taskkill.
Usage:
  powershell -ExecutionPolicy Bypass -File .\scripts\kill_port_force.ps1 -Port 8003
#>
param(
  [Parameter(Mandatory=$true)][int]$Port,
  [switch]$VerboseList
)
Write-Host "[kill_port_force] Scanning for listeners on port $Port" -ForegroundColor Cyan
$lines = netstat -ano | Select-String ":$Port" | ForEach-Object { $_.ToString() }
if(-not $lines){ Write-Host "No netstat matches for :$Port" -ForegroundColor Yellow; exit 0 }
$pids = @{}
foreach($l in $lines){
  if($l -match "LISTENING\s+(\d+)$"){
    $procId=[int]$matches[1]
    $pids[$procId]=1
  }
}
if($pids.Keys.Count -eq 0){ Write-Host "No LISTENING entries parsed for port $Port" -ForegroundColor Yellow; exit 0 }
Write-Host "Found PIDs: $([string]::Join(',', $pids.Keys))" -ForegroundColor Gray
foreach($procId in $pids.Keys){
  try {
    Write-Host "Killing PID $procId" -ForegroundColor Magenta
    taskkill /PID $procId /F | Out-Null
  } catch { Write-Warning "Failed taskkill PID $procId" }
}
Start-Sleep -Milliseconds 500
$remain = netstat -ano | Select-String ":$Port" | ForEach-Object { $_.ToString() } | Where-Object { $_ -match 'LISTENING' }
if($remain){
  $remainJoined = $remain -join '; '
  Write-Warning "Still detected listeners on $Port :: $remainJoined"
  exit 1
}
Write-Host "Port $Port free." -ForegroundColor Green
