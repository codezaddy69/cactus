"""Logging configuration for Cactus Trading Bot."""

import sys
from loguru import logger
from config.settings import settings


def setup_logging() -> None:
    """Configure application logging with Loguru."""
    # Remove default handler
    logger.remove()

    # Console logging
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # File logging - all logs
    logger.add(
        "logs/cactus.log",
        level="DEBUG",
        rotation="500 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    # File logging - errors only
    logger.add(
        "logs/errors.log",
        level="ERROR",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    logger.info(f"Logging configured - Level: {settings.log_level}")


# Initialize logging on import
setup_logging()
