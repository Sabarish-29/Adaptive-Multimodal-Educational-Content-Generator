# Metrics Reference

## Adaptation Service
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| adaptation_requests_total | Counter | method, path, status | Total HTTP requests |
| adaptation_request_latency_ms | Histogram | (none) | Request latency in ms |
| adaptation_feedback_total | Counter | (none) | Feedback events processed |

## Content Generation Service
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| contentgen_bundles_total | Counter | (none) | Bundles generated (non-cached) |
| contentgen_bundles_cached_total | Counter | (none) | Bundles served from Redis/Mongo cache |
| contentgen_captions_total | Counter | (none) | Captions generated |
| contentgen_tts_total | Counter | (none) | TTS outputs generated |

## Sessions Service
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| sessions_started_total | Counter | (none) | Sessions started |
| session_events_total | Counter | (none) | Events ingested |

## Planned Future Metrics
- contentgen_eval_fail_total
- contentgen_tokens_histogram
- adaptation_policy_switch_total
- rag_query_latency_ms

## Scraping
All implemented services expose `/metrics` (sessions metrics endpoint pending). Enable Prometheus annotations via Helm value `prometheusScrape: true`.
