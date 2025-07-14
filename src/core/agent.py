"""Core agent service and request processing."""

from __future__ import annotations

import asyncio
import os
import traceback 
from typing import Any, Dict, Optional, List

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
from .context_utils import reduce_messages

logger = setup_logger("core_agent")

_mcp_client: MultiServerMCPClient | None = None
_mcp_tools: list[Any] | None = None


async def init_mcp_tools() -> list[Any]:
    """Initialize MCP clients and cache the tools."""
    global _mcp_client, _mcp_tools
    if _mcp_tools is not None:
        return _mcp_tools

    load_env()
    try:
        servers = load_mcp_config()
    except ConfigError as exc:
        logger.error(f"❌ {exc}")
        raise

    _mcp_client = MultiServerMCPClient(servers)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            _mcp_tools = await _mcp_client.get_tools()
            break
        except* Exception as group_exc:
            for err in group_exc.exceptions:
                logger.error(
                    f"💥 Erro interno no MCP: {type(err).__name__}: {err}",
                    exc_info=True,
                )
            logger.warning(
                f"❌ Erro ao conectar MCPs: tentativa {attempt + 1}/{max_retries} 🔁"
            )
            await asyncio.sleep(2 ** attempt)

    if _mcp_tools is None:
        raise RuntimeError("❌ Falha ao conectar aos MCPs 🚫")

    logger.info(f"🧠 Ferramentas carregadas: {[t.name for t in _mcp_tools]}")
    return _mcp_tools

class AgentService:
    """Wrapper em torno do agente LangGraph com memória persistente."""

    def __init__(self, agent: Any, config: Dict[str, Any], memory: MemoryManager):
        self.agent = agent           # executor LangGraph
        self.config = config         # {"configurable": {"thread_id": ...}}
        self.memory = memory         # gerencia checkpoints .pkl

    async def run(self, user_input: str) -> str:
        thread_id = self.config["configurable"]["thread_id"]
        logger.info(f"🚀 run() – thread_id={thread_id}")

        # 1️⃣ Chamada segura ao agente (enviamos só o novo HumanMessage)
        try:
            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                self.config,
            )
        except Exception:
            logger.error(f"🔥 Falha dentro de ainvoke:\n{traceback.format_exc()}")
            raise

        # 2️⃣ Extrai diálogo completo (histórico + resposta)
        msgs = result if isinstance(result, list) else result["messages"]
        answer = msgs[-1].content
        logger.info(f"🗣️ Resposta extraída: {answer!r}")

        # 3️⃣ → APLICA RESUMO e mede tokens
        msgs_reduced = reduce_messages(msgs)          # 🔹 aqui
        logger.debug(f"📦 Mensagens após reduce: {len(msgs_reduced)}")

        # 4️⃣ Atualiza saver e grava pkl
        # self.memory.saver.storage[thread_id] = msgs_reduced
        self.memory.save(thread_id)

        return answer


async def create_agent(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None,
    thread_id: Optional[str] = None,
    checkpoint_path: Optional[str] = None,
    allowed_tools: Optional[list[str]] = None,
) -> AgentService:
    """Create the agent with optional overrides."""

    load_env()
    defaults = load_default_config()

    logger.info("🔧 Carregando configuração padrão")

    tools = await init_mcp_tools()
    if allowed_tools:
        tools = [t for t in tools if getattr(t, "name", None) in allowed_tools]
    logger.info(f"🛠️ Ferramentas permitidas: {allowed_tools}")

    llm = ChatOpenAI(
        model=model or defaults.get("model"),
        temperature=float(
            temperature if temperature is not None else defaults.get("temperature", 0)
        ),
        max_tokens=max_tokens or defaults.get("max_tokens"),
    )

    memory = MemoryManager(checkpoint_path or defaults.get("checkpoint_path", "checkpoints"))
    tid = thread_id or defaults.get("thread_id", "sessao_elian")
    memory.load(tid)

    prompt = system_prompt or defaults.get(
        "system_prompt",
        "Você é um assistente que pode usar ferramentas via MCP para ajudar o usuário.",
    )

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=prompt,
        checkpointer=memory.saver,
    )

    config = {"configurable": {"thread_id": tid}}

    logger.info("✅ Agente criado com sucesso! 🤖")
    return AgentService(agent, config, memory)


async def handle_request(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process a broker message using a newly created agent."""
    logger.info(f"Mensagem recebida: {message}")
    request_id = message.get("id")
    payload = message.get("payload", {})
    prompt = payload.get("prompt", "")
    claims = payload.get("claims", {})

    defaults = load_default_config()

    service = await create_agent(
        temperature=claims.get("default_temperature"),
        thread_id=claims.get("thread_id"),
        allowed_tools=claims.get("allowed_tools"),

    )
    try:
        response = await service.run(prompt)
    except Exception as exc:  # pragma: no cover - network
        logger.error(f"❌ Erro ao processar: {exc}")
        error_message = defaults.get("error_message", "Erro")
        return {"id": request_id, "response": error_message, "tools_used": []}

    return {"id": request_id, "response": response, "tools_used": []}