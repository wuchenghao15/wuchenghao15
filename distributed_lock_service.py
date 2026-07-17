#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS分布式锁服务
提供分布式环境下的互斥锁功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print

class DistributedLock:
    """分布式锁"""
    
    def __init__(self, lock_id: str, name: str, holder: str = '',
                 acquired_at: float = None, timeout: float = 30.0,
                 renew_interval: float = 10.0):
        self.lock_id = lock_id
        self.name = name
        self.holder = holder
        self.acquired_at = acquired_at
        self.timeout = timeout
        self.renew_interval = renew_interval
        self._renew_thread = None
        self._stop_renew = False
    
    def is_expired(self) -> bool:
        """检查锁是否过期"""
        if self.acquired_at is None:
            return True
        return time.time() - self.acquired_at > self.timeout
    
    def start_renewal(self):
        """开始自动续期"""
        def renew():
            while not self._stop_renew:
                time.sleep(self.renew_interval)
                if self.acquired_at:
                    self.acquired_at = time.time()
                    distributed_lock_service._update_lock(self.lock_id, self.acquired_at)
        
        self._renew_thread = threading.Thread(target=renew, daemon=True)
        self._renew_thread.start()
    
    def stop_renewal(self):
        """停止自动续期"""
        self._stop_renew = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'lock_id': self.lock_id,
            'name': self.name,
            'holder': self.holder,
            'acquired_at': self.acquired_at,
            'timeout': self.timeout,
            'is_expired': self.is_expired(),
            'remaining_time': max(0, self.timeout - (time.time() - self.acquired_at)) if self.acquired_at else 0
        }

class LockAcquireError(Exception):
    """锁获取失败异常"""
    pass

