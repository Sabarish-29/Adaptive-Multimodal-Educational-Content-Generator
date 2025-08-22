import pytest
from httpx import AsyncClient
from eval_safety.main import app


@pytest.mark.asyncio
async def test_content_eval_pass():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/v1/evaluate/content",
            json={"bundle_id": "b1", "text": "Safe educational text."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pass"] is True
