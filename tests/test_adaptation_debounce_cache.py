import json
import pytest
from fastapi.testclient import TestClient
from services.adaptation.adaptation.main import app as adaptation_app

client = TestClient(adaptation_app)


@pytest.mark.asyncio
async def test_recommendation_debounce(monkeypatch):
    # Monkeypatch redis client inside app to a fake dict-based cache
    class FakeRedis:
        def __init__(self):
            self.store = {}

        async def get(self, k):
            v = self.store.get(k)
            return json.dumps(v) if v else None

        async def setex(self, k, ttl, value):
            try:
                self.store[k] = json.loads(value)
            except Exception:
                self.store[k] = value

    fake = FakeRedis()
    adaptation_app.dependency_overrides = {}
    adaptation_app.state  # ensure state exists
    adaptation_module = __import__(
        "services.adaptation.adaptation.main", fromlist=["_redis"]
    )
    adaptation_module._redis = fake  # type: ignore

    payload = {"learner_id": "L1"}
    r1 = client.post("/v1/adaptation/recommend-next", json=payload)
    assert r1.status_code == 200
    r2 = client.post("/v1/adaptation/recommend-next", json=payload)
    assert r2.status_code == 200
    # second should be cached once fake redis is populated
    cached_flag = r2.json().get("cached")
    assert cached_flag is True
