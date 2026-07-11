"""统一日志系统 - MTSCOS AI项目"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


class Logger:
    """统一日志管理器"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._loggers = {}
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """配置根日志器"""
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        log_dir = os.environ.get('LOG_DIR', 'logs')
        
        os.makedirs(log_dir, exist_ok=True)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'mtscos.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, 'mtscos_error.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取日志器"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name or __name__)
        return self._loggers[name]


def get_logger(name: str = None) -> logging.Logger:
    """获取日志器（便捷函数）"""
    return Logger().get_logger(name)


def log_decorator(logger_name: str = None):
    """日志装饰器"""
    def decorator(func):
        logger = get_logger(logger_name or func.__module__)
        
        def wrapper(*args, **kwargs):
            logger.info(f"开始执行: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"执行完成: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"执行失败: {func.__name__} - {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator