import os
import json
import hashlib
import motor.motor_asyncio
import pytest

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu_test")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[os.getenv("MONGODB_DB", "edu_test")]


def make_input_hash(payload: dict):
    norm = {**payload, "objectives": sorted(payload["objectives"])}
    return hashlib.sha256(json.dumps(norm, sort_keys=True).encode()).hexdigest()


@pytest.mark.asyncio
async def test_objective_order_idempotent():
    await db.content_bundles.delete_many({})
    p1 = {
        "learner_id": "l1",
        "unit_id": "u1",
        "objectives": ["b", "a"],
        "modalities": ["text"],
    }
    p2 = {
        "learner_id": "l1",
        "unit_id": "u1",
        "objectives": ["a", "b"],
        "modalities": ["text"],
    }
    h1 = make_input_hash(p1)
    h2 = make_input_hash(p2)
    assert h1 == h2
    await db.content_bundles.insert_one(
        {"hashes": {"input_hash": h1, "output_hash": "x"}}
    )
    existing = await db.content_bundles.find_one({"hashes.input_hash": h2})
    assert existing is not None
