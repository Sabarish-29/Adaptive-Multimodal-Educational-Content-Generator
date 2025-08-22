import pytest
from fastapi.testclient import TestClient
from services.adaptation.adaptation.main import app as adaptation_app, db as service_db


@pytest.mark.asyncio
async def test_feedback_metric_with_policy():
    # Use the adaptation service's own db handle so policy is visible to get_bandit_policy
    await service_db.policies.delete_many({"type": "bandit"})
    await service_db.bandit_posteriors.delete_many({})
    await service_db.policies.insert_one(
        {
            "type": "bandit",
            "active": True,
            "algorithm": "thompson_beta",
            "priors": {"alpha": 1, "beta": 1},
            "arms": [
                {
                    "id": "arm_a",
                    "modalities": ["text"],
                    "chunk_size": "short",
                    "difficulty": 0.5,
                }
            ],
        }
    )
    client_http = TestClient(adaptation_app)
    rec = client_http.post(
        "/v1/adaptation/recommend-next", json={"learner_id": "fixtureL"}
    ).json()
    assert rec.get("arm_id") == "arm_a"
    fb = client_http.post(
        "/v1/adaptation/feedback",
        json={"learner_id": "fixtureL", "arm": "arm_a", "reward": 1.0},
    )
    assert fb.status_code in (200, 204)
    metrics = client_http.get("/metrics").text
    assert "adaptation_feedback_total" in metrics
