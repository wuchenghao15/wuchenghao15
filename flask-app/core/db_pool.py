#!/usr/bin/env python3
r"""数据库连接池 v2.0 - 由EigenFlux升级引擎生成r"""
import sqlite3
import threading
import queue
from contextlib import contextmanager

class DBConnectionPool:
    r"""SQLite连接池r"""
    def __init__(self, db_path, max_connections=20):
        self.db_path = db_path
        self._pool = queue.Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created = 0
        self._max = max_connections
        for _ in range(min(5, max_connections)):
            self._pool.put(self._create_conn())

    def _create_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute(r"PRAGMA journal_mode=WAL")
        conn.execute(r"PRAGMA busy_timeout=30000")
        with self._lock:
            self._created += 1
        return conn

    @contextmanager
    def get_conn(self):
        conn = None
        try:
            conn = self._pool.get(timeout=10)
            yield conn
        finally:
            if conn:
                self._pool.put(conn)

    def stats(self):
        return {r'pool_size': self._pool.qsize(), r'created': self._created, r'max': self._max}

_pool_instances = {}
def get_pool(db_path):
    if db_path not in _pool_instances:
        _pool_instances[db_path] = DBConnectionPool(db_path)
    return _pool_instances[db_path]
