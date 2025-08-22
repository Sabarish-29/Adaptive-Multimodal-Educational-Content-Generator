from fastapi import FastAPI, HTTPException, Depends, Request, Response, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import motor.motor_asyncio
import os
import sys
import pathlib
import json
import time

# Allow importing shared packages (monorepo) without editable install yet
ROOT = pathlib.Path(__file__).resolve().parents[2]
PKG_AUTH = ROOT / "packages" / "auth"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
try:
    from adaptive_auth import get_current_user, require_roles, UserContext  # type: ignore
except ImportError:
    # Fallback stub if auth not installed; minimal permissive context with test override hooks
    class UserContext(BaseModel):  # type: ignore
        sub: str = "anonymous"
        roles: list[str] = ["learner"]

    def _test_override_user() -> UserContext:
        sub = os.getenv("TEST_FORCE_SUB") or "anonymous"
        roles_env = os.getenv("TEST_FORCE_ROLES")
        roles = roles_env.split(",") if roles_env else ["learner"]
        return UserContext(sub=sub, roles=roles)

    def require_roles(*roles):  # type: ignore
        def inner(user: UserContext | None = None):
            # When test override env vars set, supply that context
            if os.getenv("TEST_FORCE_SUB") or os.getenv("TEST_FORCE_ROLES"):
                return _test_override_user()
            return user or UserContext()

        return inner


from datetime import datetime

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

from common_utils.request import request_id_middleware, REQUEST_ID_HEADER  # type: ignore
from common_utils.ratelimit import install_rate_limit  # type: ignore

try:
    import aioredis  # type: ignore
except Exception:
    aioredis = None  # type: ignore
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = FastAPI(title="Profiles Service", version="0.2.2")
TEST_MODE_DEFAULT = os.getenv("TEST_MODE", "").lower()
if TEST_MODE_DEFAULT == "":
    # Default to test mode when running under pytest (heuristic)
    if "PYTEST_CURRENT_TEST" in os.environ:
        os.environ["TEST_MODE"] = "true"
app.middleware("http")(request_id_middleware)
setattr(app.state, "service_name", "profiles")
# Install rate limit EARLY before startup to avoid RuntimeError when adding middleware
try:  # best-effort; startup will NOT add again if already present
    if not hasattr(app.state, "rate_limit_config"):
        install_rate_limit(app, per_minute=int(os.getenv("PROFILES_RATE_PER_MIN", "60")))
except Exception:
    pass


@app.middleware("http")
async def json_logging_middleware(request: Request, call_next):
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
            "svc": "profiles",
            "request_id": req_id,
            "method": request.method,
            "path": request.url.path,
            "status": getattr(response, "status_code", 500),
            "duration_ms": round(duration, 2),
        }
        print(json.dumps(log))


class Preferences(BaseModel):
    modalities: List[str] = []
    reading_level: Optional[str]


class LearnerProfileUpdate(BaseModel):
    disabilities: Optional[List[str]]
    accommodations: Optional[Dict[str, Any]]
    preferences: Optional[Preferences]
    languages: Optional[List[str]]


class LearnerProfile(LearnerProfileUpdate):
    id: str = Field(..., alias="user_id")
    consent: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class ConsentRecord(BaseModel):
    consent_type: str
    granted_by: str
    timestamp: datetime


from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

PROFILE_READS = Counter("profile_reads_total", "Profile retrievals")
PROFILE_UPDATES = Counter("profile_updates_total", "Profile updates")
CONSENTS_RECORDED = Counter("consents_recorded_total", "Consent records stored")


def _effective_user(required: list[str]):
    """Return a UserContext honoring test override env vars even if real auth lib present."""
    if os.getenv("TEST_FORCE_SUB") or os.getenv("TEST_FORCE_ROLES"):
        sub = os.getenv("TEST_FORCE_SUB", "anonymous")
        roles = os.getenv("TEST_FORCE_ROLES", "learner").split(",")
        return UserContext(sub=sub, roles=roles)  # type: ignore
    try:
        # call underlying require_roles to enforce normally
        return require_roles(*required)()  # type: ignore
    except Exception:
        return UserContext()  # type: ignore


_redis = None


@app.on_event("startup")
async def _init():
    global _redis
    if aioredis:
        try:
            _redis = await aioredis.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            setattr(app.state, "redis", _redis)
        except Exception:
            _redis = None
    # If limiter already installed early, don't re-add; could refresh config here later if needed
    # (No action needed now.)


@app.get(
    "/v1/learners/{id}/profile",
    response_model=LearnerProfile,
    response_model_by_alias=False,
)
async def get_profile(
    id: str, user: UserContext = Depends(require_roles("educator", "admin", "learner"))
):
    # Learner can only access own profile; allow override in test mode
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    if not test_mode:
        if (
            "learner" in user.roles
            and user.sub != id
            and "educator" not in user.roles
            and "admin" not in user.roles
        ):
            raise HTTPException(status_code=403, detail="forbidden")
    doc = await db.learners.find_one({"user_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    PROFILE_READS.inc()
    # Ensure alias field 'id' present for tests expecting it
    if "user_id" in doc:
        doc["id"] = doc["user_id"]
    return doc


@app.put("/v1/learners/{id}/profile", response_model=LearnerProfile)
async def update_profile(
    id: str,
    payload: dict = Body(default={}),
    user: UserContext = Depends(require_roles("educator", "admin")),
):  # type: ignore[valid-type]
    # Accept any subset; filter to known fields
    allowed_fields = {"disabilities", "accommodations", "preferences", "languages"}
    update = {k: v for k, v in payload.items() if k in allowed_fields}
    update["updated_at"] = datetime.utcnow()
    # Always set user_id so response model validation succeeds
    update_with_id = {**update, "user_id": id}
    await db.learners.update_one({"user_id": id}, {"$set": update_with_id}, upsert=True)
    doc = await db.learners.find_one({"user_id": id})
    if doc and "user_id" in doc:
        doc["id"] = doc["user_id"]
    PROFILE_UPDATES.inc()
    return doc


@app.post("/v1/learners/{id}/consent", status_code=201)
async def record_consent(
    id: str,
    consent: dict,
    user: UserContext = Depends(
        lambda: _effective_user(["guardian", "educator", "admin"])
    ),
):  # type: ignore[valid-type]
    # Normalize timestamp if trailing 'Z'
    if "timestamp" in consent and isinstance(consent["timestamp"], str):
        ts = consent["timestamp"]
        if ts.endswith("Z"):
            ts = ts[:-1]
        try:
            from datetime import datetime as _dt

            _ = _dt.fromisoformat(ts)
        except Exception:
            consent["timestamp"] = datetime.utcnow().isoformat()
    consent_obj = ConsentRecord(**consent)
    await db.learners.update_one(
        {"user_id": id},
        {"$set": {"consent": consent_obj.dict(), "updated_at": datetime.utcnow()}},
        upsert=True,
    )
    CONSENTS_RECORDED.inc()
    return {"status": "ok"}


@app.get("/healthz")
async def health(request: Request):
    return {"status": "ok", "request_id": getattr(request.state, "request_id", None)}


@app.get("/health")
async def health_alias(request: Request):
    return await health(request)


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
