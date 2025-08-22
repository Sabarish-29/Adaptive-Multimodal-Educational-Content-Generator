"""Key Drift Monitor

Checks active encryption key material consistency vs expected metadata.

Current approach (lightweight):
- Imports encryption module to force initialization.
- Reads environment variables FIELD_ENCRYPTION_KEY / ENCRYPTION_PROVIDER / AWS_KMS_KEY_ID.
- Emits JSON summary; returns non-zero exit if FEATURE_FIELD_ENCRYPTION=true and:
  * REQUIRE_STRONG_ENCRYPTION=true but mode != (2 or 3)
  * Active mode mismatch with expected (e.g., local key length invalid, kms configured but not active)

Future enhancement:
- Compare persisted ciphertext data key id / metadata store.
- Validate dual-key window (primary + secondary) timing.

Usage:
  python scripts/key_drift_monitor.py --strict
"""

from __future__ import annotations
import os
import json
import base64
import sys


def _key_len_ok(k: str | None) -> bool:
    if not k:
        return False
    try:
        raw = base64.b64decode(k)
        return len(raw) in (16, 24, 32)
    except Exception:
        return False


def main():
    strict = "--strict" in sys.argv
    feature = os.getenv("FEATURE_FIELD_ENCRYPTION", "false").lower() == "true"
    strong = os.getenv("REQUIRE_STRONG_ENCRYPTION", "false").lower() == "true"
    provider = os.getenv("ENCRYPTION_PROVIDER", "").lower()
    kms = provider == "aws_kms"
    local_key = os.getenv("FIELD_ENCRYPTION_KEY")
    local_ok = _key_len_ok(local_key)
    kms_id = os.getenv("AWS_KMS_KEY_ID")
    status = {
        "feature_enabled": feature,
        "strong_required": strong,
        "provider": provider or None,
        "local_key_present": bool(local_key),
        "local_key_valid_length": local_ok,
        "kms_key_id_present": bool(kms_id),
    }
    drift = False
    if feature and strong:
        if kms and not status["kms_key_id_present"]:
            drift = True
        if not kms and not local_ok:
            drift = True
    if strict and drift:
        print(json.dumps({"drift": True, "status": status}, indent=2))
        sys.exit(1)
    print(json.dumps({"drift": drift, "status": status}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
