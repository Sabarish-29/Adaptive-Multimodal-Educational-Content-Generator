# Runbook: Redis Outage

## Symptoms
- Sudden drop in cache hit metrics
- Increased latency in content generation or adaptation
- Errors in logs about Redis connection

## Immediate Actions
1. Confirm connectivity: `redis-cli PING`.
2. Check pod/status (Kubernetes): `kubectl get pods -l app=redis`.
3. Fallback behavior: Services continue (caching disabled). Rate limiting falls back to in-memory (risk: uneven enforcement across replicas).

## Mitigation
- Scale down replicas of rate-limited services if uneven enforcement problematic.
- Restart Redis pod / deployment.
- If persistence enabled, verify PVC bound.

## Postmortem Data
- adaptation_recommendation_cache_hits_total
- contentgen_bundles_cached_total
- Redis container logs

## Preventative
- Add Redis readiness & liveness probes.
- Enable Redis AUTH and network policies.
