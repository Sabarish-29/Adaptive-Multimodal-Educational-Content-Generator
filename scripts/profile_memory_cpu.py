"""Lightweight memory/CPU profiling harness.

Runs a target coroutine or HTTP loop and samples process RSS + CPU percent.
Requires psutil.

Usage:
  python scripts/profile_memory_cpu.py --duration 10 --interval 0.5
"""

from __future__ import annotations
import time
import argparse
import json

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore


def sample(duration: float, interval: float):
    if not psutil:
        print(json.dumps({"error": "psutil not installed"}))
        return
    p = psutil.Process()
    end = time.time() + duration
    out = []
    while time.time() < end:
        rss = p.memory_info().rss
        cpu = p.cpu_percent(interval=None)
        out.append({"t": time.time(), "rss_bytes": rss, "cpu_percent": cpu})
        time.sleep(interval)
    print(
        json.dumps(
            {"samples": out, "duration": duration, "interval": interval}, indent=2
        )
    )


if __name__ == "__main__":  # pragma: no cover
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=10)
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()
    sample(args.duration, args.interval)
