from __future__ import annotations
from typing import List
import logging, tiktoken

from langchain_core.messages import BaseMessage, AIMessage
from langchain_openai import ChatOpenAI

from .config import load_default_config   # ← usa o mesmo loader

cfg = load_default_config()

ENC = tiktoken.encoding_for_model(cfg.get("model", "gpt-4o-mini"))
MAX_CTX   = cfg.get("max_context_tokens", 4096)
KEEP_TAIL = cfg.get("keep_tail_msgs", 6)

_SUMMARIZER = ChatOpenAI(
    model      = cfg.get("summarizer_model", "gpt-4o-mini"),
    temperature= 0,
    max_tokens = 256,
)

from .logger_setup import setup_logger
logger = setup_logger("context_utils")

def _count(text: str) -> int: return len(ENC.encode(text))
def _total(msgs: List[BaseMessage]) -> int: return sum(_count(m.content) for m in msgs)

def _summarize(text: str) -> str:
    prompt = (
        "Resuma em até 3 frases, mantendo nomes, apelidos e decisões do usuário.\n\n"
        f"### Texto\n{text}"
    )
    return _SUMMARIZER.invoke(prompt).content.strip()

def reduce_messages(msgs: List[BaseMessage]) -> List[BaseMessage]:
    total = _total(msgs)
    logger.info(f"🧮 context_tokens={total}")
    if total <= MAX_CTX:
        return msgs

    head, tail = msgs[:-KEEP_TAIL], msgs[-KEEP_TAIL:]
    summary = _summarize("\n".join(m.content for m in head))
    logger.info(f"✂️ Resumindo {len(head)} mensagens antigas → 1 resumo")

    tail.insert(0, AIMessage(content=f"📜 Resumo até aqui: {summary}"))
    logger.info(f"🧮 novo_context_tokens={_total(tail)}")
    return tail
