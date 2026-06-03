#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程管理系统 V2.0 (Thread Manager)
增强版线程管理系统，支持线程池、任务调度、监控和资源管理
"""

import time
import uuid
import logging
import threading
import queue
import traceback
import concurrent.futures
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Callable, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('thread_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ThreadManager')

class ThreadStatus(Enum):
    """线程状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED = "blocked"
    TERMINATED = "terminated"
    ERROR = "error"

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class PoolStatus(Enum):
    """线程池状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

@dataclass
class Task:
    """任务数据类"""
    task_id: str
    function: Callable
    args: Tuple = ()
    kwargs: Dict = None
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[float] = None
    callback: Optional[Callable] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"
    result: Any = None
    error: Optional[Exception] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class ThreadInfo:
    """线程信息数据类"""
    thread_id: str
    name: str
    status: ThreadStatus
    current_task: Optional[str] = None
    task_history: List[str] = None
    start_time: float = 0.0
    last_active_time: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    error_count: int = 0
    avg_task_time: float = 0.0
    total_work_time: float = 0.0
    
    def __post_init__(self):
        if self.task_history is None:
            self.task_history = []

class ThreadManager:
    """增强版线程管理系统"""
    
    def __init__(self, max_workers: int = 10, min_workers: int = 2):
        """初始化线程管理器"""
        self.max_workers = max_workers
        self.min_workers = min_workers
        self.current_workers = min_workers
        
        self.status = PoolStatus.INITIALIZING
        self.is_running = False
        
        self.task_queue = queue.PriorityQueue(maxsize=10000)
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="tm_"
        )
        
        self.thread_info: Dict[str, ThreadInfo] = {}
        self.task_info: Dict[str, Task] = {}
        
        self.lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        self.stats = {
            "total_tasks_submitted": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "total_tasks_cancelled": 0,
            "active_tasks": 0,
            "pending_tasks": 0,
            "total_execution_time": 0,
            "avg_task_duration": 0,
            "peak_workers": 0,
            "current_workers": 0,
            "errors": []
        }
        
        self.futures: Dict[str, concurrent.futures.Future] = {}
        
        self._init_thread_info()
        
        logger.info(f"线程管理器初始化完成: max_workers={max_workers}, min_workers={min_workers}")
    
    def _init_thread_info(self):
        """初始化线程信息"""
        for i in range(self.min_workers):
            thread_id = f"thread_{i}"
            self.thread_info[thread_id] = ThreadInfo(
                thread_id=thread_id,
                name=f"tm_worker_{i}",
                status=ThreadStatus.IDLE,
                start_time=time.time()
            )
    
    def start(self):
        """启动线程管理器"""
        if self.is_running:
            logger.warning("线程管理器已在运行")
            return
        
        self.status = PoolStatus.RUNNING
        self.is_running = True
        
        self._start_monitor_thread()
        self._start_worker_threads()
        
        logger.info("线程管理器已启动")
    
    def _start_monitor_thread(self):
        """启动监控线程"""
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="tm_monitor",
            daemon=True
        )
        self.monitor_thread.start()
    
    def _start_worker_threads(self):
        """启动工作线程"""
        with self.lock:
            for i in range(self.min_workers):
                thread = threading.Thread(
                    target=self._worker_loop,
                    name=f"tm_worker_{i}",
                    daemon=True
                )
                thread.start()
    
    def _worker_loop(self):
        """工作线程循环"""
        thread_name = threading.current_thread().name
        
        while self.is_running:
            try:
                try:
                    priority, task_id, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                self._update_thread_status(thread_name, ThreadStatus.RUNNING)
                self._assign_task_to_thread(thread_name, task_id)
                
                task.started_at = time.time()
                task.status = "running"
                
                try:
                    result = self._execute_task(task)
                    task.result = result
                    task.status = "completed"
                    self._complete_task(task, thread_name)
                    
                    if task.callback:
                        try:
                            task.callback(task)
                        except Exception as e:
                            logger.error(f"任务回调执行失败: {str(e)}")
                            
                except Exception as e:
                    task.error = e
                    task.status = "failed"
                    self._fail_task(task, thread_name)
                    
                finally:
                    task.completed_at = time.time()
                    self.task_queue.task_done()
                    self._update_thread_status(thread_name, ThreadStatus.IDLE)
                    
            except Exception as e:
                logger.error(f"工作线程错误 [{thread_name}]: {str(e)}")
    
    def _execute_task(self, task: Task) -> Any:
        """执行任务"""
        if task.timeout:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"任务超时: {task.timeout}秒")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(task.timeout))
            
            try:
                result = task.function(*task.args, **task.kwargs)
            finally:
                signal.alarm(0)
            
            return result
        else:
            return task.function(*task.args, **task.kwargs)
    
    def _assign_task_to_thread(self, thread_name: str, task_id: str):
        """分配任务给线程"""
        with self.lock:
            for info in self.thread_info.values():
                if info.name == thread_name:
                    info.current_task = task_id
                    info.last_active_time = time.time()
                    info.total_tasks += 1
                    info.task_history.append(task_id)
                    if len(info.task_history) > 100:
                        info.task_history.pop(0)
                    break
    
    def _complete_task(self, task: Task, thread_name: str):
        """完成任务"""
        execution_time = 0
        if task.started_at and task.completed_at:
            execution_time = task.completed_at - task.started_at
        
        with self.stats_lock:
            self.stats["total_tasks_completed"] += 1
            self.stats["active_tasks"] -= 1
            self.stats["total_execution_time"] += execution_time
            self.stats["avg_task_duration"] = (
                self.stats["total_execution_time"] / 
                self.stats["total_tasks_completed"]
            )
        
        with self.lock:
            for info in self.thread_info.values():
                if info.name == thread_name:
                    info.completed_tasks += 1
                    info.total_work_time += execution_time
                    info.avg_task_time = info.total_work_time / info.completed_tasks
                    info.current_task = None
                    break
        
        logger.debug(f"任务完成: {task.task_id}, 耗时: {execution_time:.4f}s")
    
    def _fail_task(self, task: Task, thread_name: str):
        """任务失败"""
        with self.stats_lock:
            self.stats["total_tasks_failed"] += 1
            self.stats["active_tasks"] -= 1
            if len(self.stats["errors"]) < 100:
                self.stats["errors"].append({
                    "task_id": task.task_id,
                    "error": str(task.error),
                    "timestamp": time.time()
                })
        
        with self.lock:
            for info in self.thread_info.values():
                if info.name == thread_name:
                    info.error_count += 1
                    info.current_task = None
                    break
        
        logger.error(f"任务失败: {task.task_id}, 错误: {str(task.error)}")
    
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """提交任务到线程池"""
        if not self.is_running:
            raise RuntimeError("线程管理器未运行")
        
        priority = kwargs.pop('priority', TaskPriority.NORMAL)
        timeout = kwargs.pop('timeout', None)
        callback = kwargs.pop('callback', None)
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = Task(
            task_id=task_id,
            function=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            callback=callback
        )
        
        with self.lock:
            self.task_info[task_id] = task
        
        with self.stats_lock:
            self.stats["total_tasks_submitted"] += 1
            self.stats["active_tasks"] += 1
            self.stats["pending_tasks"] = self.task_queue.qsize()
        
        self.task_queue.put((-priority.value, task_id, task))
        
        logger.debug(f"任务已提交: {task_id}, 优先级: {priority.name}")
        return task_id
    
    def submit_batch_tasks(self, tasks: List[Tuple[Callable, Tuple, Dict, TaskPriority]]) -> List[str]:
        """批量提交任务"""
        task_ids = []
        for func, args, kwargs, priority in tasks:
            task_id = self.submit_task(func, *args, **kwargs, priority=priority)
            task_ids.append(task_id)
        return task_ids
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        with self.lock:
            task = self.task_info.get(task_id)
            if not task:
                return None
            
            return {
                "task_id": task.task_id,
                "status": task.status,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "priority": task.priority.name,
                "result": task.result,
                "error": str(task.error) if task.error else None,
                "duration": task.completed_at - task.started_at if task.started_at and task.completed_at else None
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.lock:
            task = self.task_info.get(task_id)
            if not task or task.status != "pending":
                return False
            
            task.status = "cancelled"
            self.task_info.pop(task_id, None)
        
        with self.stats_lock:
            self.stats["total_tasks_cancelled"] += 1
            self.stats["active_tasks"] -= 1
        
        logger.info(f"任务已取消: {task_id}")
        return True
    
    def _update_thread_status(self, thread_name: str, status: ThreadStatus):
        """更新线程状态"""
        with self.lock:
            for info in self.thread_info.values():
                if info.name == thread_name:
                    info.status = status
                    info.last_active_time = time.time()
                    break
    
    def get_thread_status(self, thread_name: str = None) -> Dict:
        """获取线程状态"""
        with self.lock:
            if thread_name:
                for info in self.thread_info.values():
                    if info.name == thread_name:
                        return {
                            "thread_id": info.thread_id,
                            "name": info.name,
                            "status": info.status.value,
                            "current_task": info.current_task,
                            "total_tasks": info.total_tasks,
                            "completed_tasks": info.completed_tasks,
                            "error_count": info.error_count,
                            "avg_task_time": info.avg_task_time,
                            "start_time": info.start_time,
                            "last_active_time": info.last_active_time
                        }
                return {}
            else:
                return {
                    info.name: {
                        "thread_id": info.thread_id,
                        "name": info.name,
                        "status": info.status.value,
                        "current_task": info.current_task,
                        "total_tasks": info.total_tasks,
                        "completed_tasks": info.completed_tasks,
                        "error_count": info.error_count,
                        "avg_task_time": info.avg_task_time
                    }
                    for info in self.thread_info.values()
                }
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self._update_stats()
                self._auto_scale()
                self._cleanup_completed_tasks()
                time.sleep(5)
            except Exception as e:
                logger.error(f"监控线程错误: {str(e)}")
                time.sleep(5)
    
    def _update_stats(self):
        """更新统计信息"""
        with self.lock:
            active_threads = sum(1 for info in self.thread_info.values() 
                               if info.status == ThreadStatus.RUNNING)
            
        with self.stats_lock:
            self.stats["current_workers"] = active_threads
            self.stats["pending_tasks"] = self.task_queue.qsize()
            if active_threads > self.stats["peak_workers"]:
                self.stats["peak_workers"] = active_threads
    
    def _auto_scale(self):
        """自动扩缩容"""
        with self.stats_lock:
            pending = self.stats["pending_tasks"]
            current = self.current_workers
        
        if pending > 100 and current < self.max_workers:
            new_workers = min(current + 2, self.max_workers)
            self._resize_pool(new_workers)
            logger.info(f"线程池扩容: {current} -> {new_workers}")
        
        elif pending < 10 and current > self.min_workers:
            new_workers = max(current - 1, self.min_workers)
            self._resize_pool(new_workers)
            logger.info(f"线程池缩容: {current} -> {new_workers}")
    
    def _resize_pool(self, new_size: int):
        """调整线程池大小"""
        self.current_workers = new_size
        
        with self.lock:
            current_count = len(self.thread_info)
            
            if new_size > current_count:
                for i in range(current_count, new_size):
                    thread_id = f"thread_{i}"
                    self.thread_info[thread_id] = ThreadInfo(
                        thread_id=thread_id,
                        name=f"tm_worker_{i}",
                        status=ThreadStatus.IDLE,
                        start_time=time.time()
                    )
                    
                    thread = threading.Thread(
                        target=self._worker_loop,
                        name=f"tm_worker_{i}",
                        daemon=True
                    )
                    thread.start()
            
            elif new_size < current_count:
                pass
    
    def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        with self.lock:
            completed_ids = [
                task_id for task_id, task in self.task_info.items()
                if task.status in ["completed", "failed", "cancelled"]
                and time.time() - task.created_at > 300
            ]
            
            for task_id in completed_ids:
                self.task_info.pop(task_id)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.stats_lock:
            return {
                "total_tasks_submitted": self.stats["total_tasks_submitted"],
                "total_tasks_completed": self.stats["total_tasks_completed"],
                "total_tasks_failed": self.stats["total_tasks_failed"],
                "total_tasks_cancelled": self.stats["total_tasks_cancelled"],
                "active_tasks": self.stats["active_tasks"],
                "pending_tasks": self.stats["pending_tasks"],
                "avg_task_duration": self.stats["avg_task_duration"],
                "peak_workers": self.stats["peak_workers"],
                "current_workers": self.stats["current_workers"],
                "max_workers": self.max_workers,
                "min_workers": self.min_workers,
                "error_count": len(self.stats["errors"])
            }
    
    def pause(self):
        """暂停线程管理器"""
        if self.status == PoolStatus.RUNNING:
            self.status = PoolStatus.PAUSED
            logger.info("线程管理器已暂停")
    
    def resume(self):
        """恢复线程管理器"""
        if self.status == PoolStatus.PAUSED:
            self.status = PoolStatus.RUNNING
            logger.info("线程管理器已恢复")
    
    def stop(self, wait: bool = True):
        """停止线程管理器"""
        if not self.is_running:
            logger.warning("线程管理器未运行")
            return
        
        self.status = PoolStatus.SHUTTING_DOWN
        self.is_running = False
        
        self.thread_pool.shutdown(wait=wait)
        
        self.status = PoolStatus.SHUTDOWN
        logger.info("线程管理器已停止")
    
    def wait_for_completion(self, timeout: Optional[float] = None):
        """等待所有任务完成"""
        self.task_queue.join()
    
    def execute_with_timeout(self, func: Callable, timeout: float, *args, **kwargs) -> Any:
        """带超时的任务执行"""
        future = self.thread_pool.submit(func, *args, **kwargs)
        
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise TimeoutError(f"任务超时: {timeout}秒")
    
    def map_tasks(self, func: Callable, iterable: List, timeout: Optional[float] = None) -> List:
        """批量执行任务"""
        results = []
        futures = []
        
        for item in iterable:
            future = self.thread_pool.submit(func, item)
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            try:
                results.append(future.result())
            except Exception as e:
                results.append(None)
        
        return results


def test_thread_manager():
    """测试线程管理器"""
    print("线程管理器 V2.0 测试")
    print("=" * 60)
    
    def test_task(task_id, duration=0.1):
        """测试任务"""
        time.sleep(duration)
        return f"result_{task_id}"
    
    def error_task():
        """错误任务"""
        raise ValueError("测试错误")
    
    tm = ThreadManager(max_workers=5, min_workers=2)
    tm.start()
    
    print("提交测试任务...")
    task_ids = []
    for i in range(10):
        duration = 0.1 * (i % 3 + 1)
        task_id = tm.submit_task(test_task, i, duration=duration)
        task_ids.append(task_id)
    
    print("提交错误任务...")
    error_task_id = tm.submit_task(error_task)
    task_ids.append(error_task_id)
    
    print(f"\n已提交 {len(task_ids)} 个任务")
    
    print("\n等待任务完成 (2秒)...")
    time.sleep(2)
    
    print("\n线程状态:")
    thread_status = tm.get_thread_status()
    for name, status in thread_status.items():
        print(f"  {name}: {status['status']}, 任务数: {status['total_tasks']}, 完成: {status['completed_tasks']}")
    
    print("\n统计信息:")
    stats = tm.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n任务状态检查:")
    for task_id in task_ids[:5]:
        status = tm.get_task_status(task_id)
        if status:
            print(f"  {task_id}: {status['status']}, 耗时: {status['duration']:.4f}s")
    
    print("\n测试批量任务提交...")
    batch_tasks = [
        (test_task, (100,), {}, TaskPriority.HIGH),
        (test_task, (101,), {}, TaskPriority.NORMAL),
        (test_task, (102,), {}, TaskPriority.LOW)
    ]
    batch_ids = tm.submit_batch_tasks(batch_tasks)
    print(f"批量提交 {len(batch_ids)} 个任务")
    
    time.sleep(0.5)
    
    print("\n测试带超时的任务...")
    try:
        result = tm.execute_with_timeout(test_task, 1.0, "timeout_test", duration=0.5)
        print(f"  超时任务成功: {result}")
    except TimeoutError as e:
        print(f"  超时任务失败: {e}")
    
    print("\n测试取消任务...")
    cancel_id = tm.submit_task(test_task, "cancel_test", duration=10)
    cancelled = tm.cancel_task(cancel_id)
    print(f"  任务取消: {'成功' if cancelled else '失败'}")
    
    print("\n停止线程管理器...")
    tm.stop()
    
    print("\n线程管理器 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_thread_manager()