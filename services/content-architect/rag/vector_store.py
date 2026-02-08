"""Qdrant vector store integration for RAG."""

from typing import List, Dict, Any, Optional


class VectorStore:
    """Wrapper around Qdrant for semantic search over educational content."""

    def __init__(
        self,
        url: str = "http://qdrant:6333",
        collection_name: str = "educational_content",
    ):
        self._url = url
        self._collection = collection_name
        self._client = None

    async def connect(self):
        try:
            from qdrant_client import AsyncQdrantClient
            self._client = AsyncQdrantClient(url=self._url)
        except ImportError:
            pass

    async def search(
        self, query_vector: List[float], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Semantic search in the vector store."""
        if not self._client:
            return []
        from qdrant_client.models import SearchRequest
        results = await self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=limit,
        )
        return [
            {"id": str(r.id), "score": r.score, "payload": r.payload}
            for r in results
        ]

    async def upsert(self, doc_id: str, vector: List[float], payload: Dict):
        """Insert or update a document."""
        if not self._client:
            return
        from qdrant_client.models import PointStruct
        await self._client.upsert(
            collection_name=self._collection,
            points=[PointStruct(id=doc_id, vector=vector, payload=payload)],
        )
