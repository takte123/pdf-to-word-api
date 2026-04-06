"""
Logging configuration
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure application logging"""
    settings = get_settings()

    # Create logs directory
    logs_dir = Path(settings.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Configure logger
    logger = logging.getLogger("pdf_converter")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()
