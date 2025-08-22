# Service SLOs & Error Budgets

## Overview
Defines latency & availability objectives for core user flows.

| SLO | Target | Metric Source | Notes |
|-----|--------|---------------|-------|
| Adaptation request availability | 98% success (non-error status) per 30d | adaptation_call_latency_seconds_count (status label) | status in {ok} / all |
| Adaptation p95 latency | <500ms 95% of the time (5m windows) | adaptation_call_latency_seconds_bucket | Only status="ok" |
| Session event ingest p95 latency | <300ms | session_event_ingest_latency_seconds_bucket | status="accepted" |
| Session creation p95 latency | <400ms | sessions_create_latency_seconds_bucket | |
| SSE recommendation stream availability | 99% (no circuit open >5 consecutive minutes) | sessions_adaptation_circuit_state | Derived from absence of sustained state=1 |
| Rate limit stability | <2% of requests rate limited (rolling 1h) | sessions_rate_limited_total | increase/total requests |

## Error Budgets
Using 30d window.

| SLO | Budget | Fast burn threshold | Slow burn threshold |
|-----|--------|---------------------|---------------------|
| Adaptation availability 98% | 2% | >5% errors over 10m (page) | >2% errors over 1h (warn) |
| SSE availability 99% | 1% | circuit open 10m (page) | open 5m (warn) |

## Alert Mapping
See `configs/prometheus_alerts.yml` for expressions.

## Implementation Notes
- Latency histograms aggregated with `sum(rate(metric_bucket[5m])) by (le)` then `histogram_quantile`.
- Availability derived from non-ok status proportion.
- Circuit state gauge sampled; sustained `==1` indicates outage.
- Rate limit anomaly compares short window to scaled long window baseline.

## Future Enhancements
- Add burn-rate multi-window for session ingest latency.
- Include 99th percentile guardrails.
- Integrate synthetic probe metrics once available.
