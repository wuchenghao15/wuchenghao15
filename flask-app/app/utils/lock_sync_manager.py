# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
互锁同步异步管理器
支持分布式锁、读写锁、同步/异步操作和并发控制
"""

import threading
import time
import uuid
import asyncio
import queue
from typing import Dict, List, Optional, Any, Callable, Set, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from functools import wraps
from contextlib import contextmanager

from app.utils.logging import logger
from app.utils.db import db_manager
import logging


class LockType(Enum):
    """锁类型"""
    READ = "read"
    WRITE = "write"
    EXCLUSIVE = "exclusive"


@dataclass
class LockInfo:
    """锁信息"""
    lock_id: str
    resource: str
    lock_type: LockType
    owner: str
    acquired_at: float
    expires_at: float
    is_held: bool = True


class ReadWriteLock:
    """读写锁 - 允许多个读者或一个写者"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._read_ready = threading.Condition(self._lock)
        self._readers = 0
        self._writers_waiting = 0
        self._writer_active = False
        self._write_lock_owner: Optional[str] = None

    def acquire_read(self, timeout: Optional[float] = None) -> bool:
        """获取读锁"""
        start_time = time.time()
        with self._read_ready:
            while self._writer_active or self._writers_waiting > 0:
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False
                    remaining = timeout - elapsed
                    self._read_ready.wait(remaining)
                else:
                    self._read_ready.wait()
            self._readers += 1
        return True

    def release_read(self):
        """释放读锁"""
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self, timeout: Optional[float] = None, owner: Optional[str] = None) -> bool:
        """获取写锁"""
        start_time = time.time()
        with self._read_ready:
            self._writers_waiting += 1
            try:
                while self._readers > 0 or self._writer_active:
                    if timeout is not None:
                        elapsed = time.time() - start_time
                        if elapsed >= timeout:
                            return False
                        remaining = timeout - elapsed
                        self._read_ready.wait(remaining)
                    else:
                        self._read_ready.wait()
                self._writer_active = True
                self._write_lock_owner = owner
            finally:
                self._writers_waiting -= 1
        return True

    def release_write(self):
        """释放写锁"""
        with self._read_ready:
            self._writer_active = False
            self._write_lock_owner = None
            self._read_ready.notify_all()

    @contextmanager
    def read_lock(self, timeout: Optional[float] = None):
        """读锁上下文管理器"""
        acquired = self.acquire_read(timeout)
        if not acquired:
            raise TimeoutError("Failed to acquire read lock")
        try:
            yield
        finally:
            self.release_read()

    @contextmanager
    def write_lock(self, timeout: Optional[float] = None, owner: Optional[str] = None):
        """写锁上下文管理器"""
        acquired = self.acquire_write(timeout, owner)
        if not acquired:
            raise TimeoutError("Failed to acquire write lock")
        try:
            yield
        finally:
            self.release_write()


