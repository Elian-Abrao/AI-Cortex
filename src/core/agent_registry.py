import asyncio
from typing import Dict

from .agent import create_agent, AgentService

_AGENT_CACHE: Dict[str, AgentService] = {}
_LOCK = asyncio.Lock()          # evita corrida em ambientes async

async def get_agent(thread_id: str, **kwargs) -> AgentService:
    """Retorna um AgentService em cache ou cria um novo."""
    async with _LOCK:
        if thread_id in _AGENT_CACHE:
            return _AGENT_CACHE[thread_id]

        service = await create_agent(thread_id=thread_id, **kwargs)
        _AGENT_CACHE[thread_id] = service
        return service