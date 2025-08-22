from fastapi import FastAPI, HTTPException, Request, Response, Depends, Body
import sys, os, pathlib as _p
# Ensure repo root (containing 'packages' or 'sitecustomize.py') and packages path present.
_here = _p.Path(__file__).resolve()
_root = None
for cand in [_here.parents[i] for i in range(1, min(6, len(_here.parents)) )]:
    if (cand / 'packages').is_dir() or (cand / 'sitecustomize.py').is_file():
        _root = cand
        break
if _root is None:
    _root = _here.parents[2]  # fallback (may just be services/)
_pkg = _root / 'packages'
for p in {str(_root), str(_pkg)}:
    if p not in sys.path and _p.Path(p).exists():
        sys.path.insert(0, p)
from pydantic import BaseModel
from typing import Optional, Dict, Any
import motor.motor_asyncio
import os
from datetime import datetime

try:
    from sse_starlette.sse import EventSourceResponse  # type: ignore
except Exception:  # fallback minimal SSE
    from fastapi import Response

    async def EventSourceResponse(generator):  # type: ignore
        async def stream(gen):
            async for evt in gen:
                data = evt.get("data")
                if isinstance(data, dict):
                    import json as _json

                    data_str = _json.dumps(data)
                else:
                    data_str = str(data)
                yield f"event: {evt.get('event','message')}\n" f"data: {data_str}\n\n"

        from starlette.responses import StreamingResponse

        return StreamingResponse(stream(generator), media_type="text/event-stream")


import asyncio
import httpx
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
try:
    from adaptive_auth import require_roles, UserContext  # type: ignore
except Exception:
    from pydantic import BaseModel

    class UserContext(BaseModel):  # type: ignore
        sub: str = "anonymous"
        roles: list[str] = ["learner"]

    def require_roles(*roles):
        def inner(user: UserContext | None = None):
            return user or UserContext()

        return inner


from bson import ObjectId
import json
import time
import uuid
import hashlib

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")
MONGODB_TIMEOUT_MS = int(os.getenv("MONGODB_TIMEOUT_MS", "200"))
FORCE_REAL_MONGO = os.getenv("FORCE_REAL_MONGO", "false").lower() == "true"
# If false (default), initial startup will not block on a Mongo ping; first DB op will lazy-init.
SESSIONS_EAGER_DB = os.getenv("SESSIONS_EAGER_DB", "false").lower() == "true"


class _InsertResult:
    def __init__(self, _id):
        self.inserted_id = _id


class _UpdateResult:
    def __init__(self, matched, upserted=None):
        self.matched_count = matched
        self.upserted_id = upserted


class InMemoryCollection:
    def __init__(self):
        self._docs: list[dict] = []

    async def insert_one(self, doc: dict):
        if "_id" not in doc:
            doc["_id"] = str(uuid.uuid4())
        self._docs.append(doc.copy())
        return _InsertResult(doc["_id"])

    async def find_one(self, query: dict):
        for d in self._docs:
            ok = True
            for k, v in query.items():
                if d.get(k) != v:
                    ok = False
                    break
            if ok:
                return d.copy()
        return None

    async def update_one(
        self, query: dict, spec: dict, upsert: bool = False
    ):  # simple $set only
        target = await self.find_one(query)
        if target:
            if "$set" in spec:
                target.update(spec["$set"])
            # replace stored
            for i, d in enumerate(self._docs):
                if d.get("_id") == target.get("_id") or all(
                    d.get(k) == query.get(k) for k in query.keys()
                ):
                    self._docs[i] = target
                    break
            return _UpdateResult(1)
        if upsert:
            new_doc = query.copy()
            if "$set" in spec:
                new_doc.update(spec["$set"])
            if "_id" not in new_doc:
                new_doc["_id"] = str(uuid.uuid4())
            self._docs.append(new_doc)
            return _UpdateResult(0, new_doc["_id"])
        return _UpdateResult(0)


class InMemoryDB:
    def __init__(self):
        self.sessions = InMemoryCollection()
        self.events = InMemoryCollection()
        self.audit_logs = InMemoryCollection()


