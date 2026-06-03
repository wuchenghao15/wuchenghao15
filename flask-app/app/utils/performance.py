# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
性能优化工具模块
"""

import time
import functools
import logging
from typing import Callable, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('performance')


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        """初始化性能监控器"""
        self.metrics = {}

    def measure_time(self, func: Callable) -> Callable:
        """
        测量函数执行时间的装饰器

        Args:
            func: 要测量的函数

        Returns:
            装饰后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            func_name = f"{func.__module__}.{func.__name__}"
            if func_name not in self.metrics:
                self.metrics[func_name] = {
                    'calls': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'min_time': float('inf')
                }

            self.metrics[func_name]['calls'] += 1
            self.metrics[func_name]['total_time'] += execution_time
            self.metrics[func_name]['avg_time'] = (
                self.metrics[func_name]['total_time'] /
                self.metrics[func_name]['calls']
            )
            self.metrics[func_name]['max_time'] = max(
                self.metrics[func_name]['max_time'],
                execution_time
            )
            self.metrics[func_name]['min_time'] = min(
                self.metrics[func_name]['min_time'],
                execution_time
            )

            if execution_time > 1.0:
                logger.warning(f"函数 {func_name} 执行时间过长: {execution_time:.4f}s")
            else:
                logger.debug(f"函数 {func_name} 执行时间: {execution_time:.4f}s")

            return result
        return wrapper


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self):
        """初始化异步任务管理器"""
        self.tasks = []

    def run_async(self, func: Callable) -> Callable:
        """
        异步执行函数的装饰器

        Args:
            func: 要异步执行的函数

        Returns:
            装饰后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import threading

            def task():
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"异步任务 {func.__name__} 执行完成")
                    return result
                except Exception as e:
                    logger.error(f"异步任务 {func.__name__} 执行失败: {str(e)}")
                    return None

            thread = threading.Thread(target=task)
            thread.start()
            self.tasks.append(thread)
            return thread
        return wrapper
