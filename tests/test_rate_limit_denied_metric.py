import importlib
from fastapi.testclient import TestClient


def load_app():
    mod = importlib.import_module("adaptation.main")
    return mod.app


def test_rate_limit_denied_metric(monkeypatch):
    # Deterministic health limit: allow 2 ok, 3rd 429
    monkeypatch.setenv("ADAPTATION_HEALTH_MAX", "2")
    if "adaptation.main" in importlib.sys.modules:
        del importlib.sys.modules["adaptation.main"]
    app = load_app()
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
    denied = client.get("/health")
    assert denied.status_code == 429
    metrics = client.get("/metrics").text
    # Either new adaptation_health_rate_limited_total or legacy rate_limit_denied_total present
    assert ("adaptation_health_rate_limited_total" in metrics) or (
        "rate_limit_denied_total" in metrics
    )


def test_require_strong_encryption_enforced(monkeypatch):
    monkeypatch.setenv("FEATURE_FIELD_ENCRYPTION", "true")
    monkeypatch.setenv("REQUIRE_STRONG_ENCRYPTION", "true")
    if "common_utils.encryption" in importlib.sys.modules:
        del importlib.sys.modules["common_utils.encryption"]
    import pytest

    with pytest.raises(Exception):
        importlib.import_module("common_utils.encryption")
