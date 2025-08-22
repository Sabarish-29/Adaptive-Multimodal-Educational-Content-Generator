from fastapi import FastAPI
import motor.motor_asyncio
import os
from datetime import datetime, timedelta

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

app = FastAPI(title="Analytics Service", version="0.3.0")

# Import routers AFTER db is defined to avoid circular import during module init
from .telemetry import router as telemetry_router  # noqa: E402
from .feedback import router as feedback_router    # noqa: E402
from .quality import router as quality_router      # noqa: E402

app.include_router(telemetry_router)
app.include_router(feedback_router)
app.include_router(quality_router)


@app.get("/v1/analytics/learner/{learner_id}/progress")
async def learner_progress(learner_id: str):
    # Simplified progress: count of content bundles and events last 7 days
    since = datetime.utcnow() - timedelta(days=7)
    bundle_count = await db.content_bundles.count_documents(
        {"learner_id": learner_id, "created_at": {"$gte": since}}
    )
    event_count = await db.events.count_documents(
        {"learner_id": learner_id, "timestamp": {"$gte": since}}
    )
    return {
        "learner_id": learner_id,
        "weekly_bundles": bundle_count,
        "weekly_events": event_count,
        "modality_effectiveness": {"text": 0.8, "audio": 0.7},  # placeholder
    }


@app.get("/healthz")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def _startup():
    # Ensure indexes for telemetry (ts descending queries & TTL optional)
    await db.telemetry_events.create_index([("ts", -1)])
    await db.telemetry_events.create_index([("type", 1), ("ts", -1)])
    await db.telemetry_events.create_index([("anonId", 1)])
    # TTL retention if env set
    import os
    days = os.getenv('TELEMETRY_RETENTION_DAYS')
    if days:
        ttl_seconds = int(days) * 86400
        # Create/replace TTL index
        try:
            await db.telemetry_events.drop_index('ts_ttl')
        except Exception:
            pass
        await db.telemetry_events.create_index('ts', expireAfterSeconds=ttl_seconds, name='ts_ttl')
    # Rollup & alerts indexes
    await db.telemetry_rollups.create_index([('hourStart', -1)])
    await db.telemetry_rollups.create_index([('type', 1), ('hourStart', -1)])
    await db.telemetry_alerts.create_index([('ts', -1)])
    await db.telemetry_alerts.create_index([('metric', 1), ('ts', -1)])
    # Feedback indexes
    await db.feedback.create_index([('itemId', 1), ('ts', -1)])
    await db.feedback.create_index([('itemType', 1), ('ts', -1)])
