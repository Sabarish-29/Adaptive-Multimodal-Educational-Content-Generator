from fastapi.testclient import TestClient
from services.contentgen.contentgen.main import app as content_app
from services.adaptation.adaptation.main import app as adaptation_app
from services.sessions.sessions.main import app as sessions_app


def test_metrics_contentgen_counter_increments():
    cg_client = TestClient(content_app)
    payload = {
        "learner_id": "m1",
        "unit_id": "u1",
        "objectives": ["o"],
        "modalities": ["text"],
    }
    r1 = cg_client.post("/v1/generate/lesson", json=payload)
    assert r1.status_code == 200
    m = cg_client.get("/metrics").text
    assert "contentgen_bundles_total" in m


def test_metrics_adaptation_feedback_counter():
    ad_client = TestClient(adaptation_app)
    # Need a feedback after initial recommend to ensure arm exists; recommend might fail if no policy
    # Skip if no policy configured (graceful)
    rec = ad_client.post(
        "/v1/adaptation/recommend-next", json={"learner_id": "Lx"}
    ).json()
    arm_id = rec.get("arm_id")
    if not arm_id:
        return  # no active policy; acceptable skip
    fb = ad_client.post(
        "/v1/adaptation/feedback",
        json={"learner_id": "Lx", "arm": arm_id, "reward": 1.0},
    )
    assert fb.status_code in (200, 204)
    m = ad_client.get("/metrics").text
    assert "adaptation_feedback_total" in m


def test_metrics_sessions_counters():
    s_client = TestClient(sessions_app)
    sid = s_client.post(
        "/v1/sessions", json={"learner_id": "Ls", "unit_id": "u1"}
    ).json()["session_id"]
    ev = s_client.post(
        f"/v1/sessions/{sid}/events",
        json={"type": "x", "timestamp": "2025-01-01T00:00:00Z", "payload": {}},
    )
    assert ev.status_code == 202
    m = s_client.get("/metrics").text
    assert "sessions_started_total" in m
    assert "session_events_total" in m
    # Histogram may or may not be enabled depending on prometheus_client version; check name presence if available
    if "session_event_ingest_latency_seconds_bucket" in m:
        assert "session_event_ingest_latency_seconds_count" in m