_use_memory = False
client = None
db = None  # will be set to real or in-memory DB


def _init_mongo_if_needed():
    """Initialize motor client lazily unless eager mode enabled.

    Returns current db handle (real or in-memory). If FORCE_REAL_MONGO is set and
    connection fails, exception propagates.
    """
    global client, db, _use_memory
    if db is not None:
        return db
    try:
        c = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URI, serverSelectionTimeoutMS=MONGODB_TIMEOUT_MS
        )
        if SESSIONS_EAGER_DB or FORCE_REAL_MONGO:
            c.admin.command("ping")  # type: ignore
        client = c
        db = client[MONGODB_DB]
    except Exception:
        if FORCE_REAL_MONGO:
            raise
        _use_memory = True
        db = InMemoryDB()
    return db


# Perform eager init only if configured
if SESSIONS_EAGER_DB:
    _init_mongo_if_needed()

from common_utils.request import request_id_middleware, REQUEST_ID_HEADER  # type: ignore
from common_utils.ratelimit import install_rate_limit  # type: ignore
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

try:  # optional histogram
    from prometheus_client import Histogram  # type: ignore
except Exception:  # pragma: no cover
    Histogram = None  # type: ignore

from common_utils.error import install_error_handlers  # type: ignore

print("[sessions] module import start")
app = FastAPI(title="Sessions Service", version="0.2.6")
print("[sessions] FastAPI app created")
from fastapi.middleware.cors import CORSMiddleware
# Dev CORS (frontend on 3000). For production prefer gateway and remove wide-open origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_id_middleware)
install_error_handlers(app)
setattr(app.state, "service_name", "sessions")
from common_utils.ratelimit import install_rate_limit as _install_rl_early  # type: ignore

# Early install (without redis) so middleware present for first request; startup will refresh redis in config
try:
    if not hasattr(app.state, "rate_limit_config"):
        # Primary limiter (legacy) for any POST endpoints if separate not configured
        _install_rl_early(
            app, per_minute=int(os.getenv("SESSIONS_RATE_PER_MIN", "120"))
        )
except Exception:
    pass

# Separate limiters (create vs events) using distinct configs stored on app.state
SESSIONS_CREATE_RATE = int(
    os.getenv("SESSIONS_CREATE_RATE_PER_MIN", os.getenv("SESSIONS_RATE_PER_MIN", "120"))
)
SESSIONS_EVENT_RATE = int(
    os.getenv("SESSIONS_EVENT_RATE_PER_MIN", os.getenv("SESSIONS_RATE_PER_MIN", "240"))
)

from common_utils.ratelimit import SlidingWindowLimiter  # type: ignore

if not hasattr(app.state, "sessions_limiters"):
    app.state.sessions_limiters = {
        "create": SlidingWindowLimiter(
            per_minute=SESSIONS_CREATE_RATE, redis_client=None
        ),
        "event": SlidingWindowLimiter(
            per_minute=SESSIONS_EVENT_RATE, redis_client=None
        ),
    }

SESSION_EVENTS = Counter("session_events_total", "Total session events ingested")
SESSIONS_STARTED = Counter("sessions_started_total", "Sessions started")
SESSIONS_CREATE_LATENCY = (
    Histogram(
        "sessions_create_latency_seconds", "Latency of session creation (seconds)"
    )
    if "Histogram" in globals() and Histogram
    else None
)
RECOMMENDATION_EVENTS = Counter(
    "sessions_recommendation_events_total", "Recommendation events emitted", ["source"]
)
ADAPTATION_CALL_LATENCY = (
    Histogram(
        "adaptation_call_latency_seconds",
        "Latency of adaptation recommend-next calls",
        ["status"],
    )
    if "Histogram" in globals() and Histogram
    else None
)
# New metrics: event ingest latency & rate limit sampling
SESSION_EVENT_INGEST_LATENCY = (
    Histogram(
        "session_event_ingest_latency_seconds",
        "Latency of session event ingestion (seconds)",
        ["status"],
    )
    if "Histogram" in globals() and Histogram
    else None
)
SESSIONS_RATE_LIMITED = Counter(
    "sessions_rate_limited_total", "Rate limited session requests", ["route"]
)
# Circuit breaker metrics
try:
    from prometheus_client import Gauge  # type: ignore
