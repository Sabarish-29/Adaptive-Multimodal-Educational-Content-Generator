import importlib
import os
from fastapi.testclient import TestClient


def reload_sessions_app(create_rate: int = 1, event_rate: int = 1):
    os.environ["SESSIONS_CREATE_RATE_PER_MIN"] = str(create_rate)
    os.environ["SESSIONS_EVENT_RATE_PER_MIN"] = str(event_rate)
    # Ensure fresh import so limiters pick up env vars
    if "services.sessions.sessions.main" in importlib.sys.modules:
        del importlib.sys.modules["services.sessions.sessions.main"]
    mod = importlib.import_module("services.sessions.sessions.main")
    return mod.app


def test_sessions_rate_limited_metrics():
    app = reload_sessions_app(create_rate=1, event_rate=1)
    client = TestClient(app)
    # First create allowed
    r1 = client.post("/v1/sessions", json={"learner_id": "L1", "unit_id": "U1"})
    assert r1.status_code == 201
    # Second should be rate limited
    r2 = client.post("/v1/sessions", json={"learner_id": "L1", "unit_id": "U1"})
    assert r2.status_code == 429
    sid = r1.json()["session_id"]
    # First event allowed
    e1 = client.post(
        f"/v1/sessions/{sid}/events",
        json={"type": "x", "timestamp": "2025-01-01T00:00:00Z", "payload": {}},
    )
    assert e1.status_code == 202
    # Second event should 429
    e2 = client.post(
        f"/v1/sessions/{sid}/events",
        json={"type": "x", "timestamp": "2025-01-01T00:00:00Z", "payload": {}},
    )
    assert e2.status_code == 429
    metrics = client.get("/metrics").text
    assert "sessions_rate_limited_total" in metrics
    # Optional label assertions
    assert 'route="create"' in metrics
    assert 'route="event"' in metrics
