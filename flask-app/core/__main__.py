#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI Project - Core Module
"""

from .config import config
from .database import db
from .logging import logger
from .system import system
from .ai import ai_service
from .utils import FileUtils, StringUtils, TimeUtils, ValidationUtils, DataUtils
from .exceptions import (
    MTSCOSError, DatabaseError, ConfigurationError, APIError,
    ValidationError, AuthenticationError, AuthorizationError,
    ResourceNotFoundError, RateLimitError, AIError, FileError
)

__all__ = [
    'config',
    'db',
    'logger',
    'system',
    'ai_service',
    'FileUtils',
    'StringUtils',
    'TimeUtils',
    'ValidationUtils',
    'DataUtils',
    'MTSCOSError',
    'DatabaseError',
    'ConfigurationError',
    'APIError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'ResourceNotFoundError',
    'RateLimitError',
    'AIError',
    'FileError'
]

def init():
    """Initialize core module"""
    logger.info("Initializing MTSCOS Core Module")
    
    try:
        db.execute("SELECT 1")
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    logger.info("Core module initialized successfully")

if __name__ == "__main__":
    init()
    print("MTSCOS Core Module initialized successfully!")
