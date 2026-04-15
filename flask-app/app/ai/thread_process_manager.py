#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI线程进程管理器，用于自动管理系统的线程和进程资源
"""

import os
import sys
import time
import logging
import threading
import multiprocessing
import psutil
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class AIThreadProcessManager:
    """
    AI驱动的线程进程管理器，能够自动管理系统的线程和进程资源
    """
    
    def __init__(self):
        """初始化AI线程进程管理器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI线程进程管理器已初始化")
        
        # 配置信息
        self.config = {
            'min_threads': 2,  # 最小线程数
            'max_threads': 32,  # 最大线程数
            'min_processes': 1,  # 最小进程数
            'max_processes': multiprocessing.cpu_count(),  # 最大进程数（默认CPU核心数）
            'monitor_interval': 5,  # 监控间隔（秒）
            'scale_up_threshold': 0.8,  # 资源使用阈值，超过则扩容
            'scale_down_threshold': 0.3,  # 资源使用阈值，低于则缩容
            'max_queue_size': 100,  # 最大任务队列大小
            'cpu_overload_threshold': 80,  # CPU使用率过载阈值（%）
            'memory_overload_threshold': 80,  # 内存使用率过载阈值（%）
        }
        
        # 线程池和进程池
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config['min_threads'])
        self.process_pool = ProcessPoolExecutor(max_workers=self.config['min_processes'])
        
        # 任务队列
        self.task_queue = Queue(maxsize=self.config['max_queue_size'])
        
        # 监控数据
        self.monitor_data = {
            'cpu_usage': [],  # 最近CPU使用率历史数据
            'memory_usage': [],  # 最近内存使用率历史数据
            'thread_usage': [],  # 最近线程使用率历史数据
            'process_usage': [],  # 最近进程使用率历史数据
            'queue_size': [],  # 最近队列大小历史数据
            'task_execution_time': [],  # 最近任务执行时间历史数据
        }
        
        # 监控线程
        self.monitor_thread = None
        self.optimize_thread = None
        self.running = False
        
        # 线程安全锁
        self.lock = threading.RLock()
        
    def start(self):
        """启动AI线程进程管理器"""
        if self.running:
            self.logger.warning("AI线程进程管理器已经在运行中")
            return
        
        self.logger.info("正在启动AI线程进程管理器...")
        self.running = True
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("监控线程已启动")
        
        # 启动优化线程
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
        
        # 等待线程结束
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.logger.info("监控线程已停止")
        
        if self.optimize_thread:
            self.optimize_thread.join(timeout=5)
            self.logger.info("优化线程已停止")
        
        # 关闭线程池和进程池
        self.thread_pool.shutdown(wait=True, cancel_futures=True)
        self.process_pool.shutdown(wait=True, cancel_futures=True)
        
        self.logger.info("AI线程进程管理器已停止")
    
    def _monitor_loop(self):
        """监控循环，定期收集系统资源和任务执行数据"""
        while self.running:
            self._collect_resource_data()
            self._collect_task_data()
            time.sleep(self.config['monitor_interval'])
    
    def _collect_resource_data(self):
        """收集系统资源使用数据"""
        with self.lock:
            # 收集CPU使用率
            cpu_usage = psutil.cpu_percent(interval=0.1)
            self.monitor_data['cpu_usage'].append(cpu_usage)
            if len(self.monitor_data['cpu_usage']) > 100:
                self.monitor_data['cpu_usage'].pop(0)
            
            # 收集内存使用率
            memory_usage = psutil.virtual_memory().percent
            self.monitor_data['memory_usage'].append(memory_usage)
            if len(self.monitor_data['memory_usage']) > 100:
                self.monitor_data['memory_usage'].pop(0)
            
            # 收集线程使用率
            thread_usage = len(threading.enumerate()) / self.config['max_threads'] * 100
            self.monitor_data['thread_usage'].append(thread_usage)
            if len(self.monitor_data['thread_usage']) > 100:
                self.monitor_data['thread_usage'].pop(0)
            
            # 收集进程使用率
            process_usage = len(psutil.pids()) / (self.config['max_processes'] * 10) * 100
            self.monitor_data['process_usage'].append(process_usage)
            if len(self.monitor_data['process_usage']) > 100:
                self.monitor_data['process_usage'].pop(0)
            
            # 收集队列大小
            queue_size = self.task_queue.qsize()
            self.monitor_data['queue_size'].append(queue_size)
            if len(self.monitor_data['queue_size']) > 100:
                self.monitor_data['queue_size'].pop(0)
            
            self.logger.debug(f"资源监控数据: CPU={cpu_usage}%, Memory={memory_usage}%, Thread={thread_usage}%, Process={process_usage}%, Queue={queue_size}")
    
    def _collect_task_data(self):
        """收集任务执行数据"""
        # 这里可以根据实际任务执行情况收集数据
        # 例如，记录最近任务的执行时间、成功率等
        pass
    
    def _optimize_loop(self):
        """优化循环，定期调整线程池和进程池大小"""
        while self.running:
            self._optimize_resources()
            time.sleep(self.config['monitor_interval'] * 2)  # 优化频率是监控频率的一半
    
    def _optimize_resources(self):
        """根据监控数据优化资源分配"""
        with self.lock:
            # 计算平均资源使用率
            avg_cpu = sum(self.monitor_data['cpu_usage']) / len(self.monitor_data['cpu_usage']) if self.monitor_data['cpu_usage'] else 0
            avg_memory = sum(self.monitor_data['memory_usage']) / len(self.monitor_data['memory_usage']) if self.monitor_data['memory_usage'] else 0
            avg_queue_size = sum(self.monitor_data['queue_size']) / len(self.monitor_data['queue_size']) if self.monitor_data['queue_size'] else 0
            
            self.logger.debug(f"平均资源使用率: CPU={avg_cpu}%, Memory={avg_memory}%, Queue={avg_queue_size}")
            
            # 调整线程池大小
            self._adjust_thread_pool(avg_cpu, avg_memory, avg_queue_size)
            
            # 调整进程池大小
            self._adjust_process_pool(avg_cpu, avg_memory, avg_queue_size)
    
    def _adjust_thread_pool(self, avg_cpu: float, avg_memory: float, avg_queue_size: float):
        """根据资源使用率调整线程池大小"""
        current_threads = self.thread_pool._max_workers
        new_threads = current_threads
        
        # 基于CPU、内存和队列大小的综合调整
        # 计算资源压力指数
        cpu_pressure = min(avg_cpu / 100, 1.0)
        memory_pressure = min(avg_memory / 100, 1.0)
        queue_pressure = min(avg_queue_size / self.config['max_queue_size'], 1.0)
        
        # 综合压力指数
        total_pressure = (cpu_pressure * 0.4 + memory_pressure * 0.3 + queue_pressure * 0.3)
        
        # 基于压力指数动态调整线程数
        if total_pressure < 0.3:
            # 低压力，逐渐减少线程数
            new_threads = max(self.config['min_threads'], current_threads - 1)
        elif total_pressure > 0.7:
            # 高压力，快速增加线程数
            # 根据压力程度决定增加的线程数
            increase_count = 1 if total_pressure < 0.8 else 2 if total_pressure < 0.9 else 3
            new_threads = min(self.config['max_threads'], current_threads + increase_count)
        elif total_pressure > 0.5:
            # 中等压力，缓慢增加线程数
            new_threads = min(self.config['max_threads'], current_threads + 1)
        
        # 基于内存使用率的紧急调整
        if avg_memory > self.config['memory_overload_threshold'] * 1.2:
            # 内存严重过载，立即减少线程数
            new_threads = max(self.config['min_threads'], current_threads - 2)
        elif avg_memory > self.config['memory_overload_threshold']:
            # 内存过载，减少线程数
            new_threads = max(self.config['min_threads'], current_threads - 1)
        
        # 基于队列大小的紧急调整
        if avg_queue_size > self.config['max_queue_size'] * 0.9:
            # 队列接近满，快速增加线程数
            new_threads = min(self.config['max_threads'], current_threads + 2)
        
        if new_threads != current_threads:
            self._resize_thread_pool(new_threads)
    
    def _adjust_process_pool(self, avg_cpu: float, avg_memory: float, avg_queue_size: float):
        """根据资源使用率调整进程池大小"""
        current_processes = self.process_pool._max_workers
        new_processes = current_processes
        
        # 基于CPU、内存和队列大小的综合调整
        # 计算资源压力指数
        cpu_pressure = min(avg_cpu / 100, 1.0)
        memory_pressure = min(avg_memory / 100, 1.0)
        queue_pressure = min(avg_queue_size / self.config['max_queue_size'], 1.0)
        
        # 综合压力指数（进程池对CPU更敏感）
        total_pressure = (cpu_pressure * 0.5 + memory_pressure * 0.3 + queue_pressure * 0.2)
        
        # 基于压力指数动态调整进程数
        if total_pressure < 0.2:
            # 低压力，逐渐减少进程数
            new_processes = max(self.config['min_processes'], current_processes - 1)
        elif total_pressure > 0.8:
            # 高压力，增加进程数
            new_processes = min(self.config['max_processes'], current_processes + 1)
        elif total_pressure > 0.6:
            # 中等压力，考虑增加进程数
            if current_processes < self.config['max_processes']:
                new_processes = current_processes + 1
        
        # 基于内存使用率的紧急调整
        if avg_memory > self.config['memory_overload_threshold'] * 1.5:
            # 内存严重过载，立即减少进程数
            new_processes = max(self.config['min_processes'], current_processes - 2)
        elif avg_memory > self.config['memory_overload_threshold'] * 1.2:
            # 内存过载，减少进程数
            new_processes = max(self.config['min_processes'], current_processes - 1)
        
        # 基于队列大小的紧急调整
        if avg_queue_size > self.config['max_queue_size'] * 0.95:
            # 队列即将满，增加进程数
            new_processes = min(self.config['max_processes'], current_processes + 1)
        
        # 进程池大小调整更加谨慎，避免频繁创建销毁进程
        if new_processes != current_processes:
            # 检查是否真的需要调整
            if abs(new_processes - current_processes) >= 1:
                self._resize_process_pool(new_processes)
    
    def _resize_thread_pool(self, new_size: int):
        """调整线程池大小"""
        self.logger.info(f"调整线程池大小: {self.thread_pool._max_workers} -> {new_size}")
        
        # 关闭旧的线程池并创建新的线程池
        old_pool = self.thread_pool
        self.thread_pool = ThreadPoolExecutor(max_workers=new_size)
        old_pool.shutdown(wait=False, cancel_futures=True)
    
    def _resize_process_pool(self, new_size: int):
        """调整进程池大小"""
        self.logger.info(f"调整进程池大小: {self.process_pool._max_workers} -> {new_size}")
        
        # 关闭旧的进程池并创建新的进程池
        old_pool = self.process_pool
        self.process_pool = ProcessPoolExecutor(max_workers=new_size)
        old_pool.shutdown(wait=False, cancel_futures=True)
    
    def submit_task(self, task_func, *args, **kwargs):
        """提交任务到合适的执行池"""
        with self.lock:
            # 根据任务类型和资源情况选择执行池
            task_type = self._classify_task(task_func)
            
            if task_type == 'cpu_intensive':
                # CPU密集型任务提交到进程池
                return self.process_pool.submit(task_func, *args, **kwargs)
            else:
                # I/O密集型任务提交到线程池
                return self.thread_pool.submit(task_func, *args, **kwargs)
    
    def _classify_task(self, task_func) -> str:
        """根据任务函数分类任务类型"""
        # 基于函数名称、参数类型和历史执行数据进行任务分类
        func_name = task_func.__name__
        
        # 基于名称的分类
        cpu_intensive_keywords = ['compute', 'calculate', 'process', 'train', 'generate', 'analyze', 'render', 'encrypt', 'decrypt']
        io_intensive_keywords = ['read', 'write', 'fetch', 'download', 'upload', 'request', 'response', 'socket', 'file']
        
        # 检查CPU密集型关键词
        for keyword in cpu_intensive_keywords:
            if keyword in func_name.lower():
                return 'cpu_intensive'
        
        # 检查IO密集型关键词
        for keyword in io_intensive_keywords:
            if keyword in func_name.lower():
                return 'io_intensive'
        
        # 基于函数参数和模块进行分类
        import inspect
        import os
        
        # 获取函数的模块名
        module_name = inspect.getmodule(task_func).__name__ if inspect.getmodule(task_func) else ''
        
        # 基于模块名的分类
        cpu_intensive_modules = ['numpy', 'scipy', 'tensorflow', 'torch', 'sklearn']
        io_intensive_modules = ['requests', 'urllib', 'os', 'file', 'socket']
        
        for module in cpu_intensive_modules:
            if module in module_name:
                return 'cpu_intensive'
        
        for module in io_intensive_modules:
            if module in module_name:
                return 'io_intensive'
        
        # 默认分类为IO密集型
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
            self.logger.info(f"更新AI线程进程管理器配置: {new_config}")
            self.config.update(new_config)
            
            # 如果调整了最大线程数或进程数，立即调整池大小
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

# 初始化AI线程进程管理器实例
ai_thread_process_manager = AIThreadProcessManager()