except Exception:  # pragma: no cover
    Gauge = None  # type: ignore
CB_STATE_GAUGE = (
    Gauge(
        "sessions_adaptation_circuit_state",
        "Circuit state for adaptation calls (0=closed,1=open,2=half_open)",
    )
    if "Gauge" in globals() and Gauge
    else None
)
CB_OPEN_TOTAL = Counter(
    "sessions_adaptation_circuit_open_total", "Times adaptation circuit opened"
)
SSE_HEARTBEATS = Counter(
    "sessions_sse_heartbeats_total", "SSE heartbeat events emitted"
)
SSE_DISCONNECTS = Counter("sessions_sse_disconnects_total", "SSE client disconnects")

try:
    import aioredis  # type: ignore
except Exception:
    aioredis = None  # type: ignore
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis = None

# OpenTelemetry (optional)
OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() == "true"
if OTEL_ENABLED:
    try:  # best-effort setup
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )  # type: ignore

        provider = TracerProvider(
            resource=Resource.create({"service.name": "sessions"})
        )
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("sessions")
    except Exception:  # pragma: no cover
        OTEL_ENABLED = False
        _tracer = None  # type: ignore
else:
    _tracer = None  # type: ignore


def _hash_id(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return None


@app.on_event("startup")
async def _init():
    print("[sessions] startup event firing")
    global _redis
    if aioredis:
        try:
            _redis = await aioredis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            setattr(app.state, "redis", _redis)
        except Exception:
            _redis = None
    # If limiter already installed early, just refresh config with redis-aware limiter
    try:
        install_rate_limit(
            app, per_minute=int(os.getenv("SESSIONS_RATE_PER_MIN", "120"))
        )
    except Exception:
        pass


@app.middleware("http")
async def json_logging(request: Request, call_next):
    start = time.time()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration = (time.time() - start) * 1000
        req_id = getattr(request.state, "request_id", None) or request.headers.get(
            REQUEST_ID_HEADER
        )
        log = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "svc": "sessions",
            "request_id": req_id,
            "method": request.method,
            "path": request.url.path,
            "status": getattr(response, "status_code", 500),
            "duration_ms": round(duration, 2),
        }
        print(json.dumps(log))


class SessionStartRequest(BaseModel):
    learner_id: str
    unit_id: str
    device_context: Optional[Dict[str, Any]] = None


class SessionEvent(BaseModel):  # retained for future; not used in endpoint now
    type: str
    timestamp: datetime | str
    payload: Dict[str, Any] = {}


@app.post("/v1/sessions", status_code=201)
async def start_session(
    request: Request,
    payload: dict | None = Body(default=None),
    user: UserContext = Depends(require_roles("learner", "educator", "admin")),
):
    global db, _use_memory
    _t0 = time.time()
    span = None
    if OTEL_ENABLED and _tracer:
        try:
            span = _tracer.start_span("session.start")
        except Exception:
            span = None
    # Apply create-specific rate limit first (independent of generic middleware)
    limiters = getattr(app.state, "sessions_limiters", None)
    if limiters:
        remaining = await limiters["create"].allow(
            f"create:{request.client.host if request.client else 'anon'}"
        )
        if remaining < 0:
            try:
                SESSIONS_RATE_LIMITED.labels("create").inc()
            except Exception:
                pass
            if span:  # annotate before raising
                try:
                    span.set_attribute("rate_limited", True)
                except Exception:
                    pass
            raise HTTPException(status_code=429, detail="rate_limit_exceeded")
    # Accept both {'req': {...}} and direct body
    if payload is None:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
    if "req" in payload and isinstance(payload.get("req"), dict):
        data = payload["req"]
    else:
        data = payload
    try:
        req = SessionStartRequest(**data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"invalid session start: {e}")
    # Ensure DB initialized (lazy)
    _init_mongo_if_needed()
    doc = {
        "learner_id": req.learner_id,
        "unit_id": req.unit_id,
        "status": "active",
        "started_at": datetime.utcnow(),
        "device_context": req.device_context or {},
        "created_by": getattr(user, "sub", None),
    }
    try:
        result = await db.sessions.insert_one(doc)
    except Exception:
        if FORCE_REAL_MONGO:
            raise
        # fallback if transient failure
        if not _use_memory:
            db = InMemoryDB()
            _use_memory = True
            result = await db.sessions.insert_one(doc)
        else:
            raise
    SESSIONS_STARTED.inc()
    if SESSIONS_CREATE_LATENCY is not None:
        try:
            SESSIONS_CREATE_LATENCY.observe(time.time() - _t0)
        except Exception:
            pass
    session_id = str(result.inserted_id)
    if span:
        try:
            span.set_attribute("session.id.hash", _hash_id(session_id))
            span.set_attribute("learner.id.hash", _hash_id(req.learner_id))
            span.set_attribute("unit.id", req.unit_id)
        except Exception:
            pass
        try:
            span.end()
        except Exception:
            pass
    return {"session_id": session_id}


