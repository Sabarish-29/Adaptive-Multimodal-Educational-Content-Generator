from fastapi.testclient import TestClient
from services.adaptation.adaptation import main as adaptation_main

app = adaptation_main.app
client = TestClient(app)

# Assumes a policy exists or else recommend-next returns no-arms; for test we can insert one via db directly.


def ensure_policy():
    db = adaptation_main.db
    pol = db.policies.find_one({"type": "bandit", "active": True})
    if not pol:
        db.policies.insert_one(
            {
                "type": "bandit",
                "active": True,
                "algorithm": "thompson",
                "priors": {"alpha": 1, "beta": 1},
                "arms": [
                    {
                        "id": "armA",
                        "modalities": ["text"],
                        "chunk_size": 1,
                        "difficulty": "easy",
                    },
                    {
                        "id": "armB",
                        "modalities": ["text"],
                        "chunk_size": 1,
                        "difficulty": "easy",
                    },
                ],
            }
        )


def test_strategy_and_cache():
    ensure_policy()
    r1 = client.post("/v1/adaptation/recommend-next", json={"learner_id": "L1"})
    assert r1.status_code == 200
    data1 = r1.json()
    assert "strategy" in data1
    # second call should be cached
    r2 = client.post("/v1/adaptation/recommend-next", json={"learner_id": "L1"})
    data2 = r2.json()
    assert data2.get("cached") is True
    assert data2["arm_id"] == data1["arm_id"]
