import asyncio
import threading
from time import sleep
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.agent import create_agent, AgentService, handle_request
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


class DummyClient:
    async def get_tools(self):
        class Tool:
            name = "dummy"
        return [Tool()]


@pytest.mark.asyncio
async def test_create_agent(monkeypatch):
    monkeypatch.setattr('src.core.agent.MultiServerMCPClient', lambda servers: DummyClient())
    monkeypatch.setattr('src.core.agent.ChatOpenAI', lambda **kwargs: DummyLLM())
    monkeypatch.setattr('src.core.agent.create_react_agent', lambda model, tools, prompt, checkpointer: DummyLLM())

    agent = await create_agent()
    assert isinstance(agent, AgentService)
    resp = await agent.run('hi')
    assert resp == 'echo:hi'


def test_broker_integration(monkeypatch):
    monkeypatch.setattr('src.core.agent.MultiServerMCPClient', lambda servers: DummyClient())
    monkeypatch.setattr('src.core.agent.ChatOpenAI', lambda **kwargs: DummyLLM())
    monkeypatch.setattr('src.core.agent.create_react_agent', lambda model, tools, prompt, checkpointer: DummyLLM())

    def run_consumer():
        consume(lambda msg: asyncio.run(handle_request(msg)))

    t = threading.Thread(target=run_consumer, daemon=True)
    t.start()

    request_id = publish({"prompt": "oi", "claims": {}})
    for _ in range(20):
        resp = get_response(request_id)
        if resp:
            assert resp["response"] == "echo:oi"
            break
        sleep(0.1)
    else:
        raise AssertionError('no response')