@app.post("/v1/sessions/{session_id}/events", status_code=202)
async def post_event(
    session_id: str,
    request: Request,
    user: UserContext = Depends(require_roles("learner", "educator", "admin")),
):
    global db, _use_memory
    _t0 = time.time()
    _status_label = "accepted"  # will overwrite on early errors
    span = None
    if OTEL_ENABLED and _tracer:
        try:
            span = _tracer.start_span("session.event.ingest")
            span.set_attribute("session.id.hash", _hash_id(session_id))
        except Exception:
            span = None
    # Apply event-specific limiter
    limiters = getattr(app.state, "sessions_limiters", None)
    if limiters:
        remaining = await limiters["event"].allow(
            f"event:{request.client.host if request.client else 'anon'}:{session_id}"
        )
        if remaining < 0:
            try:
                SESSIONS_RATE_LIMITED.labels("event").inc()
            except Exception:
                pass
            if SESSION_EVENT_INGEST_LATENCY is not None:
                try:
                    SESSION_EVENT_INGEST_LATENCY.labels("rate_limited").observe(
                        time.time() - _t0
                    )
                except Exception:
                    pass
            raise HTTPException(status_code=429, detail="rate_limit_exceeded")
    # Accept both {'ev': {...}} and direct body
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if (
        isinstance(payload, dict)
        and "ev" in payload
        and isinstance(payload.get("ev"), dict)
    ):
        data = payload["ev"]
    else:
        data = payload if isinstance(payload, dict) else {}
    # Minimal validation
    if (
        not isinstance(data, dict)
        or "type" not in data
        or "timestamp" not in data
        or "payload" not in data
    ):
        _status_label = "invalid"
        if SESSION_EVENT_INGEST_LATENCY is not None:
            try:
                SESSION_EVENT_INGEST_LATENCY.labels(_status_label).observe(
                    time.time() - _t0
                )
            except Exception:
                pass
        if span:
            try:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "validation")
            except Exception:
                pass
            try:
                span.end()
            except Exception:
                pass
        raise HTTPException(
            status_code=422, detail="event must include type, timestamp, payload"
        )
    # Accept either ObjectId-compatible or plain string ids (in-memory stub uses hex uuid)
    _init_mongo_if_needed()
    session = None
    try:
        oid = ObjectId(session_id)
        session = await db.sessions.find_one({"_id": oid})
    except Exception:
        # fallback: attempt direct match
        session = await db.sessions.find_one({"_id": session_id})
    if not session:
        # Also try legacy field 'id' if present
        session = await db.sessions.find_one({"id": session_id})
    if not session:
        _status_label = "notfound"
        if SESSION_EVENT_INGEST_LATENCY is not None:
            try:
                SESSION_EVENT_INGEST_LATENCY.labels(_status_label).observe(
                    time.time() - _t0
                )
            except Exception:
                pass
        if span:
            try:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "session_not_found")
            except Exception:
                pass
            try:
                span.end()
            except Exception:
                pass
        raise HTTPException(status_code=404, detail="session not found")
    doc = {
        "type": data["type"],
        "timestamp": data["timestamp"],
        "payload": data.get("payload", {}),
        "session_id": session_id,
        "learner_id": session.get("learner_id"),
    }
    try:
        await db.events.insert_one(doc)
    except Exception:
        if FORCE_REAL_MONGO:
            raise
        if not _use_memory:
            db = InMemoryDB()
            _use_memory = True
            await db.events.insert_one(doc)
        else:
            raise
    SESSION_EVENTS.inc()
    try:
        await db.audit_logs.insert_one(
            {
                "event": "session.event",
                "user_id": session.get("learner_id"),
                "details": {"session_id": session_id, "type": data.get("type")},
                "created_at": datetime.utcnow(),
            }
        )
    except Exception:
        pass
    if SESSION_EVENT_INGEST_LATENCY is not None:
        try:
            SESSION_EVENT_INGEST_LATENCY.labels(_status_label).observe(
                time.time() - _t0
            )
        except Exception:
            pass
    if span:
        try:
            span.set_attribute("event.type", data.get("type"))
            span.set_attribute("learner.id.hash", _hash_id(session.get("learner_id")))
            span.end()
        except Exception:
            pass
    return {"status": "accepted"}


