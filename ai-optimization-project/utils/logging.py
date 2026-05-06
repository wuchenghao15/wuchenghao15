#!/usr/bin/env python3
"""
日志工具模块

import os
import logging
from config.config import config

class Logger:
    """日志类"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化日志配置"""
        # 创建日志目录
        log_dir = os.path.dirname(config.LOGGING_CONFIG['file'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 配置日志
        logging.basicConfig(
            level=getattr(logging, config.LOGGING_CONFIG['level']),
            format=config.LOGGING_CONFIG['format'],
            handlers=[
                logging.FileHandler(config.LOGGING_CONFIG['file']),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger('AI_Optimization')
        self.logger.info("日志系统初始化成功")

    def get_logger(self):
        """获取日志对象

        Returns:
            logging.Logger: 日志对象
        return self.logger

# 创建日志实例
logger = Logger().get_logger()
