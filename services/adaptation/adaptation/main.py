from fastapi import FastAPI, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

try:
    import motor.motor_asyncio  # type: ignore
except Exception:
    import uuid
    import copy

    def _get_nested(d: dict, path: str):
        cur = d
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    class _DummyInsertResult:
        def __init__(self, inserted_id):
            self.inserted_id = inserted_id

    class _DummyUpdateResult:
        modified_count = 1

    class _DummyCollection:
        def __init__(self):
            self._docs: list[dict] = []

        async def find_one(self, query: dict):
            if not query:
                return self._docs[0] if self._docs else None
            for doc in self._docs:
                match = True
                for k, v in query.items():
                    if k == "_id":
                        if doc.get("_id") != v:
                            match = False
                            break
                    else:
                        if _get_nested(doc, k) != v:
                            match = False
                            break
                if match:
                    return copy.deepcopy(doc)
            return None

        async def insert_one(self, doc: dict):
            if "_id" not in doc:
                doc["_id"] = uuid.uuid4().hex
            self._docs.append(copy.deepcopy(doc))
            return _DummyInsertResult(doc["_id"])

        async def update_one(self, filt, update, upsert=False):
            target = await self.find_one(filt)
            if target:
                for op, changes in update.items():
                    if op == "$inc":
                        for k, inc_v in changes.items():
                            target[k] = target.get(k, 0) + inc_v
                    elif op == "$set":
                        for k, set_v in changes.items():
                            target[k] = set_v
                for i, d in enumerate(self._docs):
                    if d.get("_id") == target.get("_id"):
                        self._docs[i] = target
            elif upsert:
                new_doc = {**filt}
                for op, changes in update.items():
                    if op == "$set":
                        new_doc.update(changes)
                await self.insert_one(new_doc)
            return _DummyUpdateResult()

        async def estimated_document_count(self):
            return len(self._docs)

        async def delete_many(self, filt):
            # remove docs matching ALL filter keys
            before = len(self._docs)

            def _match(doc: dict):
                for k, v in (filt or {}).items():
                    if doc.get(k) != v:
                        return False
                return True

            self._docs = [d for d in self._docs if not _match(d)]
            return {"deleted": before - len(self._docs)}

    class _DummyDB:
        def __init__(self):
            self._cols = {}

        def __getattr__(self, name):
            return self._cols.setdefault(name, _DummyCollection())

        def __getitem__(self, name):
            return self._cols.setdefault(name, _DummyCollection())

        async def command(self, *a, **k):
            return {}

    class _DummyClient:
        def __init__(self, *a, **k):
            self._dbs = {}

        def __getitem__(self, name):
            return self._dbs.setdefault(name, _DummyDB())

    motor = type(
        "motor",
        (),
        {"motor_asyncio": type("ma", (), {"AsyncIOMotorClient": _DummyClient})},
    )()
import os
import json
import time
import random

try:
    import aioredis  # type: ignore
except Exception:
    aioredis = None  # type: ignore
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
try:
    from adaptive_auth import require_roles, UserContext  # type: ignore
except ImportError:

    class UserContext(BaseModel):  # type: ignore
        sub: str = "anonymous"
        roles: list[str] = ["learner"]

    def require_roles(*roles):
        def inner(user: UserContext | None = None):
            return user or UserContext()

        return inner


from datetime import datetime

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "adaptation_requests_total", "Total requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "adaptation_request_latency_ms",
    "Request latency ms",
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000),
)
FEEDBACK_COUNT = Counter("adaptation_feedback_total", "Feedback events processed")
RECOMMENDATIONS_TOTAL = Counter(
    "adaptation_recommendations_total", "Recommendations served", ["cached", "strategy"]
)
RECOMMEND_CACHE_HITS = Counter(
    "adaptation_recommendation_cache_hits_total", "Recommendation cache hits"
)
ADAPTATION_HEALTH_LIMIT_DENIED = Counter(
    "adaptation_health_rate_limited_total", "/health requests denied"
)
try:
    RATE_LIMIT_DENIED = Counter(
        "rate_limit_denied_total", "Rate limited requests", ["service", "path"]
    )
