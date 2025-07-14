import asyncio
import threading
from time import sleep
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.agent import (
    create_agent,
    AgentService,
    handle_request,
    init_mcp_tools,
    _mcp_tools,
    _mcp_client,
)
from src.broker.broker import publish, get_response, consume


class DummyLLM:
    async def ainvoke(self, state: dict, config):
        msg = state.get("messages", [])
        if msg:
            last = msg[-1]
            content = getattr(last, "content", str(last))
        else:
            content = ""
        return f"echo:{content}"


@pytest.mark.asyncio
async def test_create_agent(monkeypatch, tmp_path):
    async def dummy_init():
        class Tool:
            name = "dummy"

        return [Tool()]

    monkeypatch.setattr('src.core.agent.init_mcp_tools', dummy_init)
    monkeypatch.setattr('src.core.agent.ChatOpenAI', lambda **kwargs: DummyLLM())
    monkeypatch.setattr('src.core.agent.create_react_agent', lambda model, tools, prompt, checkpointer: DummyLLM())
    monkeypatch.setattr('src.core.agent._mcp_tools', None, raising=False)
    monkeypatch.setattr('src.core.agent._mcp_client', None, raising=False)

    agent = await create_agent(thread_id="t1", checkpoint_path=tmp_path)
    assert isinstance(agent, AgentService)
    resp = await agent.run('hi')
    assert resp == 'echo:hi'


@pytest.mark.asyncio
async def test_memory_persistence(monkeypatch, tmp_path):
    async def dummy_init():
        class Tool:
            name = "dummy"

        return [Tool()]

    monkeypatch.setattr('src.core.agent.init_mcp_tools', dummy_init)
    monkeypatch.setattr('src.core.agent.ChatOpenAI', lambda **kwargs: DummyLLM())
    monkeypatch.setattr('src.core.agent.create_react_agent', lambda model, tools, prompt, checkpointer: DummyLLM())
    monkeypatch.setattr('src.core.agent._mcp_tools', None, raising=False)
    monkeypatch.setattr('src.core.agent._mcp_client', None, raising=False)

    tid = "memtest"
    agent = await create_agent(thread_id=tid, checkpoint_path=tmp_path)
    agent.memory.saver.storage[tid] = {"msg": "hi"}
    agent.memory.save(tid)
    path = agent.memory.snapshot_path(tid)
    assert path.exists()

    agent2 = await create_agent(thread_id=tid, checkpoint_path=tmp_path)
    assert tid in agent2.memory.saver.storage


def test_broker_integration(monkeypatch):
    async def dummy_init():
        class Tool:
            name = "dummy"

        return [Tool()]

    monkeypatch.setattr('src.core.agent.init_mcp_tools', dummy_init)
    monkeypatch.setattr('src.core.agent.ChatOpenAI', lambda **kwargs: DummyLLM())
    monkeypatch.setattr('src.core.agent.create_react_agent', lambda model, tools, prompt, checkpointer: DummyLLM())
    monkeypatch.setattr('src.core.agent._mcp_tools', None, raising=False)
    monkeypatch.setattr('src.core.agent._mcp_client', None, raising=False)

    def run_consumer():
        consume(lambda msg: asyncio.run(handle_request(msg)))

    t = threading.Thread(target=run_consumer, daemon=True)
    t.start()

    request_id = publish({"prompt": "oi", "claims": {"thread_id": "broker"}})
    for _ in range(20):
        resp = get_response(request_id)
        if resp:
            assert resp["response"] == "echo:oi"
            break
        sleep(0.1)
    else:
        raise AssertionError('no response')