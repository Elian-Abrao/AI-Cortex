"""Core agent service and request processing."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from .config import (
    load_env,
    load_mcp_config,
    load_default_config,
    ConfigError,
)
from .logger_setup import setup_logger
from .memory_manager import MemoryManager

logger = setup_logger("core_agent")


class AgentService:
    """Wrapper around a LangGraph agent with memory management."""

    def __init__(self, agent: Any, config: Dict[str, Any], memory: MemoryManager):
        self.agent = agent
        self.config = config
        self.memory = memory

    async def run(self, user_input: str) -> str:
        logger.info("🚀 Processando input")
        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=user_input)]}, self.config
        )
        logger.info("✅ Resposta gerada")
        thread_id = self.config["configurable"]["thread_id"]
        path = self.memory.save(thread_id)
        logger.info(f"📝 Memória salva em {path}")
        return result


async def create_agent(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None,
    thread_id: Optional[str] = None,
    checkpoint_path: Optional[str] = None,
) -> AgentService:
    """Create the agent with optional overrides."""

    load_env()
    defaults = load_default_config()

    logger.info("🔧 Carregando configuração padrão")

    try:
        servers = load_mcp_config()
    except ConfigError as exc:
        logger.error(f"❌ {exc}")
        raise

    client = MultiServerMCPClient(servers)

    max_retries = 3
    tools = None
    for attempt in range(max_retries):
        try:
            tools = await client.get_tools()
            break
        except Exception as exc:  # pragma: no cover - network
            logger.warning(f"❌ Erro ao conectar MCPs: {exc} - retry {attempt}")
            await asyncio.sleep(2 ** attempt)
    if tools is None:
        raise RuntimeError("Falha ao conectar aos MCPs")

    logger.info(f"🔍 Ferramentas carregadas: {[t.name for t in tools]}")

    llm = ChatOpenAI(
        model=model or defaults.get("model"),
        temperature=float(
            temperature if temperature is not None else defaults.get("temperature", 0)
        ),
        max_tokens=max_tokens or defaults.get("max_tokens"),
    )

    memory = MemoryManager(checkpoint_path or defaults.get("checkpoint_path", "checkpoints"))

    prompt = system_prompt or defaults.get(
        "system_prompt",
        "Você é um assistente que pode usar ferramentas via MCP para ajudar o usuário.",
    )

    agent = create_react_agent(model=llm, tools=tools, prompt=prompt, checkpointer=memory.saver)

    config = {"configurable": {"thread_id": thread_id or defaults.get("thread_id", "sessao_elian")}}

    logger.info("✅ Agente criado")
    return AgentService(agent, config, memory)


async def handle_request(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process a broker message using a newly created agent."""

    request_id = message.get("id")
    payload = message.get("payload", {})
    prompt = payload.get("prompt", "")
    claims = payload.get("claims", {})

    defaults = load_default_config()

    service = await create_agent(
        temperature=claims.get("default_temperature"),
    )
    try:
        response = await service.run(prompt)
    except Exception as exc:  # pragma: no cover - network
        logger.error(f"❌ Erro ao processar: {exc}")
        error_message = defaults.get("error_message", "Erro")
        return {"id": request_id, "response": error_message, "tools_used": []}

    return {"id": request_id, "response": response, "tools_used": []}

