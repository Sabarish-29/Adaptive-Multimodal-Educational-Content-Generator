from fastapi.testclient import TestClient
from services.sessions.sessions.main import app as sessions_app

# Basic SSE stream smoke test: ensure recommendation events appear.


def test_sse_recommendations_stream():
    client = TestClient(sessions_app)
    sid_resp = client.post(
        "/v1/sessions", json={"learner_id": "learner_demo", "unit_id": "unit_math_1"}
    )
    assert sid_resp.status_code == 201
    sid = sid_resp.json()["session_id"]
    with client.stream("GET", f"/v1/sessions/{sid}/live") as r:
        got_event = False
        line_count = 0
        for line in r.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode()
            if line.startswith("event: recommendation"):
                got_event = True
            line_count += 1
            if got_event and line_count > 5:
                break
    assert got_event