class DistributedLockService:
    """分布式锁服务"""
    
    def __init__(self):
        self.locks: Dict[str, DistributedLock] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS distributed_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lock_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    holder TEXT,
                    acquired_at REAL,
                    timeout REAL DEFAULT 30.0,
                    renew_interval REAL DEFAULT 10.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    released_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lock_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lock_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    holder TEXT,
                    action TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_distributed_locks_id ON distributed_locks(lock_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_distributed_locks_name ON distributed_locks(name)
            ''')
            
            conn.commit()
            conn.close()
            
            self._load_locks_from_db()
        except Exception as e:
            logger(f"[锁] 初始化数据库失败: {e}")
    
    def _load_locks_from_db(self):
        """从数据库加载锁"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM distributed_locks WHERE released_at IS NULL')
            
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                lock = DistributedLock(
                    lock_id=data['lock_id'],
                    name=data['name'],
                    holder=data['holder'],
                    acquired_at=data['acquired_at'],
                    timeout=data['timeout'],
                    renew_interval=data['renew_interval']
                )
                
                if not lock.is_expired():
                    lock.start_renewal()
                    self.locks[data['lock_id']] = lock
            
            conn.close()
        except Exception as e:
            logger(f"[锁] 加载锁失败: {e}")
    
    def _generate_lock_id(self) -> str:
        """生成锁ID"""
        import uuid
        return str(uuid.uuid4())
    
    def acquire(self, name: str, holder: str = '', timeout: float = 30.0,
                renew_interval: float = 10.0, wait_timeout: float = 0.0) -> str:
        """获取锁"""
        lock_id = self._generate_lock_id()
        
        start_time = time.time()
        
        while True:
            with self.lock:
                existing_lock = None
                
                for lock in self.locks.values():
                    if lock.name == name and not lock.is_expired():
                        existing_lock = lock
                        break
                
                if existing_lock:
                    if wait_timeout > 0 and time.time() - start_time >= wait_timeout:
                        raise LockAcquireError(f"锁 {name} 获取超时")
                    time.sleep(0.1)
                    continue
                
                lock = DistributedLock(
                    lock_id=lock_id,
                    name=name,
                    holder=holder,
                    acquired_at=time.time(),
                    timeout=timeout,
                    renew_interval=renew_interval
                )
                
                self.locks[lock_id] = lock
            
            lock.start_renewal()
            self._save_lock_to_db(lock)
            self._log_lock_action(lock_id, name, holder, 'acquired')
            
            logger(f"[锁] 获取锁: {name}")
            
            return lock_id
    
    def _save_lock_to_db(self, lock: DistributedLock):
        """保存锁到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO distributed_locks 
                (lock_id, name, holder, acquired_at, timeout, renew_interval)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                lock.lock_id, lock.name, lock.holder,
                lock.acquired_at, lock.timeout, lock.renew_interval
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[锁] 保存锁失败: {e}")
    
    def _update_lock(self, lock_id: str, acquired_at: float):
        """更新锁"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE distributed_locks SET acquired_at = ? WHERE lock_id = ?
            ''', (acquired_at, lock_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[锁] 更新锁失败: {e}")
    
    def _log_lock_action(self, lock_id: str, name: str, holder: str, action: str):
        """记录锁操作"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO lock_history (lock_id, name, holder, action)
                VALUES (?, ?, ?, ?)
            ''', (lock_id, name, holder, action))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[锁] 记录操作失败: {e}")
    
    def release(self, lock_id: str) -> bool:
        """释放锁"""
        with self.lock:
            if lock_id not in self.locks:
                logger(f"[锁] 锁不存在: {lock_id}")
                return False
            
            lock = self.locks[lock_id]
            lock.stop_renewal()
            del self.locks[lock_id]
        
        self._release_lock_in_db(lock_id)
        self._log_lock_action(lock_id, lock.name, lock.holder, 'released')
        
        logger(f"[锁] 释放锁: {lock.name}")
        
        return True
    
    def _release_lock_in_db(self, lock_id: str):
        """在数据库中释放锁"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE distributed_locks SET released_at = ? WHERE lock_id = ?
            ''', (datetime.now().isoformat(), lock_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[锁] 释放锁失败: {e}")
    
    def try_acquire(self, name: str, holder: str = '',
                    timeout: float = 30.0) -> Optional[str]:
        """尝试获取锁（非阻塞）"""
        try:
            return self.acquire(name, holder, timeout, wait_timeout=0)
        except LockAcquireError:
            return None
    
    def is_locked(self, name: str) -> bool:
        """检查锁是否被持有"""
        with self.lock:
            for lock in self.locks.values():
                if lock.name == name and not lock.is_expired():
                    return True
        return False
    
    def get_lock(self, lock_id: str) -> Optional[DistributedLock]:
        """获取锁信息"""
        return self.locks.get(lock_id)
    
    def get_locks(self) -> List[DistributedLock]:
        """获取所有锁"""
        return list(self.locks.values())
    
    def get_lock_history(self, name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取锁操作历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM lock_history WHERE 1=1'
            params = []
            
            if name:
                query += ' AND name = ?'
                params.append(name)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            history = []
            
            for row in cursor.fetchall():
                history.append(dict(zip(columns, row)))
            
            conn.close()
            return history
        except Exception as e:
            logger(f"[锁] 获取锁历史失败: {e}")
            return []
    
    def release_all(self):
        """释放所有锁"""
        with self.lock:
            for lock_id in list(self.locks.keys()):
                lock = self.locks[lock_id]
                lock.stop_renewal()
                del self.locks[lock_id]
                self._release_lock_in_db(lock_id)
        
        logger(f"[锁] 释放所有锁")
    
    def cleanup_expired(self):
        """清理过期锁"""
        expired = []
        
        with self.lock:
            for lock_id, lock in self.locks.items():
                if lock.is_expired():
                    expired.append(lock_id)
            
            for lock_id in expired:
                lock = self.locks[lock_id]
                lock.stop_renewal()
                del self.locks[lock_id]
        
        logger(f"[锁] 清理过期锁: {len(expired)} 个")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_locks': len(self.locks),
            'active_locks': sum(1 for l in self.locks.values() if not l.is_expired()),
            'expired_locks': sum(1 for l in self.locks.values() if l.is_expired())
        }
    
    def start(self):
        """启动分布式锁服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self._start_cleanup_thread()
        logger(f"[锁] 分布式锁服务已启动")
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup():
            while self.is_running:
                time.sleep(60)
                self.cleanup_expired()
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def stop(self):
        """停止分布式锁服务"""
        self.is_running = False
        self.release_all()
        logger(f"[锁] 分布式锁服务已停止")

distributed_lock_service = DistributedLockService()