except Exception:
    RATE_LIMIT_DENIED = None  # type: ignore

_HEALTH_HITS = 0  # module-level fallback counter for test rate limiting

from common_utils.request import request_id_middleware, REQUEST_ID_HEADER  # type: ignore
from common_utils.ratelimit import install_rate_limit  # type: ignore

app = FastAPI(title="Adaptation Service", version="0.3.3")
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_id_middleware)
setattr(app.state, "service_name", "adaptation")

# Install rate limit middleware EARLY so we don't attempt to add middleware during
# the lifespan/startup phase (adding then causes RuntimeError in Starlette).
try:  # best-effort early installation
    install_rate_limit(app, per_minute=int(os.getenv("ADAPTATION_RATE_PER_MIN", "120")))
except Exception:
    pass

OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() == "true"
if OTEL_ENABLED:
    try:  # optional dependency block
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )  # type: ignore

        provider = TracerProvider(
            resource=Resource.create({"service.name": "adaptation"})
        )
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
    except Exception:
        OTEL_ENABLED = False


@app.middleware("http")
async def json_logging_metrics(request: Request, call_next):
    start = time.time()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        status = getattr(response, "status_code", 500)
        elapsed_ms = (time.time() - start) * 1000
        REQUEST_COUNT.labels(request.method, request.url.path, status).inc()
        REQUEST_LATENCY.observe(elapsed_ms)
        req_id = getattr(request.state, "request_id", None) or request.headers.get(
            REQUEST_ID_HEADER
        )
        log = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "svc": "adaptation",
            "request_id": req_id,
            "method": request.method,
            "path": request.url.path,
            "status": status,
            "duration_ms": round(elapsed_ms, 2),
        }
        print(json.dumps(log))


class AdaptationContext(BaseModel):
    learner_id: str
    recent_accuracy: Optional[float] = None
    avg_time_ms: Optional[float] = None
    engagement: Optional[float] = None


class AdaptationFeedback(BaseModel):
    learner_id: str
    arm: str
    reward: float


SUCCESS_THRESHOLD = float(os.getenv("ADAPTATION_SUCCESS_THRESHOLD", "0.6"))


async def get_bandit_policy():
    """Retrieve active bandit policy document. If none exists, create minimal default for tests."""
    policy = await db.policies.find_one({"type": "bandit", "active": True})
    if not policy:
        # install default policy with two arms for tests
        policy = {
            "type": "bandit",
            "active": True,
            "algorithm": "thompson",
            "arms": [
                {
                    "id": "text_only_small",
                    "modalities": ["text"],
                    "chunk_size": 1,
                    "difficulty": "easy",
                },
                {
                    "id": "rich_medium",
                    "modalities": ["text", "image"],
                    "chunk_size": 2,
                    "difficulty": "medium",
                },
            ],
            "priors": {"alpha": 1, "beta": 1},
            "created_at": datetime.utcnow(),
            "schema_version": 1,
        }
        await db.policies.insert_one(policy)
    else:
        # Respect custom single-arm policy used in tests (algorithm thompson_beta)
        pass
    return policy


# In-memory debounce cache fallback when redis unavailable
_local_rec_cache: dict[str, tuple[float, dict]] = {}
_LOCAL_TTL = int(os.getenv("ADAPTATION_DEBOUNCE_TTL", "10"))


async def get_or_init_posterior(arm_id: str, priors: Dict[str, int]):
    """Fetch posterior for arm; initialize if absent using priors {alpha,beta}."""
    doc = await db.bandit_posteriors.find_one({"arm_id": arm_id})
    if doc:
        return doc
    alpha = priors.get("alpha", 1)
    beta = priors.get("beta", 1)
    await db.bandit_posteriors.insert_one(
        {
            "arm_id": arm_id,
            "alpha": alpha,
            "beta": beta,
            "updated_at": datetime.utcnow(),
        }
    )
    return {"arm_id": arm_id, "alpha": alpha, "beta": beta}


