#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS连接池服务
提供统一的数据库连接池管理
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from queue import Queue, Empty, Full

logger = print


class PooledConnection:
    """池化连接"""

    def __init__(self, conn_id: str, connection: Any, pool_name: str):
        self.conn_id = conn_id
        self.connection = connection
        self.pool_name = pool_name
        self.created_at = time.time()
        self.last_used = time.time()
        self.use_count = 0
        self.is_valid = True

    def touch(self):
        """更新使用时间"""
        self.last_used = time.time()
        self.use_count += 1

    def close(self):
        """关闭连接"""
        try:
            if self.connection:
                self.connection.close()
        except:
            pass
        self.is_valid = False


class ConnectionPool:
    """连接池"""

    def __init__(self, pool_name: str, db_type: str, config: Dict[str, Any]):
        self.pool_name = pool_name
        self.db_type = db_type
        self.config = config
        self.min_size = config.get('min_size', 2)
        self.max_size = config.get('max_size', 10)
        self.timeout = config.get('timeout', 30)
        self.max_lifetime = config.get('max_lifetime', 3600)
        self.idle_timeout = config.get('idle_timeout', 600)

        self._pool: Queue = Queue(maxsize=self.max_size)
        self._all_connections: Dict[str, PooledConnection] = {}
        self._lock = threading.Lock()
        self._connection_counter = 0

        self.total_created = 0
        self.total_borrowed = 0
        self.total_returned = 0
        self.total_errors = 0

        self._initialize()

    def _initialize(self):
        """初始化连接池"""
        for _ in range(self.min_size):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)

    def _create_connection(self) -> Optional[PooledConnection]:
        """创建连接"""
        try:
            self._connection_counter += 1
            conn_id = f"{self.pool_name}_conn_{self._connection_counter}"

            if self.db_type == 'sqlite':
                db_path = self.config.get('database', 'app.db')
                connection = sqlite3.connect(db_path, check_same_thread=False)
            elif self.db_type == 'mysql':
                try:
                    import pymysql
                    connection = pymysql.connect(
                        host=self.config.get('host', 'localhost'),
                        port=self.config.get('port', 3306),
                        user=self.config.get('user', 'root'),
                        password=self.config.get('password', ''),
                        database=self.config.get('database', ''),
                        charset='utf8mb4'
                    )
                except ImportError:
                    connection = sqlite3.connect('app.db', check_same_thread=False)
            elif self.db_type == 'postgresql':
                try:
                    import psycopg2
                    connection = psycopg2.connect(
                        host=self.config.get('host', 'localhost'),
                        port=self.config.get('port', 5432),
                        user=self.config.get('user', 'postgres'),
                        password=self.config.get('password', ''),
                        dbname=self.config.get('database', '')
                    )
                except ImportError:
                    connection = sqlite3.connect('app.db', check_same_thread=False)
            else:
                connection = sqlite3.connect('app.db', check_same_thread=False)

            pooled = PooledConnection(conn_id, connection, self.pool_name)
            self.total_created += 1

            with self._lock:
                self._all_connections[conn_id] = pooled

            return pooled
        except Exception as e:
            logger(f"[连接池] 创建连接失败 ({self.pool_name}): {e}")
            self.total_errors += 1
            return None

    def acquire(self, timeout: float = None) -> Optional[PooledConnection]:
        """获取连接"""
        timeout = timeout or self.timeout

        try:
            pooled = self._pool.get(timeout=timeout)
        except Empty:
            if len(self._all_connections) < self.max_size:
                pooled = self._create_connection()
                if not pooled:
                    return None
            else:
                logger(f"[连接池] 连接池已满 ({self.pool_name})")
                return None

        if not pooled or not pooled.is_valid:
            pooled = self._create_connection()
            if not pooled:
                return None

        if self._is_expired(pooled):
            pooled.close()
            pooled = self._create_connection()
            if not pooled:
                return None

        pooled.touch()
        self.total_borrowed += 1
        return pooled

    def release(self, pooled: PooledConnection):
        """释放连接"""
        if not pooled or not pooled.is_valid:
            return

        if self._is_expired(pooled):
            pooled.close()
            self._remove_connection(pooled.conn_id)
            return

        try:
            self._pool.put_nowait(pooled)
            self.total_returned += 1
        except Full:
            pooled.close()
            self._remove_connection(pooled.conn_id)

    def _is_expired(self, pooled: PooledConnection) -> bool:
        """检查连接是否过期"""
        if time.time() - pooled.created_at > self.max_lifetime:
            return True
        return False

    def _remove_connection(self, conn_id: str):
        """移除连接"""
        with self._lock:
            self._all_connections.pop(conn_id, None)

    def cleanup_idle(self):
        """清理空闲连接"""
        now = time.time()
        to_remove = []

        with self._lock:
            for conn_id, pooled in list(self._all_connections.items()):
                if now - pooled.last_used > self.idle_timeout:
                    if len(self._all_connections) > self.min_size:
                        to_remove.append(conn_id)

        for conn_id in to_remove:
            with self._lock:
                pooled = self._all_connections.get(conn_id)
            if pooled:
                pooled.close()
                self._remove_connection(conn_id)

    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for pooled in self._all_connections.values():
                pooled.close()
            self._all_connections.clear()

        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except Empty:
                break

    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        with self._lock:
            return {
                'pool_name': self.pool_name,
                'db_type': self.db_type,
                'min_size': self.min_size,
                'max_size': self.max_size,
                'current_size': len(self._all_connections),
                'available': self._pool.qsize(),
                'in_use': len(self._all_connections) - self._pool.qsize(),
                'total_created': self.total_created,
                'total_borrowed': self.total_borrowed,
                'total_returned': self.total_returned,
                'total_errors': self.total_errors
            }


