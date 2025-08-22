import pytest
from fastapi.testclient import TestClient

from services.contentgen.contentgen.main import app as content_app


@pytest.fixture
def client():
    return TestClient(content_app)


def test_request_id_roundtrip(client):
    r = client.post(
        "/v1/generate/lesson",
        json={"learner_id": "l", "unit_id": "u", "objectives": ["o"]},
        headers={"X-Request-ID": "abc123"},
    )
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID") == "abc123"
