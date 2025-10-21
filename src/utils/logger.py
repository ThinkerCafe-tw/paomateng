"""
Logging configuration for Railway News Monitor
"""

from loguru import logger
import sys


def setup_logging(config: dict) -> None:
    """
    Setup logging with configuration from settings

    Args:
        config: Configuration dictionary from settings.yaml
    """
    # Remove default handler
    logger.remove()

    # Get logging config
    log_config = config.get("logging", {})
    level = log_config.get("level", "INFO")
    log_file = log_config.get("log_file", "logs/railway_monitor.log")
    rotation = log_config.get("rotation", "10 MB")

    # Add console handler
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Add file handler with rotation
    logger.add(
        log_file,
        level=level,
        rotation=rotation,
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info(f"Logging initialized: Level={level}, File={log_file}")
