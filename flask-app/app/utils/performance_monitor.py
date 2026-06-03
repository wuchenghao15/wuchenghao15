# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控器模块
负责监控系统性能和检测性能瓶颈
"""

import os
import psutil
import logging
import time
from typing import Dict, Any, List
import sys

logger = logging.getLogger('performance_monitor')


class PerformanceMonitor:
    """性能监控器类"""

    def __init__(self):
        """初始化性能监控器"""
        self.process = psutil.Process(os.getpid())
        self.history = []
        self.max_history = 100
        logger.info("性能监控器初始化完成")

    def get_system_performance(self) -> Dict[str, Any]:
        """获取系统性能数据"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            net_io = psutil.net_io_counters()
            process_cpu = self.process.cpu_percent(interval=1)
            process_memory = self.process.memory_percent()
            process_threads = self.process.num_threads()

            performance_data = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_sent': net_io.bytes_sent,
                'network_recv': net_io.bytes_recv,
                'process_cpu': process_cpu,
                'process_memory': process_memory,
                'process_threads': process_threads,
                'timestamp': time.time()
            }

            self._save_history(performance_data)
            logger.debug(f"系统性能: CPU={cpu_usage}%, 内存={memory_usage}%, 磁盘={disk_usage}%")
            return performance_data
        except Exception as e:
            logger.error(f"获取系统性能数据失败: {str(e)}")
            return {}

    def _save_history(self, data: Dict[str, Any]):
        """保存历史数据"""
        self.history.append(data)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def clear_history(self):
        """清空历史数据"""
        self.history = []


if __name__ == '__main__':
    monitor = PerformanceMonitor()
    print("系统性能:")
    system_perf = monitor.get_system_performance()
    for key, value in system_perf.items():
        if key != 'timestamp':
            print(f"{key}: {value}")
