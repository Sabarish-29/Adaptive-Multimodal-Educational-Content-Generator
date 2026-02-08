"""Agent communication utilities – HTTP and Kafka helpers."""

from typing import Dict, Any, Optional
import asyncio


class AgentCommunicator:
    """
    Unified communication layer for agent-to-agent calls.
    Supports HTTP (sync) and Kafka (async event) patterns.
    """

    def __init__(self, agent_registry: Optional[Dict[str, str]] = None):
        self._registry = agent_registry or {}
        self._http_client = None

    async def _get_client(self):
        if self._http_client is None:
            try:
                import httpx
                self._http_client = httpx.AsyncClient(timeout=30.0)
            except ImportError:
                pass
        return self._http_client

    async def call(
        self, agent_name: str, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call another agent via HTTP."""
        base_url = self._registry.get(agent_name)
        if not base_url:
            return {"error": f"Agent {agent_name} not registered"}

        client = await self._get_client()
        if client is None:
            return {"error": "httpx not available"}

        url = f"{base_url.rstrip('/')}{endpoint}"
        try:
            resp = await client.post(url, json=data, timeout=15.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    async def emit_event(self, topic: str, event: Dict[str, Any]):
        """Emit a Kafka event (placeholder)."""
        # TODO: integrate with aiokafka
        pass

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()
