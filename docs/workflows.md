# Workflows

## Lesson Generation
1. Request POST /v1/generate/lesson with learner_id, unit_id, objectives[]
2. RAG service retrieves relevant docs + embeddings.
3. contentgen orchestrates: prompt LLM with grounded context.
4. Visuals: optional image gen; captions via captioner.
5. Audio: TTS generated for text blocks.
6. Bundle assembled with provenance + hashes.
7. eval_safety runs checks (reading level, toxicity, PII, a11y completeness).
8. If pass -> store content_bundles; else -> educator moderation queue.

## Session & Adaptation
1. POST /v1/sessions to start; creates session doc.
2. Client opens SSE GET /v1/sessions/{id}/live.
3. Events (answers, focus, hint) POST /v1/sessions/{id}/events.
4. adaptation service consumes recent context (Redis + MongoDB) -> bandit recommend.
5. SSE stream pushes next activity recommendation.
6. Feedback POST /v1/adaptation/feedback updates posterior (Thompson) or statistics (UCB).

## Moderation & Safety
1. After generation, eval_safety flags issues with severity.
2. Educator dashboard fetches flagged items via GET moderation endpoints.
3. Educator can approve/regenerate (future phase).

## Analytics
1. Periodic aggregation job (cron / Celery beat) computes progress & modality effectiveness.
2. GET /v1/analytics/learner/{id}/progress returns normalized metrics.
3. Accessibility compliance aggregated from evaluations.

## A/B Experiments
1. experiments collection defines variants.
2. adaptation policy attaches experiment variant_id in recommendations.
3. Feedback updates metrics per variant.
