"""Quick Mongo connectivity test.

Usage:
  python scripts/test_mongo_connectivity.py --uri mongodb://localhost:27017/edu --db edu
Environment vars respected if flags omitted:
  MONGODB_URI, MONGODB_DB
Exits non-zero on failure.
"""
from __future__ import annotations
import argparse, os, sys, time
from contextlib import suppress

try:
    from pymongo import MongoClient
except ImportError:
    print("[mongo-test] pymongo not installed in current environment.", file=sys.stderr)
    sys.exit(2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--uri', default=os.getenv('MONGODB_URI', 'mongodb://localhost:27017/edu'))
    ap.add_argument('--db', default=os.getenv('MONGODB_DB', 'edu'))
    ap.add_argument('--timeout', type=int, default=int(os.getenv('MONGODB_TIMEOUT_MS', '1000')), help='ms server selection timeout')
    ap.add_argument('--collection', default='__connectivity_probe')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    start = time.time()
    try:
        client = MongoClient(args.uri, serverSelectionTimeoutMS=args.timeout)
        # Force server selection
        info = client.server_info()
        if args.verbose:
            print(f"[mongo-test] server_info: version={info.get('version')} gitVersion={info.get('gitVersion')}")
        db = client[args.db]
        col = db[args.collection]
        doc = {'_id': 'ping', 'ts': time.time()}
        col.replace_one({'_id': 'ping'}, doc, upsert=True)
        fetched = col.find_one({'_id': 'ping'})
        if not fetched:
            print('[mongo-test] Upsert verification failed (no document)')
            sys.exit(3)
        latency_ms = (time.time() - start) * 1000
        print(f"[mongo-test] OK uri={args.uri} db={args.db} latency_ms={latency_ms:.1f}")
        # Clean
        with suppress(Exception):
            col.delete_one({'_id': 'ping'})
    except Exception as e:
        print(f"[mongo-test] FAIL uri={args.uri} error={e.__class__.__name__}:{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
