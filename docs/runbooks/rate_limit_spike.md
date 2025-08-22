# Runbook: Rate Limit Spike

## Symptoms
- Surge in 429 responses
- Limiter deny counters (future) rising
- User complaints of blocked actions

## Immediate Actions
1. Inspect logs for offending IP/user Authorization header hash.
2. Check X-RateLimit-Remaining in responses to gauge headroom.
3. Temporarily raise *_RATE_PER_MIN if legitimate traffic surge (environment variable + redeploy).

## Analysis
- Distinguish attack vs organic growth.
- Review adaptation_recommendations_total vs feedback events for anomaly.

## Mitigation
- Block abusive tokens/IP at ingress.
- Enable WAF / API gateway rules.

## Follow-up
- Tune per-endpoint granular limits.
- Add deny counter metric & alert.
