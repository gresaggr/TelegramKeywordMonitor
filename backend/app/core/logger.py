import logging
import sys
from pathlib import Path
from app.core.config import settings

Path("logs").mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

file_handler = logging.FileHandler("logs/app.log", encoding='utf-8')
file_handler.setFormatter(formatter)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger("telegram_monitor")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f"telegram_monitor.{name}")