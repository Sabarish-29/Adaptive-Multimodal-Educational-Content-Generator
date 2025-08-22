import asyncio
import os
import pytest

os.environ.setdefault("FAST_TEST_MODE", "")  # ensure real branch used
os.environ.setdefault("SESSIONS_ADAPTATION_CB_FAILURE_THRESHOLD", "2")
os.environ.setdefault("SESSIONS_ADAPTATION_CB_RESET_SECONDS", "0.5")
os.environ.setdefault("RECOMMEND_HTTP_TIMEOUT", "0.2")

from services.sessions.sessions.main import recommendation_stream  # type: ignore
from services.sessions.sessions.main import db  # in-memory fallback if needed


@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_resets(monkeypatch):
    # Prepare session doc
    sid = "test-session-cb"
    await db.sessions.insert_one({"_id": sid, "learner_id": "learner-x"})

    calls = {"count": 0}

    class DummyResp:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data

        def json(self):
            return self._json

    async def fake_post(url, json=None, headers=None):  # noqa: A002
        calls["count"] += 1
        # First two calls fail -> open circuit
        if calls["count"] <= 2:
            raise RuntimeError("boom")
        # After circuit opens we shouldn't reach here until half-open trial after reset time.
        return DummyResp(200, {"content_id": "ok"})

    class DummyClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        post = staticmethod(fake_post)

    monkeypatch.setattr(
        "services.sessions.sessions.main.httpx.AsyncClient", DummyClient
    )

    gen = recommendation_stream(sid)
    rec_types = []
    start = asyncio.get_event_loop().time()
    opened = False
    async for evt in gen:
        if evt["event"] == "recommendation":
            rec_types.append(evt["data"])
            if rec_types and any(
                d.get("error") == "adaptation_circuit_open" for d in rec_types
            ):
                opened = True
        # After seeing open fallback, wait for reset window then continue
        if (
            opened
            and (asyncio.get_event_loop().time() - start) < 10
            and not any("content_id" in d for d in rec_types)
        ):
            # sleep longer than reset to allow half-open trial
            await asyncio.sleep(0.6)
        if any("content_id" in d and d.get("content_id") == "ok" for d in rec_types):
            break
        if len(rec_types) > 10:
            break
        if asyncio.get_event_loop().time() - start > 10:
            break
        await asyncio.sleep(0)

    # We expect at least one fallback recommendation containing error before success
    assert any("error" in d for d in rec_types), rec_types
    assert any(
        "content_id" in d and d.get("content_id") == "ok" for d in rec_types
    ), rec_types
    # Circuit should have opened at some point
    assert calls["count"] >= 2


import os
import pytest
from services.sessions.sessions.main import _use_memory  # type: ignore


@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_recovers(monkeypatch):
    # Force non-fast mode
    monkeypatch.delenv("FAST_TEST_MODE", raising=False)
    # Configure low thresholds
    monkeypatch.setenv("SESSIONS_ADAPTATION_CB_FAILURE_THRESHOLD", "2")
    monkeypatch.setenv("SESSIONS_ADAPTATION_CB_RESET_SECONDS", "1")
    # Force invalid ADAPTATION_URL so calls fail
    monkeypatch.setenv("ADAPTATION_URL", "http://127.0.0.1:59999")

    # Ensure session exists (in-memory ok)
    if _use_memory is False:
        # Switch to memory if needed for isolation
        from services.sessions.sessions.main import InMemoryDB as _IMDB  # type: ignore
        from services.sessions.sessions import main as m  # type: ignore

        m.db = _IMDB()
        m._use_memory = True
    session_id = "test-session"
    await db.sessions.insert_one({"_id": session_id, "learner_id": "L1"})

    stream = recommendation_stream(session_id, request_id="test")
    rec_types = []
    async for evt in stream:
        if evt["event"] == "recommendation":
            rec_types.append(evt["data"].get("error") or "ok")
        if len(rec_types) >= 6:
            break
    # Expect first two attempts to be real failures (adaptation_exception/unavailable) then circuit open fallback
    # Because of connection refused -> adaptation_exception
    assert any(
        e in ("adaptation_exception", "adaptation_unavailable") for e in rec_types[:2]
    )
    assert "adaptation_circuit_open" in rec_types, f"Circuit did not open: {rec_types}"
    # Wait for reset window to allow half-open trial
    await asyncio.sleep(1.2)
    # Collect a few more after reset
    async for evt in recommendation_stream(session_id, request_id="test2"):
        if evt["event"] == "recommendation":
            rec_types.append(evt["data"].get("error") or "ok")
        if len(rec_types) >= 9:
            break
    # After reset, still failing because endpoint invalid, circuit should re-open again
    assert "adaptation_circuit_open" in rec_types[-3:], rec_types
