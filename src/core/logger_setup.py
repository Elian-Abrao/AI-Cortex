# ─── src/core/logger_setup.py ───
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class JsonEmojiFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:          # pragma: no cover
        log_record = {
            "time":   self.formatTime(record),
            "level":  record.levelname,
            "name":   record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_record, ensure_ascii=False)


def _make_handler(logs_dir: Path, name: str) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        logs_dir / f"{name}.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(JsonEmojiFormatter())
    return handler


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Cria (ou recupera) um logger com formatação JSON‑emoji.
    `level` defaulta para INFO, exceto para o namespace "context"
    que já vem em DEBUG para mostrar contagem de tokens/resumos.
    """
    logger = logging.getLogger(name)
    if logger.handlers:      # já configurado → só ajusta nível se pedido
        if level is not None:
            logger.setLevel(level)
        return logger

    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    logs_dir.mkdir(exist_ok=True)

    file_handler   = _make_handler(logs_dir, name)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JsonEmojiFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Define nível: param > regra "context" > INFO padrão
    if level is not None:
        logger.setLevel(level)
    elif name == "context":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.propagate = False      # evita log duplicado no root
    return logger