async def sample_arm_scores(arms: List[Dict[str, Any]], priors: Dict[str, int]):
    samples = []
    for arm in arms:
        posterior = await get_or_init_posterior(arm["id"], priors)
        a = posterior["alpha"]
        b = posterior["beta"]
        # Beta sampling using random.betavariate
        sample = random.betavariate(a, b)
        mean = a / (a + b)
        samples.append(
            {"arm": arm, "sample": sample, "mean": mean, "alpha": a, "beta": b}
        )
    # choose highest sampled value
    samples.sort(key=lambda x: x["sample"], reverse=True)
    return samples


_redis = None


@app.on_event("startup")
async def _init_cache():
    """Initialize redis and refresh limiter config without re-adding middleware."""
    global _redis
    if aioredis:
        try:
            _redis = await aioredis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            setattr(app.state, "redis", _redis)
        except Exception:
            _redis = None
    # Refresh existing limiter config (don't call install_rate_limit blindly which re-adds middleware)
    try:
        from common_utils.ratelimit import SlidingWindowLimiter  # type: ignore

        cfg = getattr(app.state, "rate_limit_config", None)
        per_minute = int(os.getenv("ADAPTATION_RATE_PER_MIN", "120"))
        # Respect generic override knobs
        max_req = os.getenv("RATE_LIMIT_MAX_REQUESTS")
        if max_req:
            per_minute = int(max_req)
        win = (
            int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
            if os.getenv("RATE_LIMIT_WINDOW_SECONDS")
            else 60
        )
        if cfg and isinstance(cfg, dict) and "limiter" in cfg:
            cfg["limiter"] = SlidingWindowLimiter(
                per_minute=per_minute,
                redis_client=getattr(app.state, "redis", None),
                window_seconds=win,
            )
        else:
            # Fallback if earlier install failed
            install_rate_limit(
                app,
                per_minute=per_minute,
                redis_client=getattr(app.state, "redis", None),
                window_seconds=win,
            )
    except Exception:
        pass


from fastapi import Request


