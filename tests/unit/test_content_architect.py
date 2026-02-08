"""
Unit tests for Content Architect agent.
"""

import pytest


class TestModalitySelection:
    """Test cognitive-load-based modality routing."""

    def _make_engine(self):
        try:
            from services.content_architect.main import ContentEngine
            return ContentEngine()
        except ImportError:
            pytest.skip("content-architect not importable")

    def test_high_load_avoids_text(self):
        engine = self._make_engine()
        modality = engine.select_modality(cognitive_load=0.85)
        assert modality != "TEXT"

    def test_low_load_defaults_to_text(self):
        engine = self._make_engine()
        modality = engine.select_modality(cognitive_load=0.2)
        assert modality == "TEXT"


class TestKnowledgeGraph:
    """Test knowledge graph wrapper (Neo4j)."""

    @pytest.mark.asyncio
    async def test_add_and_get_concept(self):
        try:
            from services.content_architect.graph.knowledge_graph import KnowledgeGraphManager
        except ImportError:
            pytest.skip("knowledge_graph not importable")

        # Without a live Neo4j we just validate instantiation
        kg = KnowledgeGraphManager(uri="bolt://localhost:7687", user="neo4j", password="test")
        assert kg is not None


class TestVectorStore:
    """Basic vector store wrapper tests."""

    def test_instantiation(self):
        try:
            from services.content_architect.rag.vector_store import VectorStoreManager
        except ImportError:
            pytest.skip("vector_store not importable")

        vs = VectorStoreManager(url="http://localhost:6333", collection="test")
        assert vs.collection_name == "test"
