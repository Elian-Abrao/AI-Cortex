import asyncio
from src.core.config import load_default_config

from src.core import create_agent
from src.core.logger_setup import setup_logger
from langchain_core.messages.ai import AIMessage


async def interactive_console() -> None:
    logger = setup_logger("console")
    load_default_config()  # ensure file exists
    service = await create_agent()

    while True:
        try:
            user_input = input("\n📝 Pergunta: ")
            logger.debug(f"👤 Mensagem do Usuario: {user_input}")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        response = await service.run(user_input)
        if isinstance(response, AIMessage):
            conteudo = response.content
        else:
            conteudo = response["messages"][-1].content
        logger.info(f"🤖 Resposta: {conteudo}")


if __name__ == "__main__":
    asyncio.run(interactive_console())
