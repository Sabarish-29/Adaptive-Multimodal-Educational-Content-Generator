# Recommendations Service

Phase 5 (Steps 1-14) implementation with Mongo persistence.

## Features
- Data contracts: ContentMeta, LearnerState, RecommendationItem, RecommendationResponse.
- Heuristic scoring combining topic_gap, freshness, difficulty_match, diversity_penalty.
- Deterministic experiment variant assignment (control vs explore) via SHA256 hash partition.
- API endpoints:
  - `GET /v1/recommendations/{learnerId}?limit=N` returns ranked list.
  - `POST /v1/recommendations/{learnerId}/state` updates mastery & recent content ids.
  - `GET /healthz` health check.
- Mongo-backed persistence for content (`recs_content`) and learner state (`recs_learners`) with in-memory read-through/write-through cache.

## Environment Weights
```
REC_W_TOPIC_GAP=0.5
REC_W_FRESHNESS=0.2
REC_W_DIFF_MATCH=0.2
REC_W_DIVERSITY_PEN=0.1
REC_TARGET_DIFFICULTY=3
REC_FRESHNESS_DAYS=30
REC_EXPERIMENT_KEY=rec_v1
RECS_MONGODB_URI=mongodb://localhost:27017/edu
RECS_MONGODB_DB=edu
RECS_CACHE_TTL_MS=180000
RECOMMENDATIONS_ENABLED=true
ALLOW_FORCE_VARIANT=0
```

## Run
```
uvicorn recommendations.main:app --reload --port 8090
```

## Tests
```
pytest -q services/recommendations/tests/test_recommendations.py
```

## Next Steps
- Persist content & learner state (Mongo) + cache layer.
- Add impression/click telemetry emission.
- Integrate into web frontend panel.
- Introduce variant-specific weighting adjustments.
- Cold-start strategy improvements.
