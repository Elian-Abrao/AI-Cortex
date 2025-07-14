from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import uuid4
import jwt
from fastapi import HTTPException
from pydantic import BaseModel

from ..core.logger_setup import setup_logger
from ..core.config import load_default_config

cfg = load_default_config()
SECRET_KEY = cfg.get("secret_key", "secret")
ALGORITHM = cfg.get("algorithm", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = cfg.get("access_token_expire_minutes", 60)

logger = setup_logger("auth")

# Usuários de exemplo, a ideia eh conectar com um banco para registrar corretamente os valores.
USER_DB = cfg.get(
    "user_db",
    {
        "elian": {
            "password": "teste123",
            "default_temperature": 0.7,
            "allowed_tools": [],
        },
        "Matti": {
            "password": "Agromatic@2026@dev",
            "default_temperature": 0.0,
            "allowed_tools": ["DeepResearchMCP"],
        },
    },
)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    user = USER_DB.get(username)
    if user and user["password"] == password:
        logger.info(f"✅ Usuário autenticado [USUÁRIO] = {username} | [PERMISSÕES] = {user}")
        return user
    logger.warning("❌ Falha na autenticação")
    raise HTTPException(status_code=401, detail="Invalid credentials")


def create_token(username: str, user_data: Dict[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    thread_id = str(uuid4())
    payload = {
        "sub": username,
        "exp": expire,
        "thread_id": thread_id,
        "default_temperature": user_data["default_temperature"],
        "allowed_tools": user_data["allowed_tools"],
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"🔐 Token gerado com thread {thread_id} [USUARIO] = {username}")
    logger.info(f"🎲 Dados de config [USUARIO] {username} -> {payload}")
    return token


def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"🔑 Token válido [{payload}]")
        return payload
    except Exception as e:
        logger.error(f"❌ Erro ao validar token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")