"""Rotation helper for FIELD_ENCRYPTION_KEY.

Generates a new random 32-byte key (base64) and writes it to an output file.
Optionally updates an env file with FIELD_ENCRYPTION_KEY=<value> or FIELD_ENCRYPTION_KEY_NEW.
Records rotation metadata (timestamp, file path) in a JSON metadata file if provided.

Usage:
  python scripts/rotate_encryption_key.py --out secrets/field_key_<date>.b64 --env-update .env --meta rotations.json

This script does NOT modify running services; deploy new secret separately.
"""

from __future__ import annotations
import os
import base64
import argparse
import json
import datetime
import sys
import pathlib

DEF_BYTES = 32


def gen_key(n: int = DEF_BYTES) -> str:
    return base64.b64encode(os.urandom(n)).decode()


def append_env(path: pathlib.Path, key: str, value: str, new_var: bool):
    line_key = "FIELD_ENCRYPTION_KEY_NEW" if new_var else "FIELD_ENCRYPTION_KEY"
    content = (
        f"\n# rotated {datetime.datetime.utcnow().isoformat()}Z\n{line_key}={value}\n"
    )
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)


def update_meta(meta_path: pathlib.Path, record: dict):
    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8") or "[]")
            if not isinstance(data, list):
                data = [data]
        except Exception:
            data = []
    else:
        data = []
    data.append(record)
    meta_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Path to write raw base64 key file")
    ap.add_argument(
        "--bytes", type=int, default=DEF_BYTES, help="Raw key bytes (16/24/32)"
    )
    ap.add_argument(
        "--env-update", help="Append export line to this .env or env snippet file"
    )
    ap.add_argument("--meta", help="JSON metadata log file of rotations")
    ap.add_argument(
        "--new-var",
        action="store_true",
        help="Use FIELD_ENCRYPTION_KEY_NEW instead of FIELD_ENCRYPTION_KEY (for dual rotation window)",
    )
    args = ap.parse_args()

    if args.bytes not in (16, 24, 32):
        print("Key size must be 16,24,32 bytes", file=sys.stderr)
        sys.exit(2)

    key_b64 = gen_key(args.bytes)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(key_b64 + "\n", encoding="utf-8")
    print(f"Wrote new key to {out_path}")

    if args.env_update:
        append_env(
            pathlib.Path(args.env_update),
            key="FIELD_ENCRYPTION_KEY",
            value=key_b64,
            new_var=args.new_var,
        )
        print(f"Appended key line to {args.env_update}")

    if args.meta:
        update_meta(
            pathlib.Path(args.meta),
            {
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
                "key_file": str(out_path),
                "bytes": args.bytes,
                "env_file": args.env_update,
                "new_var": bool(args.new_var),
            },
        )
        print(f"Updated metadata log {args.meta}")


if __name__ == "__main__":  # pragma: no cover
    main()
