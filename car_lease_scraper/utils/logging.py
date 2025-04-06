"""
Logging Utilities

Provides consistent logging setup across the application.
"""

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from car_lease_scraper.config import SETTINGS


# Global console instance
console = Console()


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name (str): Logger name
        level (str, optional): Log level (DEBUG, INFO, etc.)
        
    Returns:
        logging.Logger: Configured logger
    """
    log_level = level or SETTINGS.log_level
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Check if logger already has handlers to avoid duplicate
    if not logger.handlers:
        # Create rich handler for nice console output
        handler = RichHandler(
            rich_tracebacks=True,
            console=console,
            show_time=True,
            show_path=False
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        
        # Propagate to root logger
        logger.propagate = False
    
    return logger


def setup_root_logger():
    """Set up the root logger."""
    logging.basicConfig(
        level=getattr(logging, SETTINGS.log_level),
        format="%(message)s",
        datefmt="[%Y-%m-%d %H:%M:%S]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                console=console,
                show_time=True,
                show_path=False
            )
        ]
    )