class ConnectionPoolService:
    """连接池服务"""

    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.is_running = False
        self.cleanup_thread = None
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_pools()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_pools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_name TEXT NOT NULL UNIQUE,
                    db_type TEXT NOT NULL,
                    config TEXT,
                    min_size INTEGER DEFAULT 2,
                    max_size INTEGER DEFAULT 10,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_pool_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_name TEXT NOT NULL,
                    borrowed INTEGER DEFAULT 0,
                    returned INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[连接池] 初始化数据库失败: {e}")

    def _register_default_pools(self):
        """注册默认连接池"""
        defaults = [
            ('main_pool', 'sqlite', {'database': 'app.db', 'min_size': 2, 'max_size': 10}),
            ('log_pool', 'sqlite', {'database': 'app.db', 'min_size': 1, 'max_size': 5}),
            ('cache_pool', 'sqlite', {'database': 'app.db', 'min_size': 1, 'max_size': 5}),
            ('report_pool', 'sqlite', {'database': 'app.db', 'min_size': 1, 'max_size': 3}),
        ]

        for name, db_type, config in defaults:
            self.create_pool(name, db_type, config)

    def create_pool(self, pool_name: str, db_type: str,
                    config: Dict[str, Any] = None) -> bool:
        """创建连接池"""
        config = config or {}

        with self.lock:
            if pool_name in self.pools:
                return False

            pool = ConnectionPool(pool_name, db_type, config)
            self.pools[pool_name] = pool

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO connection_pools
                (pool_name, db_type, config, min_size, max_size)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                pool_name, db_type, json.dumps(config),
                config.get('min_size', 2), config.get('max_size', 10)
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[连接池] 保存池配置失败: {e}")

        logger(f"[连接池] 创建连接池: {pool_name} ({db_type})")
        return True

    def get_connection(self, pool_name: str = 'main_pool') -> Optional[PooledConnection]:
        """获取连接"""
        pool = self.pools.get(pool_name)
        if not pool:
            logger(f"[连接池] 连接池不存在: {pool_name}")
            return None

        return pool.acquire()

    def release_connection(self, pooled: PooledConnection):
        """释放连接"""
        pool = self.pools.get(pooled.pool_name)
        if pool:
            pool.release(pooled)

    def remove_pool(self, pool_name: str) -> bool:
        """移除连接池"""
        with self.lock:
            pool = self.pools.get(pool_name)
            if not pool:
                return False

            pool.close_all()
            del self.pools[pool_name]

        return True

    def get_pool_stats(self, pool_name: str = None) -> Dict[str, Any]:
        """获取连接池统计"""
        if pool_name:
            pool = self.pools.get(pool_name)
            if pool:
                return pool.get_stats()
            return {}
        else:
            return {name: pool.get_stats() for name, pool in self.pools.items()}

    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                time.sleep(120)

                for pool in self.pools.values():
                    pool.cleanup_idle()

            except Exception as e:
                logger(f"[连接池] 清理错误: {e}")

    def get_status(self) -> Dict[str, Any]:
        total_connections = sum(
            len(p._all_connections) for p in self.pools.values()
        )
        total_available = sum(p._pool.qsize() for p in self.pools.values())
        total_in_use = total_connections - total_available

        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_pools': len(self.pools),
            'total_connections': total_connections,
            'available_connections': total_available,
            'in_use_connections': total_in_use
        }

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger(f"[连接池] 连接池服务已启动")

    def stop(self):
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()

        for pool in self.pools.values():
            pool.close_all()

        logger(f"[连接池] 连接池服务已停止")


connection_pool_service = ConnectionPoolService()
