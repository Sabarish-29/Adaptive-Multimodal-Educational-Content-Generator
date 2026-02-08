"""RAG retrieval pipeline."""

from typing import List, Dict, Any
from .vector_store import VectorStore


class Retriever:
    """Retrieves relevant educational content chunks for a query."""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self._embedder = None

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                pass
        return self._embedder

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Embed query and search vector store."""
        embedder = self._get_embedder()
        if embedder is None:
            return []
        vector = embedder.encode(query).tolist()
        return await self.vector_store.search(vector, limit=top_k)
