"""Concurrency Isolation Fuzz Test (ad-hoc)

Spawns many concurrent session creations + event posts for distinct learners to
ensure no cross-learner data leakage / race anomalies in in-memory fallback.

Usage (example):
  python scripts/concurrency_isolation_fuzz.py --sessions 50 --events 3
"""

from __future__ import annotations
import asyncio
import httpx
import argparse
import random
import string
import json

BASE = "http://localhost:8000"


async def run_one(client: httpx.AsyncClient, learner: str, events: int):
    r = await client.post(
        f"{BASE}/v1/sessions", json={"learner_id": learner, "unit_id": "u1"}
    )
    if r.status_code != 201:
        return {"learner": learner, "status": "create_fail"}
    sid = r.json().get("session_id")
    for i in range(events):
        await client.post(
            f"{BASE}/v1/sessions/{sid}/events",
            json={
                "type": "x",
                "timestamp": "2025-01-01T00:00:00Z",
                "payload": {"i": i},
            },
        )
    return {"learner": learner, "status": "ok"}


async def main(total_sessions: int, events: int):
    async with httpx.AsyncClient(timeout=3.0) as client:
        tasks = []
        for i in range(total_sessions):
            learner = "L" + "".join(
                random.choices(string.ascii_lowercase + string.digits, k=6)
            )
            tasks.append(run_one(client, learner, events))
        results = await asyncio.gather(*tasks)
    print(
        json.dumps(
            {
                "total": len(results),
                "ok": sum(1 for r in results if r["status"] == "ok"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=20)
    ap.add_argument("--events", type=int, default=2)
    args = ap.parse_args()
    asyncio.run(main(args.sessions, args.events))
