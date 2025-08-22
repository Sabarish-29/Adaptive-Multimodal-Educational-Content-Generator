import pytest
from fastapi.testclient import TestClient
from services.contentgen.contentgen.main import app as content_app

client = TestClient(content_app)


@pytest.mark.asyncio
async def test_contentgen_cache(monkeypatch):
    # Fake redis to count setex usage
    class FakeRedis:
        def __init__(self):
            self.store = {}
            self.set_count = 0

        async def get(self, k):
            v = self.store.get(k)
            return v

        async def setex(self, k, ttl, value):
            self.store[k] = value
            self.set_count += 1

    fake = FakeRedis()
    module = __import__("services.contentgen.contentgen.main", fromlist=["_redis"])
    module._redis = fake  # type: ignore

    payload = {
        "learner_id": "l1",
        "unit_id": "u1",
        "objectives": ["o1", "o2"],
        "modalities": ["text"],
    }
    r1 = client.post("/v1/generate/lesson", json=payload)
    assert r1.status_code == 200
    assert r1.json()["cached"] is False
    r2 = client.post("/v1/generate/lesson", json=payload)
    assert r2.status_code == 200
    assert r2.json()["cached"] is True
    assert fake.set_count == 1
