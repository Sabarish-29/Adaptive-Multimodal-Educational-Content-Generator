"""Minimal SSE client test for sessions live recommendations.

Usage (after stack up):
    python scripts/test_sessions_sse.py --session-id <id>
Will create a session automatically if --session-id omitted.
"""

from __future__ import annotations
import argparse
import sys
import time
import requests
import sseclient

import os
API = os.getenv("SESSIONS_TEST_BASE", "http://localhost:9000/api/sessions")


def create_session(learner: str = "learner-demo", unit: str = "unit-1") -> str:
    url = f"{API}/v1/sessions"
    r = requests.post(url, json={"learner_id": learner, "unit_id": unit})
    r.raise_for_status()
    return r.json()["session_id"]


def stream(session_id: str, limit: int = 5, timeout: float = 30.0, verbose: bool = False):
    url = f"{API}/v1/sessions/{session_id}/live"
    start = time.time()
    with requests.get(url, stream=True) as resp:
        resp.raise_for_status()
        client = sseclient.SSEClient(resp)
        count = 0
        last_print = time.time()
        for event in client.events():
            if event.event == "heartbeat":
                if verbose and (time.time() - last_print) > 2:
                    print("(heartbeat)")
                    last_print = time.time()
                continue
            print(f"EVENT {event.event}: {event.data[:200]}")
            count += 1
            if count >= limit:
                break
            if time.time() - start > timeout:
                print("Timeout waiting for events", file=sys.stderr)
                break
        if count == 0:
            print("No events received before stream ended / timeout.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session-id")
    ap.add_argument("--events", type=int, default=5)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--base", help="Explicit base URL (overrides SESSIONS_TEST_BASE)")
    args = ap.parse_args()
    global API
    if args.base:
        API = args.base.rstrip('/')
    sid = args.session_id or create_session()
    print("Using session", sid)
    print("Streaming from base:", API)
    stream(sid, args.events, args.timeout, args.verbose)


if __name__ == "__main__":
    main()
