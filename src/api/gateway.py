from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..auth.auth import authenticate_user, create_token, verify_token, refresh_token, Token
import asyncio
import threading

from ..broker import publish, get_response
from ..core.core_agent import start_consumer
from ..core.logger_setup import setup_logger
from ..core.agent import init_mcp_tools
from ..core.agent_registry import get_agent

logger = setup_logger("gateway")
app = FastAPI(title="AI Agent Gateway")

threading.Thread(target=start_consumer, daemon=True).start()


@app.get("/health")
async def health() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


class QueryRequest(BaseModel):
    prompt: str


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    token = create_token(form_data.username, user)
    await init_mcp_tools()
    return Token(access_token=token)


@app.post("/refresh", response_model=Token)
async def refresh(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("❌ Token ausente para refresh")
        raise HTTPException(status_code=401, detail="Token required")
    old_token = auth_header.split(" ")[1]
    new_token = refresh_token(old_token)
    return Token(access_token=new_token)


# agent_query agora chama diretamente o agente em cache
@app.post("/agent/query")
async def agent_query(request: Request, body: QueryRequest):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("❌ Token ausente")
        raise HTTPException(status_code=401, detail="Token required")

    token   = auth_header.split(" ")[1]
    claims  = verify_token(token)

    # 🚀 Recupera ou cria o AgentService em cache para este thread_id
    service = await get_agent(
        thread_id     = claims.get("thread_id"),
        temperature   = claims.get("default_temperature"),
        allowed_tools = claims.get("allowed_tools"),
    )

    try:
        response_text = await service.run(body.prompt)
    except Exception as exc:
        logger.exception(f"❌ Erro ao processar consulta: {exc}")
        raise HTTPException(status_code=500, detail="Erro interno")

    return {"response": response_text}