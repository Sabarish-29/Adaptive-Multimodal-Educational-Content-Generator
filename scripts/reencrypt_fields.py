"""Field Re-encryption Utility

Purpose:
  Re-encrypt encrypted document fields with a newly rotated key.

Current Scope:
  - Simulated data source (no DB calls) to keep logic testable/offline.
  - Implements pagination, resume, progress reporting, dry-run vs execute,
        per-record error capture, and state checkpoint.

Intended Future Extension:
  - Replace `_fetch_batch` with real DB query (sorted by _id or key_version).
  - Integrate decryption using old key, encryption with new key via
        common_utils.encryption helpers.
  - Persist key_version metadata on update.

Usage Examples:
  Dry run first  (default batch=100):
        python scripts/reencrypt_fields.py --dry-run
  Execute with smaller batch and state file for resume:
        python scripts/reencrypt_fields.py --state .reencrypt_state.json --batch 50
  Resume after interruption:
        python scripts/reencrypt_fields.py --state .reencrypt_state.json
"""

from __future__ import annotations
import argparse
import json
import datetime
import time
import os
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

STATE_VERSION = 1


@dataclass
class State:
    version: int = STATE_VERSION
    last_id: str | None = None
    processed: int = 0
    updated: int = 0
    errors: int = 0
    total_estimate: int | None = None


def load_state(path: str | None) -> State:
    if not path or not os.path.exists(path):
        return State()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return State(**data)
    except Exception:
        return State()


def save_state(path: str | None, st: State):
    if not path:
        return
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(asdict(st), f, indent=2)
    os.replace(tmp, path)


def _simulate_dataset() -> List[Dict[str, Any]]:
    # Simulated 10 records with key_version=1 needing upgrade to 2
    return [
        {"_id": f"doc{i:03d}", "encrypted_field": "enc:<...>", "key_version": 1}
        for i in range(1, 11)
    ]


def _fetch_batch(
    all_docs: List[Dict[str, Any]], after_id: str | None, limit: int
) -> List[Dict[str, Any]]:
    # Sort by _id lexicographically for deterministic pagination
    all_docs_sorted = sorted(all_docs, key=lambda d: d["_id"])
    start_index = 0
    if after_id:
        for idx, doc in enumerate(all_docs_sorted):
            if doc["_id"] == after_id:
                start_index = idx + 1
                break
    batch = []
    for doc in all_docs_sorted[start_index:]:
        if doc.get("key_version") == 1:  # candidate needing re-encryption
            batch.append(doc)
        if len(batch) >= limit:
            break
    return batch


def _reencrypt(doc: Dict[str, Any], new_version: int, dry_run: bool) -> bool:
    # Simulated re-encryption: just change key_version; could raise error randomly
    if not dry_run:
        doc["key_version"] = new_version
    return True


def process(
    dry_run: bool, batch_size: int, state_path: str | None, target_version: int
) -> State:
    st = load_state(state_path)
    dataset = _simulate_dataset()
    if st.total_estimate is None:
        st.total_estimate = sum(
            1 for d in dataset if d.get("key_version") != target_version
        )
    start_time = time.time()
    while True:
        batch = _fetch_batch(dataset, st.last_id, batch_size)
        if not batch:
            break
        for doc in batch:
            st.processed += 1
            st.last_id = doc["_id"]
            try:
                if doc.get("key_version") != target_version:
                    ok = _reencrypt(doc, target_version, dry_run)
                    if ok and not dry_run:
                        st.updated += 1
                # dry-run counts potential updates
                elif dry_run:
                    pass
            except Exception:
                st.errors += 1
            if state_path and (st.processed % 10 == 0):
                save_state(state_path, st)
        # Progress output per batch
        pct = 0.0
        if st.total_estimate:
            pct = (st.processed / st.total_estimate) * 100
        print(
            json.dumps(
                {
                    "ts": datetime.datetime.utcnow().isoformat() + "Z",
                    "dry_run": dry_run,
                    "batch_processed": len(batch),
                    "processed_total": st.processed,
                    "updated": st.updated,
                    "errors": st.errors,
                    "progress_pct": round(pct, 2),
                    "last_id": st.last_id,
                }
            )
        )
        save_state(state_path, st)
    duration = time.time() - start_time
    # Print summary as single-line JSON for easier parsing in tests
    print(
        json.dumps({"summary": True, "duration_sec": round(duration, 2), **asdict(st)})
    )
    return st


def main():  # pragma: no cover - thin CLI wrapper
    ap = argparse.ArgumentParser(
        description="Re-encrypt encrypted fields to new key version (simulated)."
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify data; report candidates and counts.",
    )
    ap.add_argument("--batch", type=int, default=100, help="Batch size for pagination.")
    ap.add_argument("--state", type=str, help="Checkpoint state file for resume.")
    ap.add_argument(
        "--target-version", type=int, default=2, help="New key version to apply."
    )
    args = ap.parse_args()
    st = process(args.dry_run, args.batch, args.state, args.target_version)
    # Exit non-zero if errors when not dry-run
    if not args.dry_run and st.errors > 0:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
