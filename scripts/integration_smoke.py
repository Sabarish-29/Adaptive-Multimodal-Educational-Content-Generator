"""Integration smoke test script.

Runs a minimal end-to-end validation of core microservices:
 1. Health checks
 2. Session creation
 3. Adaptation recommendation
 4. SSE live stream (optional)
 5. Session event ingest
 6. Metrics sampling (sessions + adaptation)

Exit code non‑zero if any required check fails.

Usage (Windows PowerShell):
  .\.venv\Scripts\python.exe scripts\integration_smoke.py --sse-events 2

Optional flags:
  --skip-sse            Skip SSE test
  --sse-events N        Number of recommendation events to collect (default 2)
  --sse-timeout SEC     Max seconds to wait for SSE events (default 25)
  --base-host HOST      Hostname (default localhost)
  --out-json PATH       Write JSON summary

Requires: requests, sseclient (for SSE, else skip) .
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
import re
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:  # pragma: no cover
    print("ERROR: requests not installed", file=sys.stderr)
    sys.exit(2)

try:
    import sseclient  # type: ignore
except Exception:  # pragma: no cover
    sseclient = None

SERVICES = [
    ("profiles", 8000),
    ("adaptation", 8001),
    ("sessions", 8002),
    ("contentgen", 8003),
    ("rag", 8005),
    ("curriculum", 8006),
    ("admin", 8007),
    ("analytics", 8008),
]

REQUIRED = {"profiles", "adaptation", "sessions"}  # hard fail if these unhealthy

@dataclass
class StepResult:
    name: str
    success: bool
    detail: str = ""
    data: Any | None = None
    duration_ms: float = 0.0


def _ts():
    return datetime.utcnow().isoformat() + "Z"


def health_checks(host: str) -> StepResult:
    t0 = time.time()
    results: Dict[str, Dict[str, Any]] = {}
    failures: List[str] = []
    for svc, port in SERVICES:
        url = f"http://{host}:{port}/healthz"
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                results[svc] = r.json()
            else:
                failures.append(f"{svc}:{r.status_code}")
        except Exception as e:  # pragma: no cover
            failures.append(f"{svc}:err:{e.__class__.__name__}")
    missing_required = [svc for svc in REQUIRED if svc not in results]
    ok = not missing_required and not failures
    detail = "ok" if ok else f"fail missing={missing_required} other={failures}".strip()
    return StepResult("health", ok, detail, results, (time.time() - t0) * 1000)


def create_session(host: str) -> StepResult:
    t0 = time.time()
    url = f"http://{host}:8002/v1/sessions"
    payload = {"learner_id": "smoke-learner", "unit_id": "unit-1"}
    try:
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code != 201:
            return StepResult("session_create", False, f"status {r.status_code}: {r.text[:200]}")
        sid = r.json().get("session_id")
        ok = isinstance(sid, str) and len(sid) > 0
        return StepResult("session_create", ok, "ok" if ok else "missing session_id", {"session_id": sid}, (time.time() - t0) * 1000)
    except Exception as e:  # pragma: no cover
        return StepResult("session_create", False, f"exc {e}")


def adaptation_recommend(host: str, learner_id: str) -> StepResult:
    t0 = time.time()
    url = f"http://{host}:8001/v1/adaptation/recommend-next"
    try:
        r = requests.post(url, json={"learner_id": learner_id}, timeout=5)
        if r.status_code != 200:
            return StepResult("adaptation_recommend", False, f"status {r.status_code}: {r.text[:160]}")
        data = r.json()
        ok = "arm_id" in data or "arm" in data  # fallback shape
        return StepResult("adaptation_recommend", ok, "ok" if ok else "unexpected payload", data, (time.time() - t0) * 1000)
    except Exception as e:
        return StepResult("adaptation_recommend", False, f"exc {e}")


def sse_stream(host: str, session_id: str, events: int, timeout_s: float) -> StepResult:
    if sseclient is None:
        return StepResult("sse", False, "sseclient not installed – pip install sseclient-py")
    t0 = time.time()
    url = f"http://{host}:8002/v1/sessions/{session_id}/live"
    try:
        with requests.get(url, stream=True, timeout=10) as resp:
            if resp.status_code != 200:
                return StepResult("sse", False, f"status {resp.status_code}")
            client = sseclient.SSEClient(resp)
            recs = []
            start = time.time()
            for evt in client.events():
                if evt.event == "heartbeat":
                    continue
                recs.append({"event": evt.event, "data": evt.data[:300]})
                if len(recs) >= events:
                    break
                if time.time() - start > timeout_s:
                    break
        ok = len(recs) >= events
        return StepResult("sse", ok, f"got {len(recs)}/{events}", recs, (time.time() - t0) * 1000)
    except Exception as e:
        return StepResult("sse", False, f"exc {e}")


def post_session_event(host: str, session_id: str) -> StepResult:
    t0 = time.time()
    url = f"http://{host}:8002/v1/sessions/{session_id}/events"
    ev = {
        "type": "page_view",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {"page": "intro"},
    }
    try:
        r = requests.post(url, json=ev, timeout=5)
        ok = r.status_code == 202
        return StepResult("session_event", ok, f"status {r.status_code}", None, (time.time() - t0) * 1000)
    except Exception as e:
        return StepResult("session_event", False, f"exc {e}")


METRIC_PATTERNS = {
    "sessions_started_total": re.compile(r"^sessions_started_total\s+(\d+(?:\.\d+)?)$"),
    "sessions_recommendation_events_total": re.compile(r"^sessions_recommendation_events_total\{[^}]*source=\"http\"[^}]*}\s+(\d+(?:\.\d+)?)$"),
    "sessions_sse_heartbeats_total": re.compile(r"^sessions_sse_heartbeats_total\s+(\d+(?:\.\d+)?)$"),
    "adaptation_recommendations_total": re.compile(r"^adaptation_recommendations_total\{[^}]*strategy=\"(explore|exploit|cached)\"[^}]*}\s+(\d+(?:\.\d+)?)$"),
}


def metrics_sample(host: str) -> StepResult:
    t0 = time.time()
    out: Dict[str, Any] = {}
    try:
        sess = requests.get(f"http://{host}:8002/metrics", timeout=5).text.splitlines()
        adap = requests.get(f"http://{host}:8001/metrics", timeout=5).text.splitlines()
    except Exception as e:
        return StepResult("metrics", False, f"exc {e}")
    for name, pat in METRIC_PATTERNS.items():
        lines = sess + adap
        vals = []
        for ln in lines:
            m = pat.match(ln)
            if m:
                vals.append(m.groups())
        if vals:
            out[name] = vals
    ok = "sessions_started_total" in out
    return StepResult("metrics", ok, "ok" if ok else "missing sessions_started_total", out, (time.time() - t0) * 1000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-host", default=os.getenv("SMOKE_BASE_HOST", "localhost"))
    ap.add_argument("--skip-sse", action="store_true")
    ap.add_argument("--sse-events", type=int, default=2)
    ap.add_argument("--sse-timeout", type=float, default=25.0)
    ap.add_argument("--out-json")
    args = ap.parse_args()

    steps: List[StepResult] = []

    steps.append(health_checks(args.base_host))
    if not steps[-1].success:
        # proceed but note failure
        pass

    sess_step = create_session(args.base_host)
    steps.append(sess_step)
    session_id = None
    if sess_step.success and isinstance(sess_step.data, dict):
        session_id = sess_step.data.get("session_id")

    steps.append(adaptation_recommend(args.base_host, "smoke-learner"))

    if session_id and not args.skip_sse:
        steps.append(sse_stream(args.base_host, session_id, args.sse_events, args.sse_timeout))
    else:
        steps.append(StepResult("sse", True, "skipped"))

    if session_id:
        steps.append(post_session_event(args.base_host, session_id))
    else:
        steps.append(StepResult("session_event", False, "no session_id"))

    steps.append(metrics_sample(args.base_host))

    summary = {s.name: {"success": s.success, "detail": s.detail, "duration_ms": round(s.duration_ms, 2), "data": s.data} for s in steps}
    overall = all(s.success for s in steps if s.name != "sse" or s.detail != "skipped")

    print("=== Integration Smoke Summary ===")
    for s in steps:
        status = "PASS" if s.success else "FAIL"
        print(f"{s.name:<20} {status}  {s.detail}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")

    if args.out_json:
        try:
            with open(args.out_json, "w", encoding="utf-8") as f:
                json.dump({"timestamp": _ts(), "overall": overall, "steps": summary}, f, indent=2)
        except Exception as e:
            print(f"WARN: could not write json: {e}", file=sys.stderr)

    sys.exit(0 if overall else 1)


if __name__ == "__main__":  # pragma: no cover
    main()
