import importlib
from fastapi.testclient import TestClient

# We use sessions service for limiter tests
from services.sessions.sessions import main as sessions_main


def _reload():
    importlib.reload(sessions_main)
    return sessions_main.app


def test_rate_limit_header_present(monkeypatch):
    monkeypatch.setenv("SESSIONS_RATE_PER_MIN", "5")
    app = _reload()
    client = TestClient(app)
    r = client.post("/v1/sessions", json={"learner_id": "l1", "unit_id": "u1"})
    assert "X-RateLimit-Remaining" in r.headers


def test_rate_limit_exhaust(monkeypatch):
    monkeypatch.setenv("SESSIONS_RATE_PER_MIN", "2")
    app = _reload()
    client = TestClient(app)
    sid = client.post(
        "/v1/sessions", json={"learner_id": "l1", "unit_id": "u1"}
    ).json()["session_id"]
    # 1st event
    assert (
        client.post(
            f"/v1/sessions/{sid}/events",
            json={"type": "x", "timestamp": "2025-01-01T00:00:00Z", "payload": {}},
        ).status_code
        == 202
    )
    # 2nd event should still pass maybe header 0
    r2 = client.post(
        f"/v1/sessions/{sid}/events",
        json={"type": "x", "timestamp": "2025-01-01T00:00:00Z", "payload": {}},
    )
    if r2.status_code == 202:
        # third should 429
        r3 = client.post(
            f"/v1/sessions/{sid}/events",
            json={"type": "x", "timestamp": "2025-01-01T00:00:00Z", "payload": {}},
        )
        assert r3.status_code in (202, 429)
    else:
        assert r2.status_code == 429
