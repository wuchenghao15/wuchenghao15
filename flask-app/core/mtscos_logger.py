# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced logging system module
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional
from .config import config

class Logger:
    """Advanced logging system with multiple handlers"""
    
    def __init__(self, name: str = "MTSCOS", log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        if log_file is None:
            log_file = config.get("logging.file_path", "logs/system.log")
        
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        self._setup_handlers(log_file)
    
    def _setup_handlers(self, log_file: str):
        """Setup logging handlers"""
        # Remove existing handlers to avoid duplication
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler with rotation
        max_size = config.get("logging.max_file_size_mb", 50) * 1024 * 1024
        backup_count = config.get("logging.backup_count", 5)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", exc_info=True, extra=kwargs)
        else:
            self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        if exception:
            self.logger.critical(f"{message}: {str(exception)}", exc_info=True, extra=kwargs)
        else:
            self.logger.critical(message, extra=kwargs)
    
    def log_exception(self, message: str, exception: Exception):
        """Log exception with traceback"""
        self.logger.error(message, exc_info=True)
    
    def log_task_start(self, task_name: str):
        """Log task start"""
        self.info(f"=== Starting task: {task_name} ===")
    
    def log_task_complete(self, task_name: str, duration: float = None):
        """Log task completion"""
        if duration:
            self.info(f"=== Task completed: {task_name} (Duration: {duration:.2f}s) ===")
        else:
            self.info(f"=== Task completed: {task_name} ===")

# Global logger instance
logger = Logger()
