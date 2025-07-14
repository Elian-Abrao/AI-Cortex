from typing import Dict, Any

import asyncio

from .agent import handle_request
from ..broker import consume
from .logger_setup import setup_logger

logger = setup_logger("core_agent")


def start_consumer():
    def _callback(request: Dict[str, Any]) -> Dict[str, Any]:
        response = asyncio.run(handle_request(request))
        logger.info(f"✅📝 Resposta gerada para {request['id']} [RESPOSTA] = [{response}]")
        return response

    consume(_callback)


if __name__ == "__main__":
    start_consumer()