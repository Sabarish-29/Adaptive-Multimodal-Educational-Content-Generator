# Runbook: Sessions SSE Stream Stalled

Alert: `sessions:recommendation_stream:stalled`

## Impact
Learners receive no live recommendations; UI may appear frozen or fallback content shown. Engagement and progression blocked.

## Hypotheses
1. Adaptation service unavailable or high error ratio.
2. Sessions service internal loop blocked (event loop saturation, deadlock, exception).
3. Upstream network/DNS issue between sessions and adaptation.
4. Rate limiting / circuit breaker (future) trip stopping outbound adaptation calls.
5. FAST_TEST_MODE inadvertently enabled in production (synthetic path generating none due to misconfig?).

## Diagnostics
### 1. Check metrics
- `sum(rate(sessions_recommendation_events_total[5m]))` should be > 0.
- `job:adaptation_recommend_error_ratio:5m` high?
- `encryption_mode` unexpected change (if deploy regression causing broader failure).

### 2. Logs
```
# Sessions recent errors
grep -i 'adaptation_exception' sessions.log | tail -50
# Adaptation latency & errors
kubectl logs deploy/adaptation -n prod --tail=200 | grep -i error
```

### 3. Health endpoints
```
curl -s $SESSIONS_URL/healthz
curl -s $ADAPTATION_URL/healthz
```

### 4. Event loop saturation
Check pod CPU & restarts:
```
kubectl top pod -l app=sessions -n prod
kubectl describe pod <pod> -n prod
```

### 5. Network / DNS
```
kubectl exec -it <sessions-pod> -- curl -s -o /dev/null -w '%{http_code}' $ADAPTATION_URL/v1/adaptation/recommend-next -d '{"learner_id":"probe"}' -H 'Content-Type: application/json'
```

## Remediation
1. If adaptation failing: roll back latest adaptation deployment or scale up (HPA) if saturation.
2. If sessions logs show repeated exceptions in streaming loop: deploy hotfix or rollback last sessions image.
3. If network issue (DNS 5xx/timeout): restart CoreDNS pods, verify service endpoints, or failover cluster networking.
4. Temporarily enable synthetic fallback (set `FAST_TEST_MODE=true`) ONLY as emergency mitigation; document and revert.
5. If deployment regression: perform rollback per `ROLLBACK_CANARY.md` playbook.

## Postmortem Data Collection
- Grafana dashboard screenshots (latency, events rate, error ratio).
- Logs excerpt of first error burst.
- Deployment diff (git SHAs) between last known good & bad.
- Timeline of detection & actions.

## Related Alerts
- `adaptation:recommendation:high_error_ratio`
- `global:rate_limit:spike`

## Exit Criteria
Event rate restored (`sessions_recommendation_events_total` increasing) and p95 latency within SLO for >30m.
