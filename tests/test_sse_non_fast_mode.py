import asyncio
import pytest


@pytest.mark.asyncio
async def test_sse_stream_non_fast_mode(monkeypatch):
    # Ensure non-fast mode (default) and set short intervals
    monkeypatch.delenv("FAST_TEST_MODE", raising=False)
    monkeypatch.setenv("RECOMMEND_STREAM_INTERVAL", "0.2")
    monkeypatch.setenv("SESSIONS_SSE_HEARTBEAT_SECONDS", "0.5")
    monkeypatch.setenv(
        "ADAPTATION_URL", "http://localhost:59999"
    )  # unreachable to trigger failures / circuit
    from services.sessions.sessions import main as sess

    sess.db = sess.InMemoryDB()  # in-memory
    sid = "sse-nonfast"
    await sess.db.sessions.insert_one({"_id": sid, "learner_id": "L1"})  # type: ignore
    gen = sess.recommendation_stream(sid)
    events = []

    async def _consume():
        async for evt in gen:
            events.append(evt)
            if len(events) >= 5:
                break

    await asyncio.wait_for(_consume(), timeout=5.0)
    # We expect recommendation fallback events (error/unavailable) given bad adaptation URL
    recs = [e for e in events if e.get("event") == "recommendation"]
    assert len(recs) >= 1
    # Circuit may open after threshold; allow presence of adaptation_circuit_open fallback
    has_fallback = any("error" in (e.get("data") or {}) for e in recs)
    assert has_fallback or any(
        e.get("data", {}).get("error") == "adaptation_circuit_open" for e in recs
    )
