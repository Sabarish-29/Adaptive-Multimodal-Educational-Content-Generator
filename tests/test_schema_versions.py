"""Schema version tests using in-memory fake DB to avoid real Mongo dependency.

We monkeypatch each service module's `db` attribute with a FakeDB whose collections
capture inserted documents. We then exercise key write endpoints and assert that
inserted records include `schema_version` == 1.
"""

import importlib
import asyncio
import sys
import pathlib
import importlib.util
import types
from fastapi.testclient import TestClient
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
PKGS = ROOT / "packages"
if PKGS.exists() and str(PKGS) not in sys.path:
    sys.path.append(str(PKGS))


def load_module_from_path(mod_name: str, rel_path: str):
    full = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, full)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    # Ensure common_utils import path works (service code expects 'common_utils.request')
    if "common_utils.request" not in sys.modules:
        inner = ROOT / "packages" / "common_utils" / "common_utils" / "request.py"
        if inner.exists():
            inner_spec = importlib.util.spec_from_file_location(
                "common_utils.request", inner
            )
            inner_mod = importlib.util.module_from_spec(inner_spec)  # type: ignore
            assert inner_spec and inner_spec.loader
            inner_spec.loader.exec_module(inner_mod)  # type: ignore
            sys.modules["common_utils.request"] = inner_mod
            # Also register package root if absent
            if "common_utils" not in sys.modules:
                pkg = types.ModuleType("common_utils")
                # Point package path to inner directory so submodule imports resolve
                pkg.__path__ = [
                    str((ROOT / "packages" / "common_utils" / "common_utils").resolve())
                ]  # type: ignore
                sys.modules["common_utils"] = pkg
            setattr(sys.modules["common_utils"], "request", inner_mod)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore
    return module


class _FakeInsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class _FakeUpdateResult: ...


class _FakeFindCursor:
    def __init__(self, docs):
        self._docs = docs

    def limit(self, n):
        return self

    def __aiter__(self):
        async def gen():
            for d in list(self._docs):
                yield d

        return gen()


class FakeCollection:
    def __init__(self):
        self.docs = []
        self._id_counter = 0

    async def find_one(self, filt):
        for d in self.docs:
            if all(d.get(k) == v for k, v in filt.items()):
                return d
        return None

    async def insert_one(self, doc):
        if "_id" not in doc:
            self._id_counter += 1
            doc["_id"] = str(self._id_counter)
        self.docs.append(doc)
        return _FakeInsertOneResult(doc["_id"])

    async def insert_many(self, docs, ordered=False):
        for d in docs:
            await self.insert_one(d)
        return SimpleNamespace(inserted_ids=[d["_id"] for d in docs])

    async def update_one(self, filt, update, upsert=False):
        doc = await self.find_one(filt)
        if not doc and upsert:
            doc = {**filt}
            self.docs.append(doc)
        if not doc:
            return _FakeUpdateResult()
        inc = update.get("$inc", {})
        for k, v in inc.items():
            doc[k] = doc.get(k, 0) + v
        setv = update.get("$set", {})
        for k, v in setv.items():
            doc[k] = v
        return _FakeUpdateResult()

    async def delete_many(self, filt):
        self.docs = [
            d for d in self.docs if not all(d.get(k) == v for k, v in filt.items())
        ]

    async def estimated_document_count(self):
        return len(self.docs)

    def find(self):
        return _FakeFindCursor(self.docs)


class FakeDB:
    def __init__(self):
        self.policies = FakeCollection()
        self.adaptation_recs = FakeCollection()
        self.arm_feedback = FakeCollection()
        self.bandit_posteriors = FakeCollection()
        self.content_bundles = FakeCollection()
        self.evaluations = FakeCollection()
        self.audit_logs = FakeCollection()
        self.rag_docs = FakeCollection()
        self.rag_answers = FakeCollection()


