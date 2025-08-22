# Runbook: Adaptation Recommend-Next Elevated Error Ratio

Alert: `adaptation:recommendation:high_error_ratio`

## Impact
Learner recommendations degrade or fail, potentially halting session progression and lowering engagement metrics.

## Common Causes
1. Downstream datastore latency (Mongo, Redis) causing timeouts.
2. Code regression in scoring / sampling logic.
3. Resource exhaustion (CPU throttling, memory OOM restarts).
4. Burst traffic exceeding rate limits (429 cascading as errors upstream).
5. External service dependency outage (future integrations).

## Quick Triage
1. Confirm error ratio via metrics:
```
histogram_quantile(0.95, sum(rate(adaptation_request_latency_ms_bucket[5m])) by (le))
sum(rate(adaptation_call_latency_seconds_count{status!="ok"}[5m])) / sum(rate(adaptation_call_latency_seconds_count[5m]))
```
2. Inspect recent logs:
```
kubectl logs deploy/adaptation -n prod --tail=300 | grep -i error
```
3. Check pod health & restarts:
```
kubectl get pods -l app=adaptation -n prod
kubectl describe pod <pod>
```
4. Datastore connectivity:
```
kubectl exec -it <adaptation-pod> -- mongo $MONGODB_URI --eval 'db.runCommand({ ping: 1 })'
```
5. Redis latency / connectivity (if enabled):
```
kubectl exec -it <adaptation-pod> -- redis-cli -u $REDIS_URL ping
```

## Remediation Steps
| Scenario | Action |
|----------|--------|
| High latency + CPU throttling | Increase resources or tune HPA (scale out); confirm GC pressure. |
| Regression after deploy | Roll back to previous image tag (`kubectl rollout undo deploy/adaptation`). |
| Redis unavailable | Fallback to in-memory debounce cache (already automatic); monitor increased latency. |
| Mongo primary failover | Wait for election, ensure connection string has replica set & retryWrites; if misconfigured, update secret & restart. |
| Rate limiting spiking | Investigate client behavior; adjust limiter temporarily; enforce auth / blocking if abuse. |

## Verification
- Error ratio < 5% over 15m.
- p95 latency within SLO (< 0.8s example) over last 15m.
- No sustained increase in 5xx logs.

## Post-Incident
- Root cause analysis (5 whys) documented.
- Add missing instrumentation / defensive checks.
- Update SLO / capacity plan if load pattern changed.

## Related Alerts
- `sessions:recommendation_stream:stalled`
- `adaptation:recommendation:high_p95_latency`
- `global:rate_limit:spike`

## References
- `docs/ALERTING_RULES.md`
- `docs/runbooks/rate_limit_spike.md`
