# Smoke test the adaptation recommend-next endpoint via PowerShell
param(
    [string]$BaseUrl = "http://localhost:8001",
    [string]$LearnerId = "learner-demo"
)

$body = @{ learner_id = $LearnerId } | ConvertTo-Json
Write-Host "POST $BaseUrl/v1/adaptation/recommend-next"
try {
    $resp = Invoke-RestMethod -Uri "$BaseUrl/v1/adaptation/recommend-next" -Method Post -Body $body -ContentType 'application/json'
    Write-Host "Recommendation:" ($resp | ConvertTo-Json -Depth 5)
} catch {
    Write-Error $_
    exit 1
}
