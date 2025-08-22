from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import motor.motor_asyncio
import numpy as np
import hashlib, os
from datetime import datetime

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/edu")
MONGODB_DB = os.getenv("MONGODB_DB", "edu")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]

app = FastAPI(title="RAG Service", version="0.2.0")

EMBED_DIM = 32

class IndexDocument(BaseModel):
    doc_id: str
    text: str
    metadata: Dict[str, Any] = {}

class RAGIndexRequest(BaseModel):
    documents: List[IndexDocument]

class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 3

class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

class VectorStore:
    def embed(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode()).digest()
        nums = [b for b in h[:EMBED_DIM]]
        vec = np.array(nums, dtype=np.float32)
        return (vec / (np.linalg.norm(vec) + 1e-8)).tolist()
    async def index(self, docs: List[IndexDocument]):
        ops = []
        for d in docs:
            ops.append({
                "doc_id": d.doc_id,
                "text": d.text,
                "metadata": d.metadata,
                "embedding": self.embed(d.text),
                "created_at": datetime.utcnow(),
                "schema_version": 1
            })
        if ops:
            await db.rag_docs.insert_many(ops, ordered=False)
        return len(ops)
    async def search(self, query: str, top_k: int):
        qv = np.array(self.embed(query))
        cur = db.rag_docs.find().limit(500)
        scored = []
        async for d in cur:
            v = np.array(d.get("embedding", [0]*EMBED_DIM))
            score = float(np.dot(qv, v))
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:top_k]]

store = VectorStore()

@app.post("/v1/rag/index")
async def index_docs(payload: RAGIndexRequest):
    count = await store.index(payload.documents)
    return {"indexed": count}

@app.post("/v1/rag/query", response_model=RAGQueryResponse)
async def rag_query(q: RAGQueryRequest):
    top_docs = await store.search(q.query, q.top_k)
    sources = []
    for rank, d in enumerate(top_docs, start=1):
        v = d.get("embedding", [0]*EMBED_DIM)
        # recompute similarity for response (store.search returns docs only)
        score = float(np.dot(np.array(store.embed(q.query)), np.array(v)))
        sources.append({
            "doc_id": d.get("doc_id"),
            "snippet": d.get("text")[:160],
            "score": score,
            "citation_label": f"[{rank}]"
        })
    answer = "Stub answer referencing " + ", ".join(s["citation_label"] for s in sources)
    res = {
        "answer": answer,
        "sources": sources
    }
    # store answer provenance
    await db.rag_answers.insert_one({"query": q.query, **res, "created_at": datetime.utcnow(), "schema_version": 1})
    return res

@app.get("/v1/rag/sources/{answer_id}")
async def rag_sources(answer_id: str):
    doc = await db.rag_answers.find_one({"_id": answer_id})  # placeholder; would use ObjectId
    if not doc:
        return {"sources": []}
    return {"sources": doc.get("sources", [])}

@app.get("/healthz")
async def health():
    return {"status": "ok"}
