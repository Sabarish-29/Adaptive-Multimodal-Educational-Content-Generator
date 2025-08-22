"""Compare latest k6 JSON summary to baseline to flag p95 regression.

Usage:
  python scripts/perf_regression.py --current results/latest.json --baseline results/baseline.json --max-p95-increase 0.2

Baseline format: k6 summary export (use k6 run --summary-export=baseline.json ...)
"""

from __future__ import annotations
import json
import argparse
import sys

KEYS = [
    ("metrics", "session_create_latency", "p(95)"),
    ("metrics", "session_event_latency", "p(95)"),
]


def get_metric(summary: dict, metric: str, stat: str):
    m = summary.get("metrics", {}).get(metric)
    if not m:
        return None
    return m.get(stat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument(
        "--max-p95-increase",
        type=float,
        default=0.2,
        help="Allowed relative increase (0.2 = 20%)",
    )
    args = ap.parse_args()
    with open(args.baseline, "r", encoding="utf-8") as f:
        base = json.load(f)
    with open(args.current, "r", encoding="utf-8") as f:
        cur = json.load(f)
    failures = []
    for metric in ("session_create_latency", "session_event_latency"):
        b = get_metric(base, metric, "p(95)")
        c = get_metric(cur, metric, "p(95)")
        if b is None or c is None:
            continue
        if b == 0:
            continue
        rel = (c - b) / b
        if rel > args.max_p95_increase:
            failures.append(
                {"metric": metric, "baseline_p95": b, "current_p95": c, "increase": rel}
            )
    if failures:
        print(json.dumps({"regression": True, "failures": failures}, indent=2))
        sys.exit(1)
    print(json.dumps({"regression": False}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
