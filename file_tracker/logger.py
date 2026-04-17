"""Logging setup — console + rotating file output with programmatic reader."""

import logging
import os
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler

_LOGGER_NAME = "file_tracker"
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s.%(module)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3
_configured = False

def setup_logging(config: dict) -> logging.Logger:
    """Configure logging to console and rotating file. Safe to call multiple times."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)

    if _configured:
        return logger

    level = getattr(logging, config.get("log_level", "INFO"), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler — rotating
    logs_dir = config.get("logs_dir", "./data/logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "file_tracker.log")

    file_handler = RotatingFileHandler(
        log_file, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured = True
    return logger

def get_logger() -> logging.Logger:
    """Get the package logger (must call setup_logging first)."""
    return logging.getLogger(_LOGGER_NAME)

_LOG_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*(\w+)\s*\|\s*([\w.]+)\s*\|\s*(.*)$"
)

def get_logs(config_path: str, level: str | None = None, last_n: int = 50) -> list[dict]:
    """Read parsed log entries from the log file.

    Args:
        config_path: Path to config.yaml (used to locate the log file).
        level: Filter by level — None (all), "WARNING", "ERROR", etc.
        last_n: Return the last N matching entries (default 50).

    Returns:
        List of dicts with keys: timestamp, level, module, message.
    """
    from file_tracker.config import load_config

    config = load_config(config_path)
    log_file = os.path.join(config["logs_dir"], "file_tracker.log")

    if not os.path.isfile(log_file):
        return []

    entries: list[dict] = []
    level_filter = level.upper() if level else None

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            match = _LOG_LINE_RE.match(line.strip())
            if not match:
                continue
            entry_level = match.group(2).strip()
            if level_filter and entry_level != level_filter:
                continue
            entries.append({
                "timestamp": match.group(1),
                "level": entry_level,
                "module": match.group(3).strip(),
                "message": match.group(4).strip(),
            })

    return entries[-last_n:] if last_n else entries
