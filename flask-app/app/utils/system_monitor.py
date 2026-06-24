# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统监控模块,用于跟踪系统状态和性能指标

import time
import threading
import psutil
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional
from app.config import Config
from app.utils.logging import logger


class SystemMonitor:
    系统监控类,用于收集和报告系统状态

    def __init__(self):
        self._is_running = False
        self._monitor_thread = None
        self._metrics: Dict[str, List[Dict]] = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'process': [],
            'database': []
        }
        self._lock = threading.Lock()
        self._max_metrics = 100  # 保留的最大指标数量

    def start(self):
        启动系统监控
        if self._is_running:
            logger.warning("系统监控已在运行")
            return

        self._is_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("系统监控已启动")

    def stop(self):
        停止系统监控
        self._is_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        logger.info("系统监控已停止")

    def _monitor_loop(self):
        while self._is_running:
            try:
                self.collect_metrics()
            except Exception as e:
                logger.error(f"监控循环错误: {str(e)}")
                time.sleep(5)  # 出错后等待5秒重试

    def collect_metrics(self):
        收集系统指标
        timestamp = time.time()
        metrics = {
            'timestamp': timestamp,
            'cpu': self._get_cpu_metrics(),
            'memory': self._get_memory_metrics(),
            'disk': self._get_disk_metrics(),
            'process': self._get_process_metrics(),
            'database': self._get_database_metrics()
        }

        with self._lock:
            # 更新指标数据,保持固定大小
            for key, value in metrics.items():
                if key != 'timestamp':
                    self._metrics[key].append(value)
                    if len(self._metrics[key]) > self._max_metrics:
                        self._metrics[key].pop(0)

    def _get_cpu_metrics(self) -> Dict:
        获取CPU指标
        return {
            'usage_percent': psutil.cpu_percent(interval=0.1),
            'count': psutil.cpu_count(),
            'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }

    def _get_memory_metrics(self) -> Dict:
        获取内存指标
        mem = psutil.virtual_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'percent': mem.percent
        }

    def _get_disk_metrics(self) -> Dict:
        获取磁盘指标
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }

        获取进程指标
        process = psutil.Process()
        with process.oneshot():
            return {
                'pid': process.pid,
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files())
            }

        获取数据库指标
        try:
            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                conn_cursor = conn.cursor()
                cursor = conn.cursor()
                
                # 获取数据库大小(简单实现)
                import os
import logging
import sys
                db_size = os.path.getsize(Config.DATABASE_PATH) if os.path.exists(Config.DATABASE_PATH) else 0
                
                # 获取表数量
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

            return {
                'size': db_size,
                'table_count': table_count,
                'status': 'healthy'
            }
        except Exception as e:
            logger.error(f"获取数据库指标失败: {str(e)}")
            return {
                'size': 0,
                'status': f'error: {str(e)}'
            }

    def get_metrics(self, metric_type: Optional[str] = None, limit: int = 20) -> Dict:
        获取系统指标

        Args:
            metric_type: 指标类型(可选),如 'cpu', 'memory', 'disk', 'process', 'database'
            limit: 返回的最大指标数量

        Returns:
            Dict: 系统指标数据
        with self._lock:
            if metric_type and metric_type in self._metrics:
                    metric_type: self._metrics[metric_type][-limit:]
                }
            else:
                # 返回所有指标类型的最新数据
                for key, values in self._metrics.items():
                    if values:
    pass
                return latest_metrics

    def get_system_status(self) -> Dict:
        获取系统状态摘要

        Returns:
            Dict: 系统状态摘要
        metrics = self.get_metrics(limit=1)
        status = {
            'timestamp': time.time(),
            'status': 'running',
            'components': {
                'cpu': 'healthy' if metrics.get('cpu') and metrics['cpu'][0]['usage_percent'] < 90 else 'warning',
                'memory': 'healthy' if metrics.get('memory') and metrics['memory'][0]['percent'] < 90 else 'warning',
                'disk': 'healthy' if metrics.get('disk') and metrics['disk'][0]['percent'] < 90 else 'warning',
                'database': 'healthy' if metrics.get('database') and metrics['database'][0]['status'] == 'healthy' else 'error'
        }
        return status

# 创建全局系统监控实例
system_monitor = SystemMonitor()

"""