ADAPTATION_URL = os.getenv("ADAPTATION_URL", "http://api-adaptation:8001")
FAST_TEST_MODE = (
    os.getenv("FAST_TEST_MODE", "").lower() == "true"
    or "PYTEST_CURRENT_TEST" in os.environ
)
print(f"[sessions] FAST_TEST_MODE={FAST_TEST_MODE}")
RECOMMEND_HTTP_TIMEOUT = float(
    os.getenv("RECOMMEND_HTTP_TIMEOUT", "1.5" if FAST_TEST_MODE else "5.0")
)
# Circuit breaker / retry env config
CB_FAILURE_THRESHOLD = int(os.getenv("SESSIONS_ADAPTATION_CB_FAILURE_THRESHOLD", "3"))
CB_RESET_SECONDS = float(os.getenv("SESSIONS_ADAPTATION_CB_RESET_SECONDS", "30"))
CB_BACKOFF_BASE = float(os.getenv("SESSIONS_ADAPTATION_RETRY_BACKOFF_BASE", "0.5"))
CB_BACKOFF_MAX = float(os.getenv("SESSIONS_ADAPTATION_RETRY_BACKOFF_MAX", "5.0"))

# Circuit breaker state (module level)
_cb_failure_count = 0
_cb_open_until: float | None = None
_cb_half_open = False


