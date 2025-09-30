"""
Logging configuration
"""
import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger
from config import settings


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Setup structured logging"""
    logger = logging.getLogger(name or __name__)
    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    if logger.hasHandlers():
        return logger
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    if settings.ENVIRONMENT == "production":
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)