# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import threading
from typing import Dict


class ContextFilter(logging.Filter):
    """
    日志上下文过滤器,用于添加额外的上下文信息
    def run_operation(**kwargs):
    """
    
    def __init__(self):
        super().__init__()
        self._context = threading.local()

    def set_context(self, **kwargs):
        """设置上下文信息"""
        for key, value in kwargs.items():
            setattr(self._context, key, value)

    def clear_context(self):
        """清除上下文信息"""
        self._context.__dict__.clear()

    def filter(self, record):
        """过滤日志记录,添加上下文信息"""
        for key, value in self._context.__dict__.items():
            setattr(record, key, value)

        if not hasattr(record, 'request_id'):
            record.request_id = getattr(self._context, 'request_id', 'N/A')
        if not hasattr(record, 'client_ip'):
            record.client_ip = getattr(self._context, 'client_ip', 'N/A')
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(self._context, 'user_id', 'N/A')

        return True


class LoggingManager:
    """日志管理器,用于统一管理日志系统"""

    def __init__(self):
        self._loggers = {}
        self._context_filter = ContextFilter()
        self._log_stats = {
            'debug': 0,
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        self._lock = threading.Lock()

    def configure_logging(self):
        """配置日志系统"""
        context_format = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter(context_format)

        console_format = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(self._context_filter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.handlers = []
        root_logger.addHandler(console_handler)

        main_logger = self.get_logger('MTSCOS_AI_Project')
        main_logger.info("日志系统配置完成")
        return main_logger

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.addFilter(self._context_filter)
            self._loggers[name] = logger

        return self._loggers[name]

    def set_module_log_level(self, module_name: str, level: int):
        """设置特定模块的日志级别"""
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        self.get_logger('MTSCOS_AI_Project').info(f"设置模块 {module_name} 的日志级别为 {logging.getLevelName(level)}")

    def set_global_log_level(self, level: int):
        """设置全局日志级别"""
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        self.get_logger('MTSCOS_AI_Project').info(f"设置全局日志级别为 {logging.getLevelName(level)}")

    def get_log_stats(self) -> Dict[str, int]:
        """获取日志统计信息"""
        with self._lock:
            return self._log_stats.copy()

    def increment_log_count(self, level: str):
        """增加日志计数"""
        level = level.lower()
        with self._lock:
            if level in self._log_stats:
                self._log_stats[level] += 1

    def get_context_filter(self) -> ContextFilter:
        """获取上下文过滤器"""
        return self._context_filter

    def set_context(self, **kwargs):
        """设置上下文信息"""
        self._context_filter.set_context(**kwargs)

    def clear_context(self):
        """清除上下文信息"""
        self._context_filter.clear_context()


logging_manager = LoggingManager()

logger = logging_manager.configure_logging()