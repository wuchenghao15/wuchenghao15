# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块,用于集中管理和分析系统日志
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LogManager:
    """日志管理模块"""

    def __init__(self):
        """初始化日志管理器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("日志管理器已初始化")

        self.config = {
            'log_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'),
            'log_file': 'system.log',
            'max_log_size': 10 * 1024 * 1024,
            'backup_count': 5,
            'log_level': logging.INFO,
            'analysis_interval': 3600
        }

        if not os.path.exists(self.config['log_dir']):
            os.makedirs(self.config['log_dir'])

        self.logs = []
        self.log_lock = threading.RLock()

        self.analysis_results = {
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'debug_count': 0,
            'error_types': {},
            'warning_types': {},
            'info_types': {},
            'debug_types': {},
            'time_distribution': {},
            'module_distribution': {},
            'trends': []
        }

        self.analysis_thread = None
        self.running = False

        self._setup_logging()

    def _setup_logging(self):
        """设置日志记录器"""
        log_file = os.path.join(self.config['log_dir'], self.config['log_file'])

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self.config['log_level'])

        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

        self.logger.info(f"日志配置完成,日志文件: {log_file}")

    def start(self):
        """启动日志管理器"""
        if self.running:
            self.logger.warning("日志管理器已经在运行中")
            return

        self.logger.info("正在启动日志管理器...")
        self.running = True

        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        self.logger.info("日志分析线程已启动")

        self.logger.info("日志管理器启动成功")

    def stop(self):
        """停止日志管理器"""
        if not self.running:
            self.logger.warning("日志管理器已经停止")
            return

        self.running = False

        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
            self.logger.info("日志分析线程已停止")

        self.logger.info("日志管理器已停止")

    def _analysis_loop(self):
        """分析循环"""
        while self.running:
            self.analyze_logs()
            time.sleep(self.config['analysis_interval'])

    def analyze_logs(self):
        """分析日志"""
        self.logger.info("开始分析日志...")

        try:
            log_file = os.path.join(self.config['log_dir'], self.config['log_file'])

            if not os.path.exists(log_file):
                self.logger.warning("日志文件不存在")
                return

            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()

            analysis_results = {
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'debug_count': 0,
                'error_types': {},
                'warning_types': {},
                'info_types': {},
                'debug_types': {},
                'time_distribution': {},
                'module_distribution': {}
            }

            log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - (ERROR|WARNING|INFO|DEBUG) - (.*)$'

            for line in log_lines:
                match = re.match(log_pattern, line)
                if match:
                    timestamp, module, level, message = match.groups()

                    if level == 'ERROR':
                        analysis_results['error_count'] += 1
                        error_type = self._extract_error_type(message)
                        analysis_results['error_types'][error_type] = analysis_results['error_types'].get(error_type, 0) + 1
                    elif level == 'WARNING':
                        analysis_results['warning_count'] += 1
                        warning_type = self._extract_warning_type(message)
                        analysis_results['warning_types'][warning_type] = analysis_results['warning_types'].get(warning_type, 0) + 1
                    elif level == 'INFO':
                        analysis_results['info_count'] += 1
                        info_type = self._extract_info_type(message)
                        analysis_results['info_types'][info_type] = analysis_results['info_types'].get(info_type, 0) + 1
                    elif level == 'DEBUG':
                        analysis_results['debug_count'] += 1
                        debug_type = self._extract_debug_type(message)
                        analysis_results['debug_types'][debug_type] = analysis_results['debug_types'].get(debug_type, 0) + 1

                    analysis_results['module_distribution'][module] = analysis_results['module_distribution'].get(module, 0) + 1

                    hour = timestamp.split(' ')[1].split(':')[0]
                    analysis_results['time_distribution'][hour] = analysis_results['time_distribution'].get(hour, 0) + 1

            with self.log_lock:
                self.analysis_results = analysis_results

            self.logger.info(f"日志分析完成,错误: {analysis_results['error_count']}, 警告: {analysis_results['warning_count']}, 信息: {analysis_results['info_count']}")
        except Exception as e:
            self.logger.error(f"分析日志失败: {str(e)}")

    def _extract_error_type(self, message: str) -> str:
        """提取错误类型"""
        error_patterns = {
            'ImportError': r'ImportError',
            'KeyError': r'KeyError',
            'AttributeError': r'AttributeError',
            'ValueError': r'ValueError',
            'TypeError': r'TypeError',
            'IOError': r'IOError',
            'FileNotFoundError': r'FileNotFoundError',
            'ConnectionError': r'ConnectionError',
            'TimeoutError': r'TimeoutError',
            'DatabaseError': r'DatabaseError',
            'OtherError': r'.*'
        }

        for error_type, pattern in error_patterns.items():
            if re.search(pattern, message):
                return error_type
        return 'OtherError'

    def _extract_warning_type(self, message: str) -> str:
        """提取警告类型"""
        if 'deprecated' in message.lower():
            return 'DeprecationWarning'
        elif 'performance' in message.lower():
            return 'PerformanceWarning'
        else:
            return 'GeneralWarning'

    def _extract_info_type(self, message: str) -> str:
        """提取信息类型"""
        if 'started' in message.lower():
            return 'StartInfo'
        elif 'completed' in message.lower():
            return 'CompletionInfo'
        else:
            return 'GeneralInfo'

    def _extract_debug_type(self, message: str) -> str:
        """提取调试类型"""
        return 'GeneralDebug'

    def get_analysis_results(self) -> Dict[str, Any]:
        """获取分析结果"""
        with self.log_lock:
            return self.analysis_results.copy()

    def log_event(self, level: str, message: str, module: str = None):
        """记录日志事件"""
        if level == 'ERROR':
            self.logger.error(f"[{module}] {message}" if module else message)
        elif level == 'WARNING':
            self.logger.warning(f"[{module}] {message}" if module else message)
        elif level == 'INFO':
            self.logger.info(f"[{module}] {message}" if module else message)
        elif level == 'DEBUG':
            self.logger.debug(f"[{module}] {message}" if module else message)


log_manager = LogManager()
