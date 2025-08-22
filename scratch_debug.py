import asyncio
from httpx import AsyncClient
from services.contentgen.contentgen.main import app


async def run():
    payload = {
        "learner_id": "learner_demo",
        "unit_id": "unit_math_1",
        "objectives": ["b", "a"],
        "modalities": ["text"],
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/v1/generate/lesson", json=payload)
        print("STATUS", r.status_code)
        print("BODY", r.text)


asyncio.run(run())
