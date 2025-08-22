"""Reusable in-memory async Mongo-style stub for tests.

Provides collections with a minimal subset of Motor/PyMongo async collection methods:
- find_one
- insert_one
- update_one (supports $inc, $set, upsert)
- delete_many
- estimated_document_count

Use: from tests.fakes.inmemory_db import InMemoryMongoClient
client = InMemoryMongoClient()
db = client["edu"]
await db.collection.insert_one({...})

Intentionally simple; NOT for production.
"""

from __future__ import annotations
import uuid
import copy
from typing import Any, Dict


class _InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _UpdateResult:
    def __init__(self, modified_count=1):
        self.modified_count = modified_count


def _get_nested(d: Dict[str, Any], path: str):
    cur = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


class InMemoryCollection:
    def __init__(self):
        self._docs: list[dict] = []

    async def find_one(self, query: dict):
        if not query:
            return copy.deepcopy(self._docs[0]) if self._docs else None
        for doc in self._docs:
            match = True
            for k, v in query.items():
                if k == "_id":
                    if doc.get("_id") != v:
                        match = False
                        break
                else:
                    if _get_nested(doc, k) != v:
                        match = False
                        break
            if match:
                return copy.deepcopy(doc)
        return None

    async def insert_one(self, doc: dict):
        if "_id" not in doc:
            doc["_id"] = uuid.uuid4().hex
        self._docs.append(copy.deepcopy(doc))
        return _InsertResult(doc["_id"])

    async def update_one(self, filt: dict, update: dict, upsert: bool = False):
        target = await self.find_one(filt)
        if target:
            for op, changes in update.items():
                if op == "$inc":
                    for k, inc_v in changes.items():
                        target[k] = target.get(k, 0) + inc_v
                elif op == "$set":
                    for k, set_v in changes.items():
                        target[k] = set_v
            for i, d in enumerate(self._docs):
                if d.get("_id") == target.get("_id"):
                    self._docs[i] = target
        elif upsert:
            new_doc = {**filt}
            for op, changes in update.items():
                if op == "$set":
                    new_doc.update(changes)
            await self.insert_one(new_doc)
        return _UpdateResult()

    async def estimated_document_count(self):
        return len(self._docs)

    async def count_documents(self, filt: dict):
        if not filt:
            return len(self._docs)
        cnt = 0
        for d in self._docs:
            ok = True
            for k, v in filt.items():
                if _get_nested(d, k) != v:
                    ok = False
                    break
            if ok:
                cnt += 1
        return cnt

    async def delete_many(self, filt: dict):
        before = len(self._docs)

        def match(d):
            for k, v in filt.items():
                if d.get(k) != v:
                    return False
            return True

        self._docs = [d for d in self._docs if not match(d)]
        return {"deleted": before - len(self._docs)}


class InMemoryDatabase:
    def __init__(self):
        self._cols: dict[str, InMemoryCollection] = {}

    def __getattr__(self, name: str):
        return self._cols.setdefault(name, InMemoryCollection())

    def __getitem__(self, name: str):
        return self._cols.setdefault(name, InMemoryCollection())

    async def command(self, *a, **k):
        return {}


class InMemoryMongoClient:
    def __init__(self, *a, **k):
        self._dbs: dict[str, InMemoryDatabase] = {}

    def __getitem__(self, name: str):
        return self._dbs.setdefault(name, InMemoryDatabase())
