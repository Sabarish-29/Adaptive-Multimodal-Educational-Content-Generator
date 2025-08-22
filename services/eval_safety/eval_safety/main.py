from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import os
import motor.motor_asyncio

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

app = FastAPI(title="Evaluation & Safety Service", version="0.1.0")


class ContentEvaluationRequest(BaseModel):
    bundle_id: str
    text: str


class AccessibilityEvaluationRequest(BaseModel):
    bundle_id: str
    text: str
    alt_text_present: bool
    captions_present: bool


@app.post("/v1/evaluate/content")
async def eval_content(req: ContentEvaluationRequest):
    checks = {
        "reading_level": {"score": 5, "target_met": True},
        "toxicity": {"score": 0.01, "below_threshold": True},
        "pii": {"detected": False},
        "pedagogy": {"clarity": 0.9, "alignment": 0.95},
    }
    passed = all(
        [
            checks["reading_level"]["target_met"],
            checks["toxicity"]["below_threshold"],
            not checks["pii"]["detected"],
        ]
    )
    doc = {
        "bundle_id": req.bundle_id,
        "checks": checks,
        "pass": passed,
        "issues": [] if passed else ["issue"],
        "created_at": datetime.utcnow(),
    }
    await db.evaluations.insert_one(doc)
    return {"pass": passed, "checks": checks}


@app.post("/v1/evaluate/accessibility")
async def eval_accessibility(req: AccessibilityEvaluationRequest):
    issues = []
    if not req.alt_text_present:
        issues.append("missing_alt_text")
    if not req.captions_present:
        issues.append("missing_captions")
    passed = len(issues) == 0
    doc = {
        "bundle_id": req.bundle_id,
        "type": "a11y",
        "pass": passed,
        "issues": issues,
        "created_at": datetime.utcnow(),
    }
    await db.evaluations.insert_one(doc)
    return {"pass": passed, "issues": issues}


@app.get("/healthz")
async def health():
    return {"status": "ok"}
