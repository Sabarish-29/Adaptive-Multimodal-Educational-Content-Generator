# Security & Privacy

## AuthN/Z
- OAuth2/OIDC (provider configurable). JWT (RS256) access tokens; refresh tokens managed at IdP.
- RBAC roles: learner, guardian, educator, admin. Future ABAC with accommodations & consent scopes.

## Data Protection
- Field-level encryption candidates: assessments.responses, consent.records.
- `FEATURE_FIELD_ENCRYPTION` activates a pluggable encryption interface currently backed by a reversible XOR/base64 placeholder (`SimpleObfuscator`). NOT cryptographic; replace with KMS-managed AEAD (AES-GCM) before production.
- KMS integration via env stubs; envelope encryption planned.
- Event TTL (90 days) enforced via MongoDB TTL index.
- Redis cache stores only derived / non-sensitive content bundle copies (hash-keyed); avoid inserting raw PII there.

## PII Minimization
- Store only necessary demographic fields. No raw free-form PII allowed in content generation prompt context.

## Audit Logging & Correlation
- Generation requests (prompt hashes, model_id, policy_id)
- Adaptation decisions (arm, expected reward, variant)
- Moderation actions (approve, reject, regenerate)
- Session events (type classification)
- `X-Request-ID` propagated across services for cross-log correlation; logs are structured JSON.

## Compliance Roadmap
- COPPA / FERPA alignment (parental consent workflow)
- GDPR / data residency (region-specific MongoDB clusters future)

## Secrets
- All secrets via environment variables; never commit.
- .env.example provided; production uses managed secret store.

## Threat Mitigation
- Rate limiting at gateway AND per-service (Redis-backed sliding window with fallback) for POST/PUT/PATCH endpoints.
- Input validation via Pydantic & JSON Schema.
- Content filtering (toxicity, PII) pre-display.
- Dependency scanning (pip-audit, npm audit) in CI.
- Redis optional: if compromised, only cached content (no secrets). Use network ACLs & auth for production Redis.
- Request ID correlation improves traceability of suspicious sequences.

## Threat Model (Baseline)
| Asset | Actor | Threat | Mitigation |
|-------|-------|--------|------------|
| Learner profiles | External attacker | Unauthorized access | Auth (JWT), role checks, least privilege |
| Content bundles | Malicious user | Prompt injection / unsafe output | RAG grounding, eval_safety filters |
| Adaptation policy | Insider | Biasing recommendations | Audit logs, policy versioning |
| Events (PII risk) | External attacker | Enumeration via IDs | Opaque ObjectIds, rate limiting |
| Redis cache entries | Insider / attacker with access | Harvest of cached bundles | Avoid PII in cached fields, restrict Redis access, short TTL |
| Model adapters | Supply chain | Malicious image/weights | Signature verification (future), pinned images |
| MongoDB data | Ransomware | Data exfil/encrypt | Backups, least privilege network ACLs |

## Incident Response
- On detection of safety model drift: disable variant via policy flag.
- Data breach runbook (see runbooks folder TBD).