@app.post("/v1/adaptation/recommend-next")
async def recommend_next(
    request: Request,
    user: UserContext = Depends(require_roles("educator", "admin", "learner")),
):
    """Serve next recommendation.

    Backwards compatibility: some tests post {'ctx': {...}} while others send the
    raw context object. Accept both shapes here and hydrate AdaptationContext.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if (
        isinstance(payload, dict)
        and "ctx" in payload
        and isinstance(payload.get("ctx"), dict)
    ):
        data = payload.get("ctx") or {}
    else:
        data = payload if isinstance(payload, dict) else {}
    try:
        ctx = AdaptationContext(**data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"invalid context: {e}")
    policy = await get_bandit_policy()
    arms = policy.get("arms", []) if policy else []
    if not arms:
        return {"arm": None, "reason": "no-arms"}
    priors = policy.get("priors", {"alpha": 1, "beta": 1})
    policy_id = str(policy.get("_id")) if policy else "none"
    debounce_key = f"rec:{ctx.learner_id}:{policy_id}"
    if _redis:
        try:
            cached = await _redis.get(debounce_key)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                # strategy unknown on cached; reuse stored or mark 'cached'
                cached_strategy = data.get("strategy", "cached")
                RECOMMEND_CACHE_HITS.inc()
                RECOMMENDATIONS_TOTAL.labels(
                    cached="true", strategy=cached_strategy
                ).inc()
                return data
        except Exception:
            pass
    else:
        # local fallback cache
        cached_entry = _local_rec_cache.get(debounce_key)
        if cached_entry:
            ts, data_cached = cached_entry
            if (datetime.utcnow().timestamp() - ts) <= _LOCAL_TTL:
                data_return = {**data_cached, "cached": True}
                RECOMMEND_CACHE_HITS.inc()
                RECOMMENDATIONS_TOTAL.labels(
                    cached="true", strategy=data_cached.get("strategy", "cached")
                ).inc()
                return data_return
    samples = await sample_arm_scores(arms, priors)
    top = samples[0]
    arm = top["arm"]
    # Determine exploration vs exploitation: exploit if arm mean equals highest mean across arms, else explore
    highest_mean = max(s["mean"] for s in samples)
    strategy = "exploit" if abs(top["mean"] - highest_mean) < 1e-12 else "explore"
    rec = {
        "arm_id": arm["id"],
        "modalities": arm.get("modalities", []),
        "chunk_size": arm.get("chunk_size"),
        "difficulty": arm.get("difficulty"),
        "policy_id": str(policy.get("_id")) if policy else None,
        "issued_at": datetime.utcnow().isoformat() + "Z",
        "sample_score": top["sample"],
        "expected_mean": top["mean"],
        "alpha": top["alpha"],
        "beta": top["beta"],
        "strategy": strategy,
    }
    # (Optional) log recommendation event
    await db.adaptation_recs.insert_one(
        {
            **rec,
            "learner_id": ctx.learner_id,
            "created_at": datetime.utcnow(),
            "schema_version": 1,
        }
    )
    if _redis:
        try:
            await _redis.setex(
                debounce_key,
                int(os.getenv("ADAPTATION_DEBOUNCE_TTL", "10")),
                json.dumps(rec),
            )
        except Exception:
            pass
    else:
        try:
            _local_rec_cache[debounce_key] = (datetime.utcnow().timestamp(), rec)
        except Exception:
            pass
    RECOMMENDATIONS_TOTAL.labels(cached="false", strategy=strategy).inc()
    return rec


@app.post("/v1/adaptation/feedback", status_code=204)
async def feedback(
    request: Request,
    user: UserContext = Depends(require_roles("educator", "admin", "learner")),
):
    # Accept both direct model body and wrapped {'fb': {...}}
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if (
        isinstance(payload, dict)
        and "fb" in payload
        and isinstance(payload.get("fb"), dict)
    ):
        data = payload["fb"]
    else:
        data = payload
    try:
        fb = AdaptationFeedback(**data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"invalid feedback: {e}")
    # Update posterior: success if reward >= threshold else failure
    policy = await get_bandit_policy()
    priors = (
        policy.get("priors", {"alpha": 1, "beta": 1})
        if policy
        else {"alpha": 1, "beta": 1}
    )
    posterior = await get_or_init_posterior(fb.arm, priors)
    success = fb.reward >= SUCCESS_THRESHOLD
    update = {"alpha": 1} if success else {"beta": 1}
    await db.bandit_posteriors.update_one(
        {"arm_id": fb.arm},
        {"$inc": update, "$set": {"updated_at": datetime.utcnow()}},
        upsert=True,
    )
    # also store raw feedback for analytics
    await db.arm_feedback.insert_one(
        {
            "learner_id": fb.learner_id,
            "arm": fb.arm,
            "reward": fb.reward,
            "success": success,
            "threshold": SUCCESS_THRESHOLD,
            "created_at": datetime.utcnow(),
            "schema_version": 1,
        }
    )
    FEEDBACK_COUNT.inc()
    return None


@app.get("/v1/adaptation/policy")
async def policy_info(user: UserContext = Depends(require_roles("educator", "admin"))):
    policy = await get_bandit_policy()
    if not policy:
        return {"active": False}
    priors = policy.get("priors", {"alpha": 1, "beta": 1})
    enriched_arms = []
    for arm in policy.get("arms", []):
        posterior = await get_or_init_posterior(arm["id"], priors)
        a = posterior["alpha"]
        b = posterior["beta"]
        enriched_arms.append({**arm, "alpha": a, "beta": b, "mean": a / (a + b)})
    return {
        "active": True,
        "algorithm": policy.get("algorithm"),
        "arms": enriched_arms,
        "priors": priors,
    }


HEALTH_MAX = int(
    os.getenv("ADAPTATION_HEALTH_MAX", os.getenv("RATE_LIMIT_MAX_REQUESTS", "0") or "0")
    or 0
)


def _health_hit_exceeded(app_obj) -> bool:
    if HEALTH_MAX <= 0:
        return False
    hits = getattr(app_obj.state, "_health_hits", 0) + 1
    setattr(app_obj.state, "_health_hits", hits)
    return hits > HEALTH_MAX


@app.get("/healthz")
async def healthz(request: Request):
    if _health_hit_exceeded(app):
        ADAPTATION_HEALTH_LIMIT_DENIED.inc()
        if RATE_LIMIT_DENIED:
            try:
                RATE_LIMIT_DENIED.labels("adaptation", "/health").inc()
            except Exception:
                pass
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")
    return {
        "status": "ok",
        "request_id": getattr(request.state, "request_id", None),
        "hits": getattr(app.state, "_health_hits", 0),
        "max": HEALTH_MAX,
    }


@app.get("/health")
async def health_alias(request: Request):
    return await healthz(request)


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# ---- RL (Reinforcement Learning) placeholder endpoints (future Phase) ----
@app.post("/v1/rl/train")
async def rl_train(user: UserContext = Depends(require_roles("admin"))):
    raise HTTPException(
        status_code=501, detail="RL training pipeline not yet implemented"
    )


@app.get("/v1/rl/status")
async def rl_status(user: UserContext = Depends(require_roles("admin", "educator"))):
    return {"status": "not_implemented", "detail": "RL components pending future phase"}


@app.post("/v1/rl/offline-log")
async def rl_offline_log(user: UserContext = Depends(require_roles("admin"))):
    raise HTTPException(
        status_code=501, detail="Offline log ingestion not yet implemented"
    )


@app.get("/v1/rl/policy/export")
async def rl_policy_export(user: UserContext = Depends(require_roles("admin"))):
    raise HTTPException(status_code=501, detail="Policy export not yet implemented")


@app.get("/v1/rl/dataset/status")
async def rl_dataset_status(
    user: UserContext = Depends(require_roles("admin", "educator")),
):
    # Provide simple counts of feedback and recommendations as proxy future dataset size
    rec_count = await db.adaptation_recs.estimated_document_count()
    fb_count = await db.arm_feedback.estimated_document_count()
    return {"dataset": {"recommendations": rec_count, "feedback_events": fb_count}}


# Policy export/import (basic JSON) -- feature expansion
@app.get("/v1/adaptation/policy/export")
async def policy_export(
    user: UserContext = Depends(require_roles("admin", "educator")),
):
    pol = await get_bandit_policy()
    if not pol:
        raise HTTPException(status_code=404, detail="no_active_policy")
    # Remove internal _id for export cleanliness
    exp = {k: v for k, v in pol.items() if k != "_id"}
    return {"policy": exp}


@app.post("/v1/adaptation/policy/import")
async def policy_import(
    request: Request, user: UserContext = Depends(require_roles("admin"))
):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    doc = payload.get("policy") if isinstance(payload, dict) else None
    if not isinstance(doc, dict):
        raise HTTPException(status_code=422, detail="policy object required")
    # Mark any existing active false (simplistic approach)
    try:
        await db.policies.update_one(
            {"type": "bandit", "active": True},
            {"$set": {"active": False}},
            upsert=False,
        )
    except Exception:
        pass
    doc["type"] = "bandit"
    doc["active"] = True
    doc["created_at"] = datetime.utcnow()
    await db.policies.insert_one(doc)
    return {"status": "imported"}
