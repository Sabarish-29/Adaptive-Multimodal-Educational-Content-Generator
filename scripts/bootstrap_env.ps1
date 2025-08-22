param(
  [switch]$Dev
)

Write-Host "[bootstrap] Creating venv (.venv) with Python 3.11..."
if (Test-Path .venv) { Write-Host "[bootstrap] Existing venv detected" } else { py -3.11 -m venv .venv }

. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip wheel > $null

# Aggregate requirements from each service
$reqFiles = Get-ChildItem services -Recurse -Filter requirements.txt

Write-Host "[bootstrap] Installing service requirements..."
foreach ($f in $reqFiles) {
  Write-Host " -> $($f.FullName)"; pip install -r $f.FullName
}

if ($Dev) {
  if (Test-Path requirements-dev.txt) { pip install -r requirements-dev.txt }
  pip install pytest
}

Write-Host "[bootstrap] Done. Activate with:`n  .\\.venv\\Scripts\\Activate.ps1"
