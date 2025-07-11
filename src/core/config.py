import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

import logging
logger = logging.getLogger("core_agent")

class ConfigError(Exception):
    """Raised when configuration loading fails."""

    pass


def load_env(env_file: str | None = None) -> None:
    """Load environment variables from .env."""

    load_dotenv(env_file)


def load_mcp_config(path: str | os.PathLike = "config/mcp_config.json") -> Dict[str, Any]:
    """Load MCP server configuration and inject env vars."""
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"🗂️ Arquivo de configuração não encontrado: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_cfg = json.load(f)
    except Exception as exc:
        raise ConfigError(f"❌ Falha ao ler {config_path}: {exc}") from exc

    servers: Dict[str, Any] = {}
    for name, cfg in raw_cfg.items():
        if not all(k in cfg for k in ("command", "args", "transport")):
            raise ConfigError(f"❌ Configuração inválida para {name}")
        srv = {
            "command": cfg["command"],
            "args": cfg["args"],
            "transport": cfg["transport"],
        }
        if "env_vars" in cfg:
            srv["env"] = {var: os.getenv(var) for var in cfg["env_vars"]}
        servers[name] = srv

        # 🚀 Log do comando a ser executado
        cmd_preview = f"{srv['command']} {' '.join(srv['args'])}"
        logger.info(f"📦 MCP '{name}' será iniciado com: `{cmd_preview}`")

    return servers


def load_default_config(path: str | os.PathLike = "config/default.yaml") -> Dict[str, Any]:
    """Load default agent configuration."""
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise ConfigError(f"Arquivo de configuração não encontrado: {cfg_path}")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover - sanity
        raise ConfigError(f"Falha ao ler {cfg_path}: {exc}") from exc
    return cfg
