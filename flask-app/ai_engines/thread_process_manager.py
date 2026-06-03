# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""AI线程进程管理器,用于自动管理系统的线程和进程资源"""

import os
import sys
import time
import logging
import threading
import multiprocessing
import psutil
import inspect
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, Any, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class AIThreadProcessManager:
    """AI驱动的线程进程管理器,能够自动管理系统的线程和进程资源"""

    def __init__(self):
        """初始化AI线程进程管理器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI线程进程管理器已初始化")

        self.config = {
            'min_threads': 2,
            'max_threads': 32,
            'min_processes': 1,
            'max_processes': multiprocessing.cpu_count(),
            'monitor_interval': 5,
            'scale_up_threshold': 0.8,
            'scale_down_threshold': 0.3,
            'max_queue_size': 100,
            'cpu_overload_threshold': 80,
            'memory_overload_threshold': 80,
        }

        self.thread_pool = ThreadPoolExecutor(max_workers=self.config['min_threads'])
        self.process_pool = ProcessPoolExecutor(max_workers=self.config['min_processes'])

        self.task_queue = Queue(maxsize=self.config['max_queue_size'])

        self.monitor_data = {
            'cpu_usage': [],
            'memory_usage': [],
            'thread_usage': [],
            'process_usage': [],
            'queue_size': [],
            'task_execution_time': [],
        }

        self.monitor_thread = None
        self.optimize_thread = None
        self.running = False

        self.lock = threading.RLock()

    def start(self):
        """启动AI线程进程管理器"""
        if self.running:
            self.logger.warning("AI线程进程管理器已经在运行中")
            return

        self.logger.info("正在启动AI线程进程管理器...")
        self.running = True

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("监控线程已启动")

        self.optimize_thread = threading.Thread(target=self._optimize_loop, daemon=True)
        self.optimize_thread.start()
        self.logger.info("优化线程已启动")

        self.logger.info("AI线程进程管理器启动成功")

    def stop(self):
        """停止AI线程进程管理器"""
        if not self.running:
            self.logger.warning("AI线程进程管理器已经停止")
            return

        self.logger.info("正在停止AI线程进程管理器...")
        self.running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.logger.info("监控线程已停止")

        if self.optimize_thread:
            self.optimize_thread.join(timeout=5)
            self.logger.info("优化线程已停止")

        self.thread_pool.shutdown(wait=True, cancel_futures=True)
        self.process_pool.shutdown(wait=True, cancel_futures=True)

        self.logger.info("AI线程进程管理器已停止")

    def _monitor_loop(self):
        """监控循环,定期收集系统资源和任务执行数据"""
        while self.running:
            self._collect_resource_data()
            self._collect_task_data()
            time.sleep(self.config['monitor_interval'])

    def _collect_resource_data(self):
        """收集系统资源使用数据"""
        with self.lock:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            self.monitor_data['cpu_usage'].append(cpu_usage)
            if len(self.monitor_data['cpu_usage']) > 100:
                self.monitor_data['cpu_usage'].pop(0)

            memory_usage = psutil.virtual_memory().percent
            self.monitor_data['memory_usage'].append(memory_usage)
            if len(self.monitor_data['memory_usage']) > 100:
                self.monitor_data['memory_usage'].pop(0)

            thread_usage = len(threading.enumerate()) / self.config['max_threads'] * 100
            self.monitor_data['thread_usage'].append(thread_usage)
            if len(self.monitor_data['thread_usage']) > 100:
                self.monitor_data['thread_usage'].pop(0)

            process_usage = len(psutil.pids()) / (self.config['max_processes'] * 10) * 100
            self.monitor_data['process_usage'].append(process_usage)
            if len(self.monitor_data['process_usage']) > 100:
                self.monitor_data['process_usage'].pop(0)

            queue_size = self.task_queue.qsize()
            self.monitor_data['queue_size'].append(queue_size)
            if len(self.monitor_data['queue_size']) > 100:
                self.monitor_data['queue_size'].pop(0)

            self.logger.debug(f"资源监控数据: CPU={cpu_usage}%, Memory={memory_usage}%, Thread={thread_usage}%, Process={process_usage}%, Queue={queue_size}")

    def _collect_task_data(self):
        """收集任务执行数据"""
        pass

    def _optimize_loop(self):
        """优化循环,定期调整线程池和进程池大小"""
        while self.running:
            self._optimize_resources()
            time.sleep(self.config['monitor_interval'] * 2)

    def _optimize_resources(self):
        """根据监控数据优化资源分配"""
        with self.lock:
            avg_cpu = sum(self.monitor_data['cpu_usage']) / len(self.monitor_data['cpu_usage']) if self.monitor_data['cpu_usage'] else 0
            avg_memory = sum(self.monitor_data['memory_usage']) / len(self.monitor_data['memory_usage']) if self.monitor_data['memory_usage'] else 0
            avg_queue_size = sum(self.monitor_data['queue_size']) / len(self.monitor_data['queue_size']) if self.monitor_data['queue_size'] else 0

            self.logger.debug(f"平均资源使用率: CPU={avg_cpu}%, Memory={avg_memory}%, Queue={avg_queue_size}")

            self._adjust_thread_pool(avg_cpu, avg_memory, avg_queue_size)
            self._adjust_process_pool(avg_cpu, avg_memory, avg_queue_size)

    def _adjust_thread_pool(self, avg_cpu: float, avg_memory: float, avg_queue_size: float):
        """根据资源使用率调整线程池大小"""
        current_threads = self.thread_pool._max_workers
        new_threads = current_threads

        cpu_pressure = min(avg_cpu / 100, 1.0)
        memory_pressure = min(avg_memory / 100, 1.0)
        queue_pressure = min(avg_queue_size / self.config['max_queue_size'], 1.0)

        total_pressure = (cpu_pressure * 0.4 + memory_pressure * 0.3 + queue_pressure * 0.3)

        if total_pressure < 0.3:
            new_threads = max(self.config['min_threads'], current_threads - 1)
        elif total_pressure > 0.7:
            increase_count = 1 if total_pressure < 0.8 else 2 if total_pressure < 0.9 else 3
            new_threads = min(self.config['max_threads'], current_threads + increase_count)
        elif total_pressure > 0.5:
            new_threads = min(self.config['max_threads'], current_threads + 1)

        if avg_memory > self.config['memory_overload_threshold'] * 1.2:
            new_threads = max(self.config['min_threads'], current_threads - 2)
        elif avg_memory > self.config['memory_overload_threshold']:
            new_threads = max(self.config['min_threads'], current_threads - 1)

        if avg_queue_size > self.config['max_queue_size'] * 0.9:
            new_threads = min(self.config['max_threads'], current_threads + 2)

        if new_threads != current_threads:
            self._resize_thread_pool(new_threads)

    def _adjust_process_pool(self, avg_cpu: float, avg_memory: float, avg_queue_size: float):
        """根据资源使用率调整进程池大小"""
        current_processes = self.process_pool._max_workers
        new_processes = current_processes

        cpu_pressure = min(avg_cpu / 100, 1.0)
        memory_pressure = min(avg_memory / 100, 1.0)
        queue_pressure = min(avg_queue_size / self.config['max_queue_size'], 1.0)

        total_pressure = (cpu_pressure * 0.5 + memory_pressure * 0.3 + queue_pressure * 0.2)

        if total_pressure < 0.3:
            new_processes = max(self.config['min_processes'], current_processes - 1)
        elif total_pressure > 0.8:
            new_processes = min(self.config['max_processes'], current_processes + 1)
        elif total_pressure > 0.6:
            if current_processes < self.config['max_processes']:
                new_processes = current_processes + 1

        if avg_memory > self.config['memory_overload_threshold'] * 1.5:
            new_processes = max(self.config['min_processes'], current_processes - 2)
        elif avg_memory > self.config['memory_overload_threshold'] * 1.2:
            new_processes = max(self.config['min_processes'], current_processes - 1)

        if avg_queue_size > self.config['max_queue_size'] * 0.95:
            new_processes = min(self.config['max_processes'], current_processes + 1)

        if abs(new_processes - current_processes) >= 1:
            self._resize_process_pool(new_processes)

    def _resize_thread_pool(self, new_size: int):
        """调整线程池大小"""
        self.logger.info(f"调整线程池大小: {self.thread_pool._max_workers} -> {new_size}")
        old_pool = self.thread_pool
        self.thread_pool = ThreadPoolExecutor(max_workers=new_size)
        old_pool.shutdown(wait=False, cancel_futures=True)

    def _resize_process_pool(self, new_size: int):
        """调整进程池大小"""
        self.logger.info(f"调整进程池大小: {self.process_pool._max_workers} -> {new_size}")
        old_pool = self.process_pool
        self.process_pool = ProcessPoolExecutor(max_workers=new_size)
        old_pool.shutdown(wait=False, cancel_futures=True)

    def submit_task(self, task_func: Callable, *args, **kwargs):
        """提交任务到合适的执行池"""
        with self.lock:
            task_type = self._classify_task(task_func)

            if task_type == 'cpu_intensive':
                return self.process_pool.submit(task_func, *args, **kwargs)
            else:
                return self.thread_pool.submit(task_func, *args, **kwargs)

    def _classify_task(self, task_func: Callable) -> str:
        """根据任务函数分类任务类型"""
        func_name = task_func.__name__

        cpu_intensive_keywords = ['compute', 'calculate', 'process', 'train', 'generate', 'analyze', 'render', 'encrypt', 'decrypt']
        io_intensive_keywords = ['read', 'write', 'fetch', 'download', 'upload', 'request', 'response', 'socket', 'file']

        for keyword in cpu_intensive_keywords:
            if keyword in func_name.lower():
                return 'cpu_intensive'

        for keyword in io_intensive_keywords:
            if keyword in func_name.lower():
                return 'io_intensive'

        module_name = inspect.getmodule(task_func).__name__ if inspect.getmodule(task_func) else ''

        cpu_intensive_modules = ['numpy', 'scipy', 'tensorflow', 'torch', 'sklearn']
        io_intensive_modules = ['requests', 'urllib', 'os', 'file', 'socket']

        for module in cpu_intensive_modules:
            if module in module_name:
                return 'cpu_intensive'

        for module in io_intensive_modules:
            if module in module_name:
                return 'io_intensive'

        return 'io_intensive'

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        with self.lock:
            return {
                'running': self.running,
                'thread_pool_size': self.thread_pool._max_workers,
                'process_pool_size': self.process_pool._max_workers,
                'queue_size': self.task_queue.qsize(),
                'monitor_data': self.monitor_data.copy(),
                'config': self.config.copy(),
            }

    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        with self.lock:
            self.config.update(new_config)

            if 'max_threads' in new_config:
                current_threads = self.thread_pool._max_workers
                new_max_threads = new_config['max_threads']
                if current_threads > new_max_threads:
                    self._resize_thread_pool(new_max_threads)

            if 'max_processes' in new_config:
                current_processes = self.process_pool._max_workers
                new_max_processes = new_config['max_processes']
                if current_processes > new_max_processes:
                    self._resize_process_pool(new_max_processes)

    def shutdown(self, wait: bool = True):
        """关闭线程进程管理器"""
        self.stop()

ai_thread_process_manager = AIThreadProcessManager()