from fastapi import FastAPI, Depends
from pydantic import BaseModel
import motor.motor_asyncio
import os
from datetime import datetime
from typing import Dict
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
        roles: list[str] = ["admin"]

    def require_roles(*roles):
        def inner(user: UserContext | None = None):
            return user or UserContext()

        return inner


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

app = FastAPI(title="Admin Service", version="0.1.1")

STATIC_MODELS = [
    {
        "name": "llm_stub",
        "type": "llm",
        "version": "0.0.1",
        "license": "Apache-2.0",
        "routing_tags": ["default"],
    },
    {
        "name": "captioner_stub",
        "type": "vlm",
        "version": "0.0.1",
        "license": "Apache-2.0",
        "routing_tags": ["caption"],
    },
]


class ModelSelectRequest(BaseModel):
    name: str
    version: str


class TenantSettings(BaseModel):
    feature_flags: Dict[str, bool] = {}


@app.get("/v1/models")
async def list_models(user: UserContext = Depends(require_roles("admin", "educator"))):
    return {"models": STATIC_MODELS}


@app.post("/v1/models/select")
async def select_model(
    sel: ModelSelectRequest, user: UserContext = Depends(require_roles("admin"))
):
    # store selection (simplified global)
    await db.model_selection.update_one(
        {"name": sel.name},
        {"$set": {"version": sel.version, "selected_at": datetime.utcnow()}},
        upsert=True,
    )
    return {"selected": sel.name, "version": sel.version}


@app.post("/v1/tenants/{tenant_id}/settings")
async def tenant_settings(
    tenant_id: str,
    settings: TenantSettings,
    user: UserContext = Depends(require_roles("admin")),
):
    await db.tenant_settings.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"settings": settings.dict(), "updated_at": datetime.utcnow()}},
        upsert=True,
    )
    return {"tenant_id": tenant_id, "updated": True}


@app.get("/healthz")
async def health():
    return {"status": "ok"}
