# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块
"""

import logging
import os
from datetime import datetime

# 创建日志目录
log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

# 创建日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)

# 创建全局logger实例
logger = logging.getLogger('mtscos')
logger.setLevel(logging.INFO)

# 创建模块级别的logger
def get_logger(name: str):
    """获取指定名称的logger"""
    return logging.getLogger(name)

class LoggingManager:
    def __init__(self):
        self.log_counts = {}
        self.error_counts = {}
    
    def get_log_stats(self):
        return {
            'total_logs': sum(self.log_counts.values()),
            'error_count': sum(self.error_counts.values()),
            'log_counts': self.log_counts
        }
    
    def increment_log_count(self, level):
        self.log_counts[level] = self.log_counts.get(level, 0) + 1
    
    def increment_error_count(self, error_type):
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

logging_manager = LoggingManager()

__all__ = ['logger', 'get_logger', 'logging_manager']
