import importlib
from fastapi.testclient import TestClient


def reload_sessions_fast():
    if "services.sessions.sessions.main" in importlib.sys.modules:
        del importlib.sys.modules["services.sessions.sessions.main"]
    mod = importlib.import_module("services.sessions.sessions.main")
    return mod.app


def test_sse_fast_mode_mock_payload(monkeypatch):
    monkeypatch.setenv("FAST_TEST_MODE", "true")
    app = reload_sessions_fast()
    client = TestClient(app)
    sid = client.post(
        "/v1/sessions", json={"learner_id": "l1", "unit_id": "u1"}
    ).json()["session_id"]
    observed = False
    with client.stream("GET", f"/v1/sessions/{sid}/live") as r:
        for line in r.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode()
            if line.startswith("data:") and "demo-" in line:
                assert 'strategy":"mock' in line.replace(" ", "")
                observed = True
                break
    assert observed, "Did not observe mock recommendation in fast mode"
