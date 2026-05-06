#!/usr/bin/env python3
"""
性能优化工具模块

import time
import functools
import logging
from typing import Callable, Any

# 配置日志
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
        测量函数执行时间的装饰器

        Args:
            func: 要测量的函数

        Returns:
            装饰后的函数
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            # 记录性能指标
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
            )
            self.metrics[func_name]['min_time'] = min(
                self.metrics[func_name]['min_time'],
            )

            # 记录执行时间
                logger.warning(f"函数 {func_name} 执行时间过长: {execution_time:.4f}s")
                logger.debug(f"函数 {func_name} 执行时间: {execution_time:.4f}s")

            return result

        return wrapper

    def get_metrics(self) -> dict:
        获取性能指标

        Returns:
            性能指标字典
        return self.metrics

    def reset_metrics(self) -> None:
        重置性能指标
        self.metrics.clear()

    def print_metrics(self) -> None:
        打印性能指标
        logger.info("===== 性能指标报告 =====")
        for func_name, metrics in self.metrics.items():
            logger.info(
                f"函数: {func_name}\n" +
                f"  调用次数: {metrics['calls']}\n" +
                f"  总执行时间: {metrics['total_time']:.4f}s\n" +
                f"  平均执行时间: {metrics['avg_time']:.4f}s\n" +
                f"  最大执行时间: {metrics['max_time']:.4f}s\n" +
                f"  最小执行时间: {metrics['min_time']:.4f}s"
            )
        logger.info("=====================")

# 创建全局性能监控器实例
performance_monitor = PerformanceMonitor()

# 导出装饰器
timeit = performance_monitor.measure_time

    """异步任务管理器"""

    def __init__(self):
        """初始化异步任务管理器"""
        self.tasks = []

    def run_async(self, func: Callable) -> Callable:
        异步执行函数的装饰器

        Args:
            func: 要异步执行的函数

        Returns:
            装饰后的函数
        @functools.wraps(func)
            import threading

            def task():
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"异步任务 {func.__name__} 执行完成")
                    return result
                except Exception as e:
                    logger.error(f"异步任务 {func.__name__} 执行失败: {str(e)}")
                    raise

            thread = threading.Thread(target=task)
            thread.start()
            self.tasks.append(thread)
            logger.debug(f"启动异步任务 {func.__name__}")

        return wrapper

    def wait_all(self) -> None:
        等待所有异步任务完成
            if thread.is_alive():
                thread.join()
        self.tasks.clear()

# 创建全局异步任务管理器实例
async_task_manager = AsyncTaskManager()

# 导出装饰器
async_run = async_task_manager.run_async

def optimize_memory_usage(func: Callable) -> Callable:
    优化内存使用的装饰器

    Args:
        func: 要优化的函数

    Returns:
        装饰后的函数
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import gc

        # 执行前清理垃圾
        gc.collect()

        result = func(*args, **kwargs)

        # 执行后清理垃圾
        gc.collect()


    return wrapper

def batch_process(items, batch_size: int, process_func: Callable) -> list:
    批量处理数据
    Args:
        items: 要处理的项目列表
        batch_size: 批处理大小

    Returns:
    results = []
    total = len(items)

    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        batch_results = process_func(batch)
        results.extend(batch_results)
        # 记录进度
        processed = min(i + batch_size, total)
        logger.info(f"批量处理进度: {processed}/{total} ({processed/total*100:.1f}%)")

    return results
