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
            "allowed_tools": ["calculate", "converter_moedas", "converter_medidas", 'obter_cotacao'],
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


def create_token(username: str, user_data: Dict[str, Any], thread_id: str | None = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    tid = thread_id or str(uuid4())
    payload = {
        "sub": username,
        "exp": expire,
        "thread_id": tid,
        "default_temperature": user_data["default_temperature"],
        "allowed_tools": user_data["allowed_tools"],
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"🔐 Token gerado com thread {tid}")
    return token


def refresh_token(old_token: str) -> str:
    try:
        payload = jwt.decode(
            old_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False}
        )
    except Exception as exc:
        logger.error(f"❌ Erro ao decodificar token expirado: {exc}")
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("sub")
    if not username or username not in USER_DB:
        logger.warning("❌ Usuário desconhecido no refresh")
        raise HTTPException(status_code=401, detail="Invalid token")

    user_data = USER_DB[username]
    thread_id = payload.get("thread_id")
    return create_token(username, user_data, thread_id=thread_id)


def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"🔑 Token válido [{payload}]")
        return payload
    except Exception as e:
        logger.error(f"❌ Erro ao validar token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")