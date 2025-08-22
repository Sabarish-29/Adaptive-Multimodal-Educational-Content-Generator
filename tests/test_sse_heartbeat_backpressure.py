import asyncio
import pytest


@pytest.mark.asyncio
async def test_heartbeat_and_backpressure(monkeypatch):
    # Configure environment for generator
    monkeypatch.setenv("FAST_TEST_MODE", "true")
    monkeypatch.setenv("SESSIONS_SSE_MAX_EVENTS_PER_SEC", "1")
    monkeypatch.setenv("SESSIONS_SSE_HEARTBEAT_SECONDS", "0.1")
    monkeypatch.setenv("RECOMMEND_STREAM_INTERVAL", "0.4")
    from services.sessions.sessions import main as sess

    # Force in-memory DB to avoid external dependencies
    sess.db = sess.InMemoryDB()  # type: ignore
    sid = "sess-heartbeat"
    await sess.db.sessions.insert_one({"_id": sid, "learner_id": "L1"})  # type: ignore
    gen = sess.recommendation_stream(sid)
    rec_times = []
    saw_heartbeat = False

    async def _consume():
        nonlocal saw_heartbeat
        async for evt in gen:
            if evt.get("event") == "recommendation":
                rec_times.append(asyncio.get_event_loop().time())
                if len(rec_times) >= 2:
                    break
            elif evt.get("event") == "heartbeat":
                saw_heartbeat = True
            # safety to avoid infinite loop in test
            if len(rec_times) >= 2 and saw_heartbeat:
                break

    await asyncio.wait_for(_consume(), timeout=3.0)
    assert len(rec_times) >= 1
    assert saw_heartbeat, "expected at least one heartbeat event"
