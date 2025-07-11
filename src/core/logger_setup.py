import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class JsonEmojiFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - simple
        log_record = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(log_record, ensure_ascii=False)


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    logs_dir.mkdir(exist_ok=True)

    handler = RotatingFileHandler(
        logs_dir / f"{name}.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(JsonEmojiFormatter())

    stream = logging.StreamHandler()
    stream.setFormatter(JsonEmojiFormatter())

    logger.addHandler(handler)
    logger.addHandler(stream)
    logger.setLevel(logging.INFO)
    return logger