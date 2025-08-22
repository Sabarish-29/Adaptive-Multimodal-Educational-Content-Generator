# Performance Baseline: Sessions + Adaptation Mix

Date: 2025-08-19
Environment: Local dev (single workstation), Python 3.11, FastAPI uvicorn default workers, no Redis, in-memory fallback where applicable.

Tool: k6 (script `loadtests/sessions_adaptation_mix.js`)
Command Example:
```
k6 run loadtests/sessions_adaptation_mix.js --vus 20 --duration 1m \
  -e ADAPTATION_URL=http://localhost:8001 -e SESSIONS_URL=http://localhost:8002
```

## Target SLOs (Initial)
- Adaptation recommend-next p95 latency < 800ms (under light load)
- Error ratio < 1%
- Sessions create 95th < 150ms

## Collected Metrics (Placeholder Example)
| Metric | Observed | Target | Status |
|--------|----------|--------|--------|
| Adaptation p95 latency | TBD | <800ms | Pending |
| Adaptation error % | TBD | <1% | Pending |
| Session create p95 | TBD | <150ms | Pending |
| Throughput (req/s adaptation) | TBD | n/a | - |

Populate the placeholders by pasting k6 summary output and Prometheus query results:
```
histogram_quantile(0.95, sum(rate(adaptation_request_latency_ms_bucket[5m])) by (le))
rate(adaptation_requests_total{status!="200"}[5m]) / rate(adaptation_requests_total[5m])
histogram_quantile(0.95, sum(rate(sessions_create_latency_seconds_bucket[5m])) by (le))
```

## Methodology
1. Warm-up 30s (discard metrics) – future improvement: run with separate stage.
2. Steady 60s collection at fixed VUs.
3. Observe resource usage (`kubectl top pods` or local OS metrics).
4. Record any spikes or GC pauses.

## Next Steps
- Add staged ramp (5->20->40 VUs) and capture scaling curve.
- Introduce Redis to measure caching impact.
- Run in CI nightly (optional) with reduced VUs and compare drift (alert if >20% regression p95).
- Add environment tag to trends for multi-env dashboarding.
