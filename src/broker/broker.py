from collections import deque
from itertools import count
from time import sleep
from uuid import uuid4
from typing import Callable, Dict, Any
from tqdm import tqdm

from ..core.logger_setup import setup_logger

logger = setup_logger("broker")

# simple in-memory queues
_request_queue: deque[Dict[str, Any]] = deque()
_responses: Dict[str, Dict[str, Any]] = {}


def publish(request_payload: Dict[str, Any]) -> str:
    """Push a request into the queue."""
    request_id = str(request_payload.get("id") or uuid4())
    _request_queue.append({"id": request_id, "payload": request_payload})
    logger.info(f"🚀✅ Mensagem publicada {request_id}")
    return request_id


def get_response(request_id: str) -> Dict[str, Any] | None:
    return _responses.pop(request_id, None)


def consume(callback: Callable[[Dict[str, Any]], Dict[str, Any]]):
    """Consume requests and invoke callback for each."""
    logger.info("🚀 Iniciando consumidor")
    progress = tqdm(desc="🔄 Consumindo requests", unit="req")
    while True:
        if _request_queue:
            request = _request_queue.popleft()
            try:
                response = callback(request)
                _responses[request["id"]] = response
                progress.update(1)
            except Exception as exc:
                logger.error(f"❌ Erro ao consumir: {exc}")
        else:
            sleep(0.1)