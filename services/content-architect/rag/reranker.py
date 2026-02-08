"""Cross-encoder re-ranker for RAG results."""

from typing import List, Dict, Any


class Reranker:
    """Re-ranks retrieved documents using a cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load(self):
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
        except ImportError:
            pass

    def rerank(
        self, query: str, documents: List[Dict[str, Any]], top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Re-rank documents by relevance to query."""
        if not documents:
            return []
        if self._model is None:
            self._load()
        if self._model is None:
            return documents[:top_k]

        pairs = [(query, doc.get("payload", {}).get("text", "")) for doc in documents]
        scores = self._model.predict(pairs)
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)
        documents.sort(key=lambda d: d.get("rerank_score", 0), reverse=True)
        return documents[:top_k]
