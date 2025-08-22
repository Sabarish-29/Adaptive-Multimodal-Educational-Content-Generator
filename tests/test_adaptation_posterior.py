import os
import motor.motor_asyncio
import pytest
from datetime import datetime

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu_test")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[os.getenv("MONGODB_DB", "edu_test")]


@pytest.mark.asyncio
async def test_posterior_update():
    await db.bandit_posteriors.delete_many({})
    await db.arm_feedback.delete_many({})
    arm_id = "text_only_small"
    # Insert prior
    await db.bandit_posteriors.insert_one({"arm_id": arm_id, "alpha": 1, "beta": 1})
    # Simulate reward update path (increment alpha)
    await db.bandit_posteriors.update_one({"arm_id": arm_id}, {"$inc": {"alpha": 1}})
    doc = await db.bandit_posteriors.find_one({"arm_id": arm_id})
    assert doc["alpha"] == 2


@pytest.mark.asyncio
async def test_feedback_log():
    await db.arm_feedback.delete_many({})
    await db.arm_feedback.insert_one(
        {"learner_id": "l1", "arm": "a1", "reward": 1.0, "ts": datetime.utcnow()}
    )
    count = await db.arm_feedback.count_documents({"learner_id": "l1"})
    assert count == 1
