from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import motor.motor_asyncio
import os
from datetime import datetime

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

app = FastAPI(title="Curriculum Service", version="0.1.1")


class UnitCreate(BaseModel):
    unit_id: str
    title: str
    description: Optional[str]


class ObjectiveCreate(BaseModel):
    unit_id: str
    objective_id: str
    text: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


@app.post("/v1/units", status_code=201)
async def create_unit(u: UnitCreate):
    await db.units.update_one(
        {"unit_id": u.unit_id},
        {"$setOnInsert": {**u.dict(), "created_at": datetime.utcnow()}},
        upsert=True,
    )
    return {"unit_id": u.unit_id}


@app.get("/v1/units/{unit_id}")
async def get_unit(unit_id: str):
    doc = await db.units.find_one({"unit_id": unit_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="not found")
    return doc


@app.post("/v1/objectives", status_code=201)
async def create_objective(o: ObjectiveCreate):
    await db.objectives.update_one(
        {"unit_id": o.unit_id, "objective_id": o.objective_id},
        {"$setOnInsert": {**o.dict(), "created_at": datetime.utcnow()}},
        upsert=True,
    )
    return {"objective_id": o.objective_id}


@app.get("/v1/units/{unit_id}/objectives")
async def list_objectives(unit_id: str):
    cursor = db.objectives.find({"unit_id": unit_id}, {"_id": 0})
    return [doc async for doc in cursor]


@app.post("/v1/content/search")
async def search(req: SearchRequest):
    # naive search across objectives text
    q = req.query.lower()
    cursor = db.objectives.find()
    results = []
    async for doc in cursor:
        if q in doc.get("text", "").lower():
            results.append(
                {
                    "unit_id": doc["unit_id"],
                    "objective_id": doc["objective_id"],
                    "snippet": doc["text"][:120],
                }
            )
        if len(results) >= req.limit:
            break
    return {"results": results}


@app.get("/healthz")
async def health():
    return {"status": "ok"}
