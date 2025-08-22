import pytest
from httpx import AsyncClient
from profiles.main import app, db


@pytest.mark.asyncio
async def test_get_demo_profile(monkeypatch):
    # Insert a demo profile
    await db.learners.insert_one(
        {
            "user_id": "test_user",
            "disabilities": [],
            "accommodations": {},
            "preferences": {"modalities": [], "reading_level": "grade4"},
        }
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/v1/learners/test_user/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "test_user"