def _install_motor_stub():
    """Install a lightweight stub for motor.motor_asyncio so service imports don't pull real motor/pymongo."""
    if "motor.motor_asyncio" in sys.modules:
        return
    dummy_mod = types.ModuleType("motor.motor_asyncio")

    class _DummyClient:
        def __init__(self, *a, **k):
            pass

        def __getitem__(self, name):
            # return simple namespace; will be replaced by our FakeDB right after import
            return types.SimpleNamespace()

    setattr(dummy_mod, "AsyncIOMotorClient", _DummyClient)
    root = types.ModuleType("motor")
    setattr(root, "motor_asyncio", dummy_mod)
    sys.modules["motor"] = root
    sys.modules["motor.motor_asyncio"] = dummy_mod


def test_adaptation_schema_version():
    _install_motor_stub()
    mod = load_module_from_path(
        "adaptation_main", "services/adaptation/adaptation/main.py"
    )
    fake = FakeDB()
    mod.db = fake
    # Rebind db in function globals so previously bound references use fake
    for fname in [
        "get_bandit_policy",
        "get_or_init_posterior",
        "sample_arm_scores",
        "recommend_next",
        "feedback",
    ]:
        if hasattr(mod, fname):
            getattr(mod, fname).__globals__["db"] = fake  # type: ignore
    client = TestClient(mod.app)
    # seed active policy
    asyncio.get_event_loop().run_until_complete(
        fake.policies.insert_one(
            {
                "type": "bandit",
                "active": True,
                "arms": [
                    {
                        "id": "arm1",
                        "modalities": ["text"],
                        "chunk_size": 1,
                        "difficulty": "easy",
                    }
                ],
                "priors": {"alpha": 1, "beta": 1},
            }
        )
    )
    rec = client.post(
        "/v1/adaptation/recommend-next", json={"ctx": {"learner_id": "L1"}}
    )
    if rec.status_code != 200:
        print("Adaptation rec failure body:", rec.text)
    assert rec.status_code == 200
    rec_doc = asyncio.get_event_loop().run_until_complete(
        fake.adaptation_recs.find_one({"learner_id": "L1"})
    )
    assert rec_doc and rec_doc.get("schema_version") == 1
    fb = client.post(
        "/v1/adaptation/feedback",
        json={"fb": {"learner_id": "L1", "arm": "arm1", "reward": 0.9}},
    )
    assert fb.status_code in (200, 204)
    fb_doc = asyncio.get_event_loop().run_until_complete(
        fake.arm_feedback.find_one({"learner_id": "L1"})
    )
    assert fb_doc and fb_doc.get("schema_version") == 1


def test_contentgen_schema_version():
    _install_motor_stub()
    mod = load_module_from_path(
        "contentgen_main", "services/contentgen/contentgen/main.py"
    )
    fake = FakeDB()
    mod.db = fake
    client = TestClient(mod.app)
    payload = {"learner_id": "L2", "unit_id": "U1", "objectives": ["obj1", "obj2"]}
    r = client.post("/v1/generate/lesson", json={"req": payload})
    assert r.status_code == 200
    bundle_doc = asyncio.get_event_loop().run_until_complete(
        fake.content_bundles.find_one({"learner_id": "L2"})
    )
    assert bundle_doc and bundle_doc.get("schema_version") == 1
    eval_doc = asyncio.get_event_loop().run_until_complete(
        fake.evaluations.find_one({"bundle_id": r.json()["bundle_id"]})
    )
    assert eval_doc and eval_doc.get("schema_version") == 1


def test_rag_schema_version():
    _install_motor_stub()
    mod = load_module_from_path("rag_main", "services/rag/rag/main.py")
    fake = FakeDB()
    mod.db = fake
    client = TestClient(mod.app)
    idx = client.post(
        "/v1/rag/index",
        json={
            "documents": [{"doc_id": "d1", "text": "Alpha beta gamma", "metadata": {}}]
        },
    )
    assert idx.status_code == 200
    doc = asyncio.get_event_loop().run_until_complete(
        fake.rag_docs.find_one({"doc_id": "d1"})
    )
    assert doc and doc.get("schema_version") == 1
    q = client.post("/v1/rag/query", json={"query": "alpha", "top_k": 1})
    assert q.status_code == 200
    ans = asyncio.get_event_loop().run_until_complete(
        fake.rag_answers.find_one({"query": "alpha"})
    )
    assert ans and ans.get("schema_version") == 1
