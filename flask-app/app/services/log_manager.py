#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块，用于集中管理和分析系统日志
"""

import os
import sys
import logging
import threading
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LogManager:
    """日志管理模块"""
    
    def __init__(self):
        """初始化日志管理器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("日志管理器已初始化")
        
        # 日志配置
        self.config = {
            'log_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'),
            'log_file': 'system.log',
            'max_log_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'log_level': logging.INFO,
            'analysis_interval': 3600,  # 分析间隔（秒）
        }
        
        # 确保日志目录存在
        if not os.path.exists(self.config['log_dir']):
            os.makedirs(self.config['log_dir'])
        
        # 日志存储
        self.logs = []
        self.log_lock = threading.RLock()
        
        # 日志分析结果
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
            'trends': [],
        }
        
        # 分析线程
        self.analysis_thread = None
        self.running = False
        
        # 初始化日志处理器
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志记录器"""
        # 创建文件处理器
        log_file = os.path.join(self.config['log_dir'], self.config['log_file'])
        
        # 配置日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 添加文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self.config['log_level'])
        
        # 添加到根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        self.logger.info(f"日志配置完成，日志文件: {log_file}")
    
    def start(self):
        """启动日志管理器"""
        if self.running:
            self.logger.warning("日志管理器已经在运行中")
            return
        
        self.logger.info("正在启动日志管理器...")
        self.running = True
        
        # 启动分析线程
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        self.logger.info("日志分析线程已启动")
        
        self.logger.info("日志管理器启动成功")
    
    def stop(self):
        """停止日志管理器"""
        if not self.running:
            self.logger.warning("日志管理器已经停止")
            return
        
        self.logger.info("正在停止日志管理器...")
        self.running = False
        
        # 等待分析线程结束
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
            
            # 读取日志文件
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_lines = f.readlines()
            
            # 分析日志
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
                'module_distribution': {},
                'trends': [],
            }
            
            # 日志格式正则表达式
            log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - (ERROR|WARNING|INFO|DEBUG) - (.*)$'
            
            for line in log_lines:
                match = re.match(log_pattern, line.strip())
                if match:
                    timestamp, module, level, message = match.groups()
                    
                    # 统计日志级别
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
                    
                    # 统计模块分布
                    analysis_results['module_distribution'][module] = analysis_results['module_distribution'].get(module, 0) + 1
                    
                    # 统计时间分布
                    hour = timestamp.split(' ')[1].split(':')[0]
                    analysis_results['time_distribution'][hour] = analysis_results['time_distribution'].get(hour, 0) + 1
            
            # 更新分析结果
            with self.log_lock:
                self.analysis_results = analysis_results
            
            self.logger.info(f"日志分析完成，错误: {analysis_results['error_count']}, 警告: {analysis_results['warning_count']}, 信息: {analysis_results['info_count']}")
        except Exception as e:
            self.logger.error(f"分析日志失败: {str(e)}")
    
    def _extract_error_type(self, message: str) -> str:
        """提取错误类型"""
        error_patterns = {
            'ImportError': r'ImportError',
            'AttributeError': r'AttributeError',
            'ValueError': r'ValueError',
            'TypeError': r'TypeError',
            'IOError': r'IOError',
            'FileNotFoundError': r'FileNotFoundError',
            'ConnectionError': r'ConnectionError',
            'TimeoutError': r'TimeoutError',
            'DatabaseError': r'DatabaseError',
            'OtherError': r'.*',
        }
        
        for error_type, pattern in error_patterns.items():
            if re.search(pattern, message):
                return error_type
        return 'OtherError'
    
    def _extract_warning_type(self, message: str) -> str:
        """提取警告类型"""
        warning_patterns = {
            'ResourceWarning': r'ResourceWarning',
            'DeprecationWarning': r'DeprecationWarning',
            'RuntimeWarning': r'RuntimeWarning',
            'UserWarning': r'UserWarning',
            'OtherWarning': r'.*',
        }
        
        for warning_type, pattern in warning_patterns.items():
            if re.search(pattern, message):
                return warning_type
        return 'OtherWarning'
    
    def _extract_info_type(self, message: str) -> str:
        """提取信息类型"""
        info_patterns = {
            'Startup': r'start|启动',
            'Shutdown': r'stop|停止',
            'Request': r'request|请求',
            'Response': r'response|响应',
            'Database': r'database|数据库',
            'AI': r'ai|AI',
            'OtherInfo': r'.*',
        }
        
        for info_type, pattern in info_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return info_type
        return 'OtherInfo'
    
    def _extract_debug_type(self, message: str) -> str:
        """提取调试类型"""
        debug_patterns = {
            'Resource': r'resource|资源',
            'Performance': r'performance|性能',
            'Cache': r'cache|缓存',
            'OtherDebug': r'.*',
        }
        
        for debug_type, pattern in debug_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return debug_type
        return 'OtherDebug'
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """获取分析结果"""
        with self.log_lock:
            return self.analysis_results.copy()
    
    def get_logs(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, 
                 level: Optional[str] = None, module: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取日志"""
        log_file = os.path.join(self.config['log_dir'], self.config['log_file'])
        
        if not os.path.exists(log_file):
            return []
        
        logs = []
        log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - (ERROR|WARNING|INFO|DEBUG) - (.*)$'
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = re.match(log_pattern, line.strip())
                if match:
                    timestamp_str, module_name, log_level, message = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    
                    # 过滤日志
                    if start_time and timestamp < start_time:
                        continue
                    if end_time and timestamp > end_time:
                        continue
                    if level and log_level != level:
                        continue
                    if module and module_name != module:
                        continue
                    
                    logs.append({
                        'timestamp': timestamp.isoformat(),
                        'module': module_name,
                        'level': log_level,
                        'message': message
                    })
        
        return logs
    
    def export_logs(self, file_path: str, start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None) -> bool:
        """导出日志"""
        try:
            logs = self.get_logs(start_time, end_time)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"日志导出成功: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出日志失败: {str(e)}")
            return False
    
    def clean_logs(self, days: int = 7) -> bool:
        """清理日志"""
        try:
            log_file = os.path.join(self.config['log_dir'], self.config['log_file'])
            
            if not os.path.exists(log_file):
                return True
            
            # 读取日志文件
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_lines = f.readlines()
            
            # 过滤出最近days天的日志
            cutoff_time = datetime.now() - timedelta(days=days)
            filtered_lines = []
            log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - .*$'
            
            for line in log_lines:
                match = re.match(log_pattern, line.strip())
                if match:
                    timestamp_str = match.group(1)
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    if timestamp >= cutoff_time:
                        filtered_lines.append(line)
                else:
                    # 保留无法解析的行
                    filtered_lines.append(line)
            
            # 写回过滤后的日志
            with open(log_file, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            
            self.logger.info(f"日志清理完成，保留最近{days}天的日志")
            return True
        except Exception as e:
            self.logger.error(f"清理日志失败: {str(e)}")
            return False
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        with self.log_lock:
            self.logger.info(f"更新日志管理器配置: {new_config}")
            self.config.update(new_config)
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        log_file = os.path.join(self.config['log_dir'], self.config['log_file'])
        
        stats = {
            'log_file': log_file,
            'log_size': os.path.getsize(log_file) if os.path.exists(log_file) else 0,
            'log_count': len(self.get_logs()),
            'analysis_results': self.get_analysis_results(),
        }
        
        return stats

# 初始化日志管理器实例
log_manager = LogManager()