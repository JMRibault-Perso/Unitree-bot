"""Logging Configuration"""

import logging
import sys
import platform
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger
    
    Args:
        name: Logger name (None for root logger)
        level: Logging level
        log_file: Optional file to log to
        format_string: Custom format string
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Default format
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    formatter = logging.Formatter(format_string)
    
    # Console handler with UTF-8 encoding for Windows
    if platform.system() == 'Windows':
        # Use UTF-8 encoding on Windows, with error handling to avoid crashes
        console_handler = logging.StreamHandler(
            stream=sys.stdout
        )
        # Reconfigure stdout to use UTF-8 with error replacement
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    else:
        console_handler = logging.StreamHandler(sys.stdout)
    
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def setup_app_logging(verbose: bool = False):
    """
    Setup logging for entire application
    
    Args:
        verbose: Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Setup root logger
    setup_logger(
        name='g1_app',
        level=level,
        format_string='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    # Silence noisy third-party loggers
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    
    logging.info(f"Logging configured (level: {logging.getLevelName(level)})")
