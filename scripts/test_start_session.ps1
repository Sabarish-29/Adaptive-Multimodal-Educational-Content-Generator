# Create a session (learner_id + unit_id)
param(
  # Base URL should point either directly to sessions service (e.g. http://localhost:8003)
  # OR to the gateway sessions path (e.g. http://localhost:9000/api/sessions)
  [string]$BaseUrl = $( if($env:SESSIONS_TEST_BASE){ $env:SESSIONS_TEST_BASE } else { 'http://localhost:9000/api/sessions' } ),
  [string]$LearnerId = "demo-1",
  [string]$UnitId = "u1"
)

$payload = @{ learner_id = $LearnerId; unit_id = $UnitId } | ConvertTo-Json -Compress
if($BaseUrl -match '/v1/sessions$'){
  # Allow user to pass full endpoint root ending in /v1/sessions
  $endpoint = $BaseUrl
} else {
  $endpoint = "$BaseUrl/v1/sessions"
}
Write-Host "POST $endpoint -> $payload"
try {
  $resp = Invoke-RestMethod -Uri $endpoint -Method Post -ContentType application/json -Body $payload
} catch {
  Write-Error "Request failed: $($_.Exception.Message)"
  throw
}
Write-Host "Session ID:" $resp.session_id