async def recommendation_stream(session_id: str, request_id: str | None = None):
    # Query session to pull learner_id; accept raw or ObjectId-compatible
    from bson import ObjectId

    session = None
    try:
        oid = ObjectId(session_id)
        session = await db.sessions.find_one({"_id": oid})
    except Exception:
        session = await db.sessions.find_one({"_id": session_id})
    if not session:
        return
    learner_id = session.get("learner_id")
    counter = 0
    interval = float(os.getenv("RECOMMEND_STREAM_INTERVAL", "0.2"))
    heartbeat_interval = float(os.getenv("SESSIONS_SSE_HEARTBEAT_SECONDS", "15"))
    max_events_per_sec = int(
        os.getenv("SESSIONS_SSE_MAX_EVENTS_PER_SEC", "0")
    )  # 0=unlimited
    recent_event_ts: list[float] = []  # sliding window timestamps (seconds)
    last_emit = time.time()

    async def _post_yield_sleep():
        """Sleep for 'interval' seconds emitting heartbeat events if no recommendations sent."""
        nonlocal last_emit
        target = time.time() + interval
        # subdivide sleep so we can emit heartbeats
        while True:
            now = time.time()
            if now >= target:
                break
            if heartbeat_interval > 0 and (now - last_emit) >= heartbeat_interval:
                try:
                    SSE_HEARTBEATS.inc()
                except Exception:
                    pass
                hb = {
                    "event": "heartbeat",
                    "id": "hb-%d" % counter,
                    "data": {"ts": datetime.utcnow().isoformat() + "Z"},
                }
                yield hb
                last_emit = time.time()
            await asyncio.sleep(
                min(
                    heartbeat_interval / 2 if heartbeat_interval > 0 else 0.25,
                    target - now,
                    0.5,
                )
            )

    # Fast-path for tests: synthesize recommendations without external call
    try:
        if FAST_TEST_MODE:
            while True:
                now = time.time()
                # backpressure throttle
                if max_events_per_sec > 0:
                    recent_event_ts[:] = [t for t in recent_event_ts if now - t < 1.0]
                    if len(recent_event_ts) >= max_events_per_sec:
                        await asyncio.sleep(0.01)
                        continue
                data = {"content_id": f"demo-{counter}", "strategy": "mock"}
                print(f"[sessions][sse][synthetic] emit recommendation #{counter} session={session_id}")
                try:
                    RECOMMENDATION_EVENTS.labels("synthetic").inc()
                except Exception:
                    pass
                yield {"event": "recommendation", "id": str(counter), "data": data}
                last_emit = time.time()
                recent_event_ts.append(last_emit)
                counter += 1
                # sleep with heartbeats
                async for hb_evt in _post_yield_sleep():
                    yield hb_evt
        else:
            global _cb_failure_count, _cb_open_until, _cb_half_open
            if CB_STATE_GAUGE:
                try:
                    CB_STATE_GAUGE.set(0)
                except Exception:
                    pass
            async with httpx.AsyncClient(timeout=RECOMMEND_HTTP_TIMEOUT) as client_http:
                while True:
                    span = None
                    if OTEL_ENABLED and _tracer:
                        try:
                            span = _tracer.start_span("session.recommend.loop")
                            span.set_attribute("session.id.hash", _hash_id(session_id))
                            span.set_attribute("learner.id.hash", _hash_id(learner_id))
                        except Exception:
                            span = None
                    now_loop = time.time()
                    circuit_open = False
                    # Evaluate circuit state
                    if _cb_open_until is not None:
                        if now_loop < _cb_open_until:
                            circuit_open = True
                        else:
                            # Move to half-open trial state
                            _cb_open_until = None
                            _cb_half_open = True
                            if CB_STATE_GAUGE:
                                try:
                                    CB_STATE_GAUGE.set(2)
                                except Exception:
                                    pass
                    if circuit_open:
                        # Emit fallback without calling adaptation
                        fallback = {"error": "adaptation_circuit_open"}
                        try:
                            RECOMMENDATION_EVENTS.labels("http").inc()
                        except Exception:
                            pass
                        yield {
                            "event": "recommendation",
                            "id": str(counter),
                            "data": fallback,
                        }
                        print(f"[sessions][sse][circuit_open] emit fallback #{counter} session={session_id}")
                        last_emit = time.time()
                        counter += 1
                        # During open state sleep with heartbeats only
                        async for hb_evt in _post_yield_sleep():
                            yield hb_evt
                        continue
                    # Attempt call (normal or half-open trial)
                    try:
                        _t0 = time.time()
                        headers = {"X-Request-ID": request_id} if request_id else {}
                        r = await client_http.post(
                            f"{ADAPTATION_URL}/v1/adaptation/recommend-next",
                            json={"learner_id": learner_id},
                            headers=headers,
                        )
                        ok = r.status_code == 200
                        data = r.json() if ok else {"error": "adaptation_unavailable"}
                        status_label = "ok" if ok else "unavailable"
                    except Exception:
                        ok = False
                        data = {"error": "adaptation_exception"}
                        status_label = "error"
                    # Update circuit breaker state
                    if ok:
                        _cb_failure_count = 0
                        if _cb_half_open:
                            _cb_half_open = False
                            if CB_STATE_GAUGE:
                                try:
                                    CB_STATE_GAUGE.set(0)
                                except Exception:
                                    pass
                    else:
                        _cb_failure_count += 1
                        if _cb_half_open:
                            # Trial failed -> reopen
                            _cb_half_open = False
                        if (
                            _cb_failure_count >= CB_FAILURE_THRESHOLD
                            and _cb_open_until is None
                        ):
                            _cb_open_until = time.time() + CB_RESET_SECONDS
                            if CB_STATE_GAUGE:
                                try:
                                    CB_STATE_GAUGE.set(1)
                                except Exception:
                                    pass
                            try:
                                CB_OPEN_TOTAL.inc()
                            except Exception:
                                pass
                    # metrics
                    try:
                        RECOMMENDATION_EVENTS.labels("http").inc()
                    except Exception:
                        pass
                    if ADAPTATION_CALL_LATENCY is not None:
                        try:
                            ADAPTATION_CALL_LATENCY.labels(status_label).observe(
                                time.time() - _t0
                            )
                        except Exception:
                            pass
                    yield {"event": "recommendation", "id": str(counter), "data": data}
                    print(f"[sessions][sse][http] emit recommendation #{counter} ok={ok} status={status_label} session={session_id}")
                    last_emit = time.time()
                    counter += 1
                    # Adaptive retry backoff on failure when circuit still closed (pre-open)
                    if not ok and _cb_open_until is None:
                        backoff = min(
                            CB_BACKOFF_BASE * (2 ** max(_cb_failure_count - 1, 0)),
                            CB_BACKOFF_MAX,
                        )
                        # integrate into interval sleep
                        backoff_end = time.time() + backoff
                        while time.time() < backoff_end:
                            # Can still emit heartbeat if due
                            if (
                                heartbeat_interval > 0
                                and (time.time() - last_emit) >= heartbeat_interval
                            ):
                                try:
                                    SSE_HEARTBEATS.inc()
                                except Exception:
                                    pass
                                hb = {
                                    "event": "heartbeat",
                                    "id": "hb-%d" % counter,
                                    "data": {"ts": datetime.utcnow().isoformat() + "Z"},
                                }
                                yield hb
                                last_emit = time.time()
                            await asyncio.sleep(0.1)
                    if span:
                        try:
                            span.set_attribute("adaptation.status", status_label)
                            if not ok:
                                span.set_attribute("error", True)
                            span.end()
                        except Exception:
                            pass
                    async for hb_evt in _post_yield_sleep():
                        yield hb_evt
    except asyncio.CancelledError:
        try:
            SSE_DISCONNECTS.inc()
        except Exception:
            pass
        raise


