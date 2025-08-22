# Operations & Runtime Guide

## Environment Variables (Key Runtime)
| Variable | Service(s) | Default | Purpose |
|----------|------------|---------|---------|
| MONGODB_URI | all | mongodb://localhost:27017/edu | Mongo connection string |
| MONGODB_DB | all | edu | Database name |
| REDIS_URL | contentgen, adaptation | redis://localhost:6379/0 | Redis cache (optional) |
| CONTENTGEN_CACHE_TTL | contentgen | 300 | Seconds to retain bundle cache entries |
| ADAPTATION_DEBOUNCE_TTL | adaptation | 10 | Seconds to reuse last recommendation per learner |
| CONTENTGEN_RATE_PER_MIN | contentgen | 90 | Rate limit per minute for POST/PUT/PATCH |
| SESSIONS_RATE_PER_MIN | sessions | 120 | Rate limit per minute for POST/PUT/PATCH |
| ADAPTATION_RATE_PER_MIN | adaptation | 120 | Rate limit per minute for POST/PUT/PATCH |
| PROFILES_RATE_PER_MIN | profiles | 60 | Rate limit per minute for POST/PUT/PATCH |
| FEATURE_CAPTION | contentgen | false | Enable caption generation |
| FEATURE_TTS | contentgen | false | Enable TTS generation |
| FEATURE_FIELD_ENCRYPTION | contentgen | false | Enable pluggable encryption interface (current placeholder XOR/base64) |
| OTEL_ENABLED | adaptation (others future) | false | Enable OpenTelemetry tracing |

## Request Correlation
Send `X-Request-ID` header to correlate logs across services. If absent, a UUID is generated. SSE streams append `?rid=` query parameter since custom headers aren't supported.

## Rate Limiting
Redis-backed sliding window per-minute limiter (mutating endpoints). Falls back to in-memory if Redis unavailable. Exceed returns HTTP 429 with `{ "detail": "rate_limit_exceeded" }`. Remaining quota via `X-RateLimit-Remaining` header.

## Caching Layers
- Content Bundles: Redis first-level cache keyed by input payload hash; falls back to Mongo. Cache miss triggers generation and storage.
- Adaptation Recommendations: Short-lived Redis entry to smooth bursty calls from UI polling or multiple tabs.
If Redis is unavailable or `aioredis` not installed, logic silently degrades (no caching).

## Metrics Endpoints
Each service (where implemented) exposes `/metrics` in Prometheus exposition format. Key metrics:
- adaptation_requests_total{method,path,status}
- adaptation_request_latency_ms (Histogram)
- adaptation_feedback_total
- contentgen_bundles_total
- contentgen_bundles_cached_total (only increments on cache hits)
- contentgen_captions_total
- contentgen_tts_total
- sessions_started_total
- session_events_total

## Logging
Structured one-line JSON per request including: timestamp, service code, method, path, status, duration_ms, request_id.

## Encryption Interface Notice
`FEATURE_FIELD_ENCRYPTION` activates a pluggable encryption interface currently wired to a reversible XOR/base64 placeholder (`SimpleObfuscator`). This is NOT cryptographic protection. Replace with a KMS-backed AEAD implementation (e.g., AES-GCM) before production.

## Failure & Degradation Modes
| Scenario | Behavior |
|----------|----------|
| Redis down | Cache operations skipped (no exceptions propagated) |
| OpenTelemetry exporter missing | OTEL_DISABLED fallback silently |
| Caption/TTS adapter missing | Feature returns 400 (disabled) or 500 (adapter unavailable) |
| Evaluation service down | Content generation proceeds (fail-open initial phase) |

## Future Hardening (Planned)
- Distributed tracing propagation into model adapters
- Circuit breakers for external adapter calls
- Token-level cost metrics, standardized error taxonomy
- Strong cryptographic field encryption (KMS-managed) replacing placeholder

