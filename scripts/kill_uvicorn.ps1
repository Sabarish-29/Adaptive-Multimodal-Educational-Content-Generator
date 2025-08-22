<#
Kills all running uvicorn server processes (and their workers) by matching 'uvicorn' in the command line.
Use when stray reload watcher processes keep ports bound (Windows).
#>
param(
  [switch]$DryRun
)
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uvicorn' }
if(-not $procs){ Write-Host "No uvicorn processes found."; return }
foreach($p in $procs){
  $id = $p.ProcessId
  $cmd = ($p.CommandLine -replace '\s+',' ') -replace '(^.{0,120}).*','$1...'
  if($DryRun){
    Write-Host "DRYRUN would kill PID $id : $cmd" -ForegroundColor Yellow
  } else {
    try {
      Stop-Process -Id $id -Force -ErrorAction Stop
      Write-Host "Killed uvicorn PID $id : $cmd" -ForegroundColor Cyan
    } catch {
      Write-Warning "Failed to kill PID $id"
    }
  }
}