@app.get("/v1/sessions/{session_id}/live")
async def live(
    session_id: str,
    request: Request,
    user: UserContext = Depends(require_roles("learner", "educator", "admin")),
):
    rid = getattr(request.state, "request_id", None)
    return EventSourceResponse(recommendation_stream(session_id, rid))


@app.get("/healthz")
async def health(request: Request):
    print("[sessions] /healthz hit")
    return {"status": "ok", "request_id": getattr(request.state, "request_id", None)}


# Backwards compatibility for tests expecting /health
@app.get("/health")
async def health_alias(request: Request):
    return await health(request)


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/debug/info")
async def debug_info():
    """Expose key runtime flags to help diagnose environment issues."""
    return {
        "fast_test_mode": FAST_TEST_MODE,
        "adaptation_url": ADAPTATION_URL,
        "use_memory_db": _use_memory,
        "pid": os.getpid(),
    }


@app.get("/v1/sessions/audit/logs")
async def audit_logs(
    limit: int = 50, user: UserContext = Depends(require_roles("educator", "admin"))
):
    """Return recent audit log entries (in-memory stub if no real DB)."""
    try:
        # naive: iterate last N from in-memory or query by created_at desc (not indexed in stub)
        if isinstance(db, InMemoryDB):  # type: ignore
            logs = list(db.audit_logs._docs)[-limit:]
        else:  # pragma: no cover - requires real mongo
            cursor = db.audit_logs.find({}).sort("created_at", -1).limit(limit)  # type: ignore
            logs = [doc async for doc in cursor]
    except Exception:
        logs = []
    return {"logs": logs, "count": len(logs)}
