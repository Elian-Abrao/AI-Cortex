from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..auth.auth import authenticate_user, create_token, verify_token, Token
import asyncio
import threading

from ..broker import publish, get_response
from ..core.core_agent import start_consumer
from ..core.logger_setup import setup_logger

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
    return Token(access_token=token)


@app.post("/agent/query")
async def agent_query(request: Request, body: QueryRequest):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("❌ Token ausente")
        raise HTTPException(status_code=401, detail="Token required")

    token = auth_header.split(" ")[1]
    claims = verify_token(token)
    message = {
        "prompt": body.prompt,
        "claims": claims,
    }
    request_id = publish(message)

    for _ in range(100):
        await asyncio.sleep(0.1)
        response = get_response(request_id)
        if response:
            logger.info("✅ Consulta processada")
            return response

    raise HTTPException(status_code=504, detail="Timeout waiting for agent")