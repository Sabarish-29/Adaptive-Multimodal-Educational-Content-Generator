import pytest
from httpx import AsyncClient
from services.contentgen.contentgen.main import (
    app,
)  # adjusted import for package layout


@pytest.mark.asyncio
async def test_lesson_idempotent_hash():
    payload = {
        "learner_id": "learner_demo",
        "unit_id": "unit_math_1",
        "objectives": ["b", "a"],
        "modalities": ["text"],
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r1 = await ac.post("/v1/generate/lesson", json={"req": payload})
        assert r1.status_code == 200
        b1 = r1.json()["bundle_id"]
        # reversed objectives -> should yield same bundle id (cached true)
        payload2 = {**payload, "objectives": ["a", "b"]}
        r2 = await ac.post("/v1/generate/lesson", json={"req": payload2})
        assert r2.status_code == 200
        assert r2.json().get("cached") is True
        assert r2.json()["bundle_id"] == b1
