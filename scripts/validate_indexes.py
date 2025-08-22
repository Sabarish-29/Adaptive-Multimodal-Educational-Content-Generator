#!/usr/bin/env python
"""Validate presence of critical MongoDB indexes & schema markers.
Usage: python scripts/validate_indexes.py
"""

import os
import sys
import motor.motor_asyncio
import asyncio

REQUIRED_INDEXES = {
    "bandit_posteriors": [("arm_id", 1)],
    "arm_feedback": [("learner_id", 1), ("arm", 1)],
    "adaptation_recs": [("learner_id", 1)],
    "content_bundles": [("hashes.input_hash", 1)],
    "events": [("created_at", 1)],
    "rag_docs": [("doc_id", 1)],
}


async def main():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
    db_name = os.getenv("MONGODB_DB", "edu")
    client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    db = client[db_name]
    missing = []
    for coll, spec in REQUIRED_INDEXES.items():
        try:
            existing = await db[coll].index_information()
            # flatten index key tuples
            existing_keys = [
                tuple(v["key"]) if isinstance(v, dict) else tuple(v)
                for v in existing.values()
            ]
            need = tuple(spec)
            if need not in existing_keys:
                missing.append((coll, need))
        except Exception as e:
            missing.append((coll, f"error:{e}"))
    if missing:
        print("MISSING_INDEXES", missing)
        sys.exit(1)
    print("INDEX_VALIDATION_OK")


if __name__ == "__main__":
    asyncio.run(main())
