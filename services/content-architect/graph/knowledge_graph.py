"""Knowledge Graph integration – Neo4j driver wrapper."""

from typing import Dict, List, Any, Optional


class KnowledgeGraph:
    """
    Interface to Neo4j for concept relationships, prerequisites,
    and learning path computation.
    """

    def __init__(self, uri: str = "bolt://neo4j:7687", user: str = "neo4j", password: str = "neurosync"):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = None

    async def connect(self):
        try:
            from neo4j import AsyncGraphDatabase
            self._driver = AsyncGraphDatabase.driver(self._uri, auth=(self._user, self._password))
        except ImportError:
            pass

    async def close(self):
        if self._driver:
            await self._driver.close()

    async def get_prerequisites(self, concept: str) -> List[str]:
        """Get prerequisite concepts from the graph."""
        if not self._driver:
            return []
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (c:Concept {name: $name})<-[:PREREQUISITE_FOR]-(p:Concept) "
                "RETURN p.name AS prerequisite",
                name=concept,
            )
            records = await result.data()
            return [r["prerequisite"] for r in records]

    async def get_related_concepts(self, concept: str, limit: int = 5) -> List[str]:
        """Get related concepts."""
        if not self._driver:
            return []
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (c:Concept {name: $name})-[:RELATED_TO]-(r:Concept) "
                "RETURN r.name AS related LIMIT $limit",
                name=concept,
                limit=limit,
            )
            records = await result.data()
            return [r["related"] for r in records]

    async def add_concept(self, concept: str, domain: str, keywords: List[str] = None):
        """Add a concept node."""
        if not self._driver:
            return
        async with self._driver.session() as session:
            await session.run(
                "MERGE (c:Concept {name: $name}) "
                "SET c.domain = $domain, c.keywords = $keywords",
                name=concept,
                domain=domain,
                keywords=keywords or [],
            )