class DistributedLock:
    """分布式锁 - 基于数据库实现"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self._local_locks: Dict[str, threading.Lock] = {}
        self._lock_creation_lock = threading.Lock()
        self._init_lock_table()

    def _init_lock_table(self):
        """初始化锁表"""
        try:
            query = """CREATE TABLE IF NOT EXISTS distributed_locks (
                lock_id TEXT PRIMARY KEY,
                resource TEXT NOT NULL,
                owner TEXT NOT NULL,
                acquired_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                UNIQUE(resource)
            )"""
            self.db.execute(query)
        except Exception as e:
            logger.warning(f"初始化锁表失败: {str(e)}")

    def _get_local_lock(self, resource: str) -> threading.Lock:
        """获取本地锁"""
        with self._lock_creation_lock:
            if resource not in self._local_locks:
                self._local_locks[resource] = threading.Lock()
            return self._local_locks[resource]

    def acquire(self, resource: str, owner: Optional[str] = None, 
                ttl: float = 30.0, timeout: Optional[float] = None) -> Optional[str]:
        """获取分布式锁"""
        if not owner:
            owner = f"process_{uuid.uuid4().hex[:8]}"
        
        lock_id = str(uuid.uuid4())
        acquired_at = time.time()
        expires_at = acquired_at + ttl
        
        start_time = time.time()
        
        while True:
            # 先获取本地锁以防止竞态条件
            local_lock = self._get_local_lock(resource)
            if not local_lock.acquire(blocking=False):
                if timeout is not None and time.time() - start_time >= timeout:
                    return None
                time.sleep(0.01)
                continue
            
            try:
                # 检查是否有有效的锁
                query = """SELECT lock_id, owner, expires_at FROM distributed_locks 
                          WHERE resource = ?"""
                result = self.db.fetch_one(query, (resource,))
                
                if result:
                    # 有现有锁
                    if isinstance(result, dict):
                        existing_expires = result.get('expires_at', 0)
                        existing_owner = result.get('owner', '')
                    else:
                        existing_expires = result[2] if len(result) > 2 else 0
                        existing_owner = result[1] if len(result) > 1 else ''
                    
                    # 检查是否过期
                    if existing_expires > time.time():
                        # 锁仍然有效
                        if existing_owner == owner:
                            # 同一所有者,更新过期时间
                            query = """UPDATE distributed_locks 
                                      SET expires_at = ?, acquired_at = ?
                                      WHERE resource = ? AND owner = ?"""
                            self.db.execute(query, (expires_at, acquired_at, resource, owner))
                            return lock_id
                        
                        # 等待锁释放
                        if timeout is not None and time.time() - start_time >= timeout:
                            return None
                        time.sleep(0.1)
                        continue
                
                # 尝试获取锁
                try:
                    query = """INSERT OR REPLACE INTO distributed_locks 
                              (lock_id, resource, owner, acquired_at, expires_at)
                              VALUES (?, ?, ?, ?, ?)"""
                    self.db.execute(query, (lock_id, resource, owner, acquired_at, expires_at))
                    logger.debug(f"获取分布式锁: {resource} (owner: {owner})")
                    return lock_id
                except Exception as e:
                    logger.debug(f"获取锁失败: {str(e)}")
                    if timeout is not None and time.time() - start_time >= timeout:
                        return None
                    time.sleep(0.1)
            finally:
                local_lock.release()

    def release(self, lock_id: str) -> bool:
        """释放分布式锁"""
        try:
            query = "DELETE FROM distributed_locks WHERE lock_id = ?"
            self.db.execute(query, (lock_id,))
            logger.debug(f"释放分布式锁: {lock_id}")
            return True
        except Exception as e:
            logger.error(f"释放锁失败: {str(e)}")
            return False

    def refresh(self, lock_id: str, ttl: float = 30.0) -> bool:
        """刷新锁的过期时间"""
        try:
            expires_at = time.time() + ttl
            query = """UPDATE distributed_locks 
                      SET expires_at = ?
                      WHERE lock_id = ?"""
            self.db.execute(query, (expires_at, lock_id))
            return True
        except Exception as e:
            logger.error(f"刷新锁失败: {str(e)}")
            return False

    def is_locked(self, resource: str) -> bool:
        """检查资源是否被锁定"""
        try:
            query = """SELECT expires_at FROM distributed_locks WHERE resource = ?"""
            result = self.db.fetch_one(query, (resource,))
            if result:
                if isinstance(result, dict):
                    expires = result.get('expires_at', 0)
                else:
                    expires = result[0] if result else 0
                return expires > time.time()
        except Exception:
            pass
        return False

    @contextmanager
    def lock(self, resource: str, owner: Optional[str] = None, 
             ttl: float = 30.0, timeout: Optional[float] = None):
        """分布式锁上下文管理器"""
        lock_id = self.acquire(resource, owner, ttl, timeout)
        if not lock_id:
            raise TimeoutError(f"Failed to acquire lock on {resource}")
        try:
            yield lock_id
        finally:
            self.release(lock_id)


class AsyncQueue:
    """异步任务队列"""
    
    def __init__(self, max_size: int = 1000):
        self._queue = queue.Queue(maxsize=max_size)
        self._workers: List[threading.Thread] = []
        self._running = False
        self._task_count = 0
        self._completed_count = 0
        self._lock = threading.Lock()

    def put(self, task: Callable, *args, **kwargs):
        """添加任务"""
        self._queue.put((task, args, kwargs))
        with self._lock:
            self._task_count += 1

    def start(self, worker_count: int = 4):
        """启动工作线程"""
        if self._running:
            return
        
        self._running = True
        for i in range(worker_count):
            worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"AsyncWorker-{i}")
            worker.start()
            self._workers.append(worker)
        logger.info(f"异步队列启动, {worker_count} 个工作线程")

    def stop(self, wait: bool = True):
        """停止工作线程"""
        self._running = False
        if wait:
            for worker in self._workers:
                worker.join(timeout=5.0)
        self._workers.clear()
        logger.info("异步队列停止")

    def _worker_loop(self):
        """工作线程循环"""
        while self._running:
            try:
                task, args, kwargs = self._queue.get(timeout=0.1)
                try:
                    task(*args, **kwargs)
                except Exception as e:
                    logger.error(f"异步任务执行失败: {str(e)}")
                finally:
                    self._queue.task_done()
                    with self._lock:
                        self._completed_count += 1
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程异常: {str(e)}")

    def wait_completion(self):
        """等待所有任务完成"""
        self._queue.join()

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        with self._lock:
            return {
                'pending': self._queue.qsize(),
                'total': self._task_count,
                'completed': self._completed_count
            }


class SyncAsyncManager:
    """同步异步管理器"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self._rw_locks: Dict[str, ReadWriteLock] = {}
        self._rw_lock_creation = threading.Lock()
        self._distributed_lock = DistributedLock(db_manager)
        self._async_queue = AsyncQueue()
        self._operation_history: List[Dict] = []
        self._history_lock = threading.Lock()
        self._max_history = 1000

    def _get_rw_lock(self, resource: str) -> ReadWriteLock:
        """获取读写锁"""
        with self._rw_lock_creation:
            if resource not in self._rw_locks:
                self._rw_locks[resource] = ReadWriteLock()
            return self._rw_locks[resource]

    @contextmanager
    def read_lock(self, resource: str, timeout: Optional[float] = None, 
                  distributed: bool = False):
        """读锁 - 支持本地和分布式"""
        rw_lock = self._get_rw_lock(resource)
        
        if distributed:
            dist_lock_id = None
            try:
                dist_lock_id = self._distributed_lock.acquire(
                    f"{resource}:read", timeout=timeout
                )
                if not dist_lock_id:
                    raise TimeoutError("Failed to acquire distributed read lock")
                
                with rw_lock.read_lock(timeout):
                    yield
            finally:
                if dist_lock_id:
                    self._distributed_lock.release(dist_lock_id)
        else:
            with rw_lock.read_lock(timeout):
                yield

    @contextmanager
    def write_lock(self, resource: str, timeout: Optional[float] = None,
                   distributed: bool = False, owner: Optional[str] = None):
        """写锁 - 支持本地和分布式"""
        rw_lock = self._get_rw_lock(resource)
        
        if distributed:
            dist_lock_id = None
            try:
                dist_lock_id = self._distributed_lock.acquire(
                    f"{resource}:write", owner=owner, timeout=timeout
                )
                if not dist_lock_id:
                    raise TimeoutError("Failed to acquire distributed write lock")
                
                with rw_lock.write_lock(timeout, owner):
                    yield dist_lock_id
            finally:
                if dist_lock_id:
                    self._distributed_lock.release(dist_lock_id)
        else:
            with rw_lock.write_lock(timeout, owner):
                yield None

    def execute_sync(self, func: Callable, resource: Optional[str] = None,
                    lock_type: LockType = LockType.EXCLUSIVE,
                    *args, **kwargs) -> Any:
        """同步执行 - 带锁保护"""
        start_time = time.time()
        result = None
        success = False
        
        try:
            if resource:
                if lock_type == LockType.READ:
                    with self.read_lock(resource):
                        result = func(*args, **kwargs)
                else:
                    with self.write_lock(resource):
                        result = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            success = True
        finally:
            self._record_operation(
                'sync', func.__name__ if hasattr(func, '__name__') else str(func),
                resource, lock_type, success, time.time() - start_time
            )
        
        return result

    def execute_async(self, func: Callable, resource: Optional[str] = None,
                     lock_type: LockType = LockType.EXCLUSIVE,
                     callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None,
                     *args, **kwargs):
        """异步执行 - 带锁保护"""
        
        def wrapped():
            start_time = time.time()
            success = False
            try:
                if resource:
                    if lock_type == LockType.READ:
                        with self.read_lock(resource):
                            result = func(*args, **kwargs)
                    else:
                        with self.write_lock(resource):
                            result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                success = True
                
                if callback:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"回调执行失败: {str(e)}")
                
                return result
            except Exception as e:
                logger.error(f"异步任务失败: {str(e)}")
                if error_callback:
                    try:
                        error_callback(e)
                    except Exception as ce:
                        logger.error(f"错误回调执行失败: {str(ce)}")
            finally:
                self._record_operation(
                    'async', func.__name__ if hasattr(func, '__name__') else str(func),
                    resource, lock_type, success, time.time() - start_time
                )
        
        self._async_queue.put(wrapped)

    def start_async_workers(self, count: int = 4):
        """启动异步工作线程"""
        self._async_queue.start(count)

    def stop_async_workers(self):
        """停止异步工作线程"""
        self._async_queue.stop()

    def wait_async_completion(self):
        """等待异步任务完成"""
        self._async_queue.wait_completion()

    def _record_operation(self, op_type: str, func_name: str,
                         resource: Optional[str], lock_type: LockType,
                         success: bool, duration: float):
        """记录操作历史"""
        with self._history_lock:
            self._operation_history.append({
                'type': op_type,
                'function': func_name,
                'resource': resource,
                'lock_type': lock_type.value,
                'success': success,
                'duration': duration,
                'timestamp': time.time()
            })
            
            if len(self._operation_history) > self._max_history:
                self._operation_history = self._operation_history[-self._max_history:]

    def get_operation_stats(self) -> Dict:
        """获取操作统计"""
        with self._history_lock:
            if not self._operation_history:
                return {}
            
            sync_count = sum(1 for op in self._operation_history if op['type'] == 'sync')
            async_count = sum(1 for op in self._operation_history if op['type'] == 'async')
            success_count = sum(1 for op in self._operation_history if op['success'])
            avg_duration = sum(op['duration'] for op in self._operation_history) / len(self._operation_history)
            
            return {
                'total': len(self._operation_history),
                'sync': sync_count,
                'async': async_count,
                'success_rate': success_count / len(self._operation_history),
                'avg_duration_ms': avg_duration * 1000,
                'queue_stats': self._async_queue.get_stats()
            }

    def get_distributed_lock(self) -> DistributedLock:
        """获取分布式锁实例"""
        return self._distributed_lock


# 装饰器
def synchronized(resource: Optional[str] = None, lock_type: LockType = LockType.EXCLUSIVE):
    """同步装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = lock_sync_manager
            return manager.execute_sync(func, resource, lock_type, *args, **kwargs)
        return wrapper
    return decorator


def async_synchronized(resource: Optional[str] = None, lock_type: LockType = LockType.EXCLUSIVE,
                      callback: Optional[Callable] = None):
    """异步同步装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            manager = lock_sync_manager
            manager.execute_async(func, resource, lock_type, callback, *args, **kwargs)
        return wrapper
    return decorator


# 创建全局实例
lock_sync_manager = SyncAsyncManager()
distributed_lock = DistributedLock()
