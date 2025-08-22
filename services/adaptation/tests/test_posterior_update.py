import pytest
from httpx import AsyncClient

try:
    from adaptation.main import app, db, SUCCESS_THRESHOLD  # provided by conftest alias
except Exception:
    from services.adaptation.adaptation.main import (
        app,
        db,
        SUCCESS_THRESHOLD,
    )  # fallback


@pytest.mark.asyncio
async def test_posterior_feedback_increments_alpha_or_beta():
    # Ensure a fresh posterior state: remove any existing entries for test arm
    await db.bandit_posteriors.delete_many({"arm_id": "text_only_small"})
    # Trigger recommendation to initialize posteriors via sampling
    async with AsyncClient(app=app, base_url="http://test") as ac:
        rec_resp = await ac.post(
            "/v1/adaptation/recommend-next",
            json={"ctx": {"learner_id": "learner_demo"}},
        )
        assert rec_resp.status_code == 200
        # Send feedback below threshold -> increments beta
        fb_reward = SUCCESS_THRESHOLD - 0.05
        resp = await ac.post(
            "/v1/adaptation/feedback",
            json={
                "fb": {
                    "learner_id": "learner_demo",
                    "arm": "text_only_small",
                    "reward": fb_reward,
                }
            },
        )
        assert resp.status_code in (200, 204)
        posterior = await db.bandit_posteriors.find_one({"arm_id": "text_only_small"})
        assert posterior is not None
        assert posterior["beta"] >= 2
        # Now success case
        resp2 = await ac.post(
            "/v1/adaptation/feedback",
            json={
                "fb": {
                    "learner_id": "learner_demo",
                    "arm": "text_only_small",
                    "reward": SUCCESS_THRESHOLD + 0.01,
                }
            },
        )
        assert resp2.status_code in (200, 204)
        posterior2 = await db.bandit_posteriors.find_one({"arm_id": "text_only_small"})
        assert posterior2["alpha"] >= 2
