import importlib
from httpx import AsyncClient
from fastapi import FastAPI

# Simple smoke test: FEATURE_FIELD_ENCRYPTION toggles transformed text


def get_app():
    from contentgen.main import app

    return app


async def generate(client):
    r = await client.post(
        "/v1/generate/lesson",
        json={"learner_id": "t", "unit_id": "u", "objectives": ["o1"]},
    )
    assert r.status_code == 200
    return r.json()["content_bundle"]["content"]["text"]


async def test_encryption_toggle(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "false")
    import contentgen.main as m

    importlib.reload(m)
    app: FastAPI = m.app
    async with AsyncClient(app=app, base_url="http://test") as client:
        plain = await generate(client)
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    importlib.reload(m)
    app = m.app
    async with AsyncClient(app=app, base_url="http://test") as client:
        enc = await generate(client)
    assert plain != enc, "Encrypted text should differ when feature enabled"
