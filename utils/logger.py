"""Logger setup for DYChatBot.

This module provides logging configuration with console and file output.
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logger(name: str, level: str, log_dir: str) -> logging.Logger:
    """Set up a logger with console and file handlers.

    Args:
        name: Logger name.
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        log_dir: Directory for log files.

    Returns:
        Configured logger instance.
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler (StreamHandler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (TimedRotatingFileHandler - rotate daily)
    log_file = log_path / f"{name}.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
