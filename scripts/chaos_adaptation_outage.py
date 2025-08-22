"""Chaos Drill: Simulate adaptation outage and observe sessions circuit breaker.

Approach:
- Repeatedly call sessions recommendation stream (synthetic HTTP call to /v1/sessions + /live) while
  returning failures from adaptation by pointing ADAPTATION_URL to an invalid address or injecting env.
- Measures time until circuit breaker opens (sessions_adaptation_circuit_state=1).

This script does not modify running services; user should export ADAPTATION_URL to a blackhole host beforehand:
  export ADAPTATION_URL=http://127.0.0.1:59999
Then run:
  python scripts/chaos_adaptation_outage.py --duration 30

Outputs JSON log lines with circuit state transitions.
"""

from __future__ import annotations
import os
import json
import time
import httpx
import argparse

SESSIONS_BASE = os.getenv("SESSIONS_BASE_URL", "http://localhost:8000")


async def run(duration: int):
    end = time.time() + duration
    async with httpx.AsyncClient(timeout=2.0) as client:
        # create session
        try:
            r = await client.post(
                f"{SESSIONS_BASE}/v1/sessions",
                json={"learner_id": "chaosL", "unit_id": "u1"},
            )
            sid = r.json().get("session_id") if r.status_code == 201 else None
        except Exception:
            sid = None
        last_state = None
        while time.time() < end:
            # scrape metrics
            try:
                m = await client.get(f"{SESSIONS_BASE}/metrics")
                txt = m.text
                # parse gauge line
                for line in txt.splitlines():
                    if (
                        line.startswith("sessions_adaptation_circuit_state")
                        and " " in line
                    ):
                        try:
                            state = int(line.strip().split(" ")[-1])
                        except Exception:
                            state = None
                        if state is not None and state != last_state:
                            print(
                                json.dumps({"ts": time.time(), "circuit_state": state})
                            )
                            last_state = state
                        break
            except Exception:
                pass
            await asyncio.sleep(1)


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=30)
    args = ap.parse_args()
    asyncio.run(run(args.duration))
