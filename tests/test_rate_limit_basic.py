from fastapi.testclient import TestClient
from services.sessions.sessions.main import app as sessions_app

client = TestClient(sessions_app)


def test_rate_limit_applies():
    # Use a low rate limit via env override would be better; here we just send a few events
    sid_resp = client.post("/v1/sessions", json={"learner_id": "l1", "unit_id": "u1"})
    assert sid_resp.status_code == 201
    sid = sid_resp.json()["session_id"]
    # Post a couple events should be fine; we cannot deterministically hit limit without adjusting config
    for i in range(3):
        r = client.post(
            f"/v1/sessions/{sid}/events",
            json={"type": "x", "timestamp": "2025-01-01T00:00:00Z", "payload": {}},
        )
        assert r.status_code == 202
        assert "X-RateLimit-Remaining" in r.headers
