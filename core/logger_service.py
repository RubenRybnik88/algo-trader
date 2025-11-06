"""
logger_service.py
-----------------
Centralised logging utility for the Algo-Trader project.

Use:
    from core.logger_service import get_logger
    logger = get_logger("fetch_market_data")

This returns a script-local logger that writes to its own file in /logs,
mirrors to console, and does NOT propagate to ibkr_service or root loggers.
"""

import logging
import os
from datetime import datetime

LOG_ROOT = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_ROOT, exist_ok=True)


def get_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Returns a dedicated logger with its own file + console output.
    - Logs are stored in /logs/<name>.log
    - No propagation to root/ibkr_service
    - Each logger is initialised once
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # If already configured, return it
    if logger.handlers:
        return logger

    # File + console handlers
    log_file = os.path.join(LOG_ROOT, f"{name}.log")

    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(fmt)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent duplication in ibkr_service / root
    logger.propagate = False

    logger.info(f"Logger initialised for '{name}' → {log_file}")
    return logger
