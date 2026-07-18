import logging
import os
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            base["exception"] = self.formatException(record.exc_info)
        return json.dumps(base)


def configure_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    env = os.getenv("ENVIRONMENT", "development")
    logging.getLogger().setLevel(getattr(logging, level, logging.INFO))
    for name in ["uvicorn", "uvicorn.error", "gunicorn", "gunicorn.error"]:
        logging.getLogger(name).setLevel(getattr(logging, level, logging.INFO))
    if env == "production":
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
    else:
        logging.basicConfig(
            level=getattr(logging, level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,
        )
