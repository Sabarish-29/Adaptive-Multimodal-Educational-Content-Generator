import importlib
from fastapi.testclient import TestClient


def reload_sessions():
    if "services.sessions.sessions.main" in importlib.sys.modules:
        del importlib.sys.modules["services.sessions.sessions.main"]
    mod = importlib.import_module("services.sessions.sessions.main")
    return mod.app, mod


def test_sessions_in_memory_fallback(monkeypatch):
    # Force unreachable mongo by pointing to bogus port and very short timeout
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:59999/test")
    monkeypatch.setenv("MONGODB_TIMEOUT_MS", "50")
    monkeypatch.delenv("FORCE_REAL_MONGO", raising=False)
    app, mod = reload_sessions()
    client = TestClient(app)
    r = client.post("/v1/sessions", json={"learner_id": "lX", "unit_id": "uY"})
    assert r.status_code == 201
    # Ensure the module flagged memory mode
    assert getattr(mod, "_use_memory", False) is True


def test_sessions_force_real_mongo(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:59999/test")
    monkeypatch.setenv("MONGODB_TIMEOUT_MS", "50")
    monkeypatch.setenv("FORCE_REAL_MONGO", "true")
    # Import should raise because mongo unreachable and fallback disabled
    if "services.sessions.sessions.main" in importlib.sys.modules:
        del importlib.sys.modules["services.sessions.sessions.main"]
    import pytest

    with pytest.raises(Exception):
        importlib.import_module("services.sessions.sessions.main")
