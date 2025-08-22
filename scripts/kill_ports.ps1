<#!
Kills processes listening on specified TCP ports (default core service + gateway ports).
Usage:
  powershell -ExecutionPolicy Bypass -File .\scripts\kill_ports.ps1 -Ports 8001,8002,8003,8004,9000
Optional:
  -DryRun   Show what would be killed without stopping processes.
#>
param(
  [Parameter(Position=0)]
  [object]$Ports = @(8001,8002,8003,8004,9000),
  [switch]$DryRun
)

# Normalize Ports input to an int array (supports: array, space-separated, or comma-separated string)
if($Ports -is [string]){
  $Ports = $Ports -split '[, ]+' | Where-Object { $_ -and ($_ -match '^\\d+$') }
}
elseif($Ports -isnot [System.Collections.IEnumerable]){
  $Ports = @($Ports)
}
$Ports = $Ports | ForEach-Object { try { [int]$_ } catch { } } | Where-Object { $_ }
$killed = @()
foreach($p in $Ports){
  try {
    $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction Stop
  } catch { continue }
  foreach($c in $conns){
  $procId = $c.OwningProcess
  if(-not $procId){ continue }
  $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if($proc){
      if($DryRun){
        Write-Host "DRYRUN would kill PID $procId ($($proc.ProcessName)) on port $p" -ForegroundColor Yellow
      } else {
        try {
          Stop-Process -Id $procId -Force -ErrorAction Stop
          Write-Host "Killed PID $procId ($($proc.ProcessName)) on port $p" -ForegroundColor Cyan
          $killed += $procId
        } catch {
          Write-Warning "Failed to kill PID $procId on port $p"
        }
      }
    }
  }
}
if(-not $DryRun){
  if($killed.Count -gt 0){
    $joined = [string]::Join(',', ($killed | Sort-Object -Unique))
  } else {
    $joined = '(none)'
  }
  Write-Host "Done. Killed: $joined"
}
