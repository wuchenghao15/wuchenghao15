#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS健康检查服务
提供细粒度的健康检查和探针功能
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


class HealthCheck:
    """健康检查项"""

    def __init__(self, check_id: str, name: str, check_func: Callable,
                 interval: int = 30, timeout: int = 10,
                 healthy_threshold: int = 2, unhealthy_threshold: int = 3,
                 enabled: bool = True, category: str = 'system'):
        self.check_id = check_id
        self.name = name
        self.check_func = check_func
        self.interval = interval
        self.timeout = timeout
        self.healthy_threshold = healthy_threshold
        self.unhealthy_threshold = unhealthy_threshold
        self.enabled = enabled
        self.category = category
        self.status = 'unknown'
        self.consecutive_success = 0
        self.consecutive_failure = 0
        self.last_check = None
        self.last_result = None
        self.last_error = None
        self.response_time = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'check_id': self.check_id,
            'name': self.name,
            'interval': self.interval,
            'timeout': self.timeout,
            'enabled': self.enabled,
            'category': self.category,
            'status': self.status,
            'consecutive_success': self.consecutive_success,
            'consecutive_failure': self.consecutive_failure,
            'last_check': self.last_check,
            'last_error': self.last_error,
            'response_time': round(self.response_time, 3)
        }


class HealthCheckService:
    """健康检查服务"""

    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.is_running = False
        self.check_thread = None
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_checks()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    category TEXT DEFAULT 'system',
                    interval INTEGER DEFAULT 30,
                    timeout INTEGER DEFAULT 10,
                    enabled INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'unknown',
                    last_check TEXT,
                    last_error TEXT,
                    response_time REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_check_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_time REAL,
                    error_message TEXT,
                    checked_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_health_checks_id ON health_checks(check_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_health_check_history_check ON health_check_history(check_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[健康] 初始化数据库失败: {e}")

    def _register_default_checks(self):
        """注册默认健康检查"""
        self.register_check('db_connection', '数据库连接', self._check_database,
                           interval=30, category='database')
        self.register_check('disk_space', '磁盘空间', self._check_disk_space,
                           interval=60, category='system')
        self.register_check('memory_usage', '内存使用', self._check_memory,
                           interval=30, category='system')
        self.register_check('cpu_usage', 'CPU使用率', self._check_cpu,
                           interval=30, category='system')
        self.register_check('app_response', '应用响应', self._check_app_response,
                           interval=15, category='application')
        self.register_check('cache_connection', '缓存连接', self._check_cache,
                           interval=30, category='cache')

    def _check_database(self) -> bool:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            return True
        except:
            return False

    def _check_disk_space(self) -> bool:
        try:
            stat = os.statvfs('.')
            free_space = stat.f_bavail * stat.f_frsize
            total_space = stat.f_blocks * stat.f_frsize
            usage = (1 - free_space / total_space) * 100
            return usage < 90
        except:
            return False

    def _check_memory(self) -> bool:
        try:
            import psutil
            mem = psutil.virtual_memory()
            return mem.percent < 90
        except:
            return True

    def _check_cpu(self) -> bool:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            return cpu < 90
        except:
            return True

    def _check_app_response(self) -> bool:
        return True

    def _check_cache(self) -> bool:
        return True

    def register_check(self, check_id: str, name: str, check_func: Callable,
                       interval: int = 30, timeout: int = 10,
                       healthy_threshold: int = 2, unhealthy_threshold: int = 3,
                       enabled: bool = True, category: str = 'system') -> str:
        check = HealthCheck(
            check_id=check_id,
            name=name,
            check_func=check_func,
            interval=interval,
            timeout=timeout,
            healthy_threshold=healthy_threshold,
            unhealthy_threshold=unhealthy_threshold,
            enabled=enabled,
            category=category
        )

        with self.lock:
            self.checks[check_id] = check

        self._save_check_to_db(check)
        logger(f"[健康] 注册检查: {name}")

        return check_id

    def _save_check_to_db(self, check: HealthCheck):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO health_checks
                (check_id, name, category, interval, timeout, enabled, status, last_check)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                check.check_id, check.name, check.category,
                check.interval, check.timeout,
                1 if check.enabled else 0,
                check.status, check.last_check
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[健康] 保存检查失败: {e}")

    def remove_check(self, check_id: str) -> bool:
        with self.lock:
            if check_id not in self.checks:
                return False
            del self.checks[check_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM health_checks WHERE check_id = ?', (check_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[健康] 删除检查失败: {e}")

        return True

    def _run_check(self, check: HealthCheck):
        """执行单个检查"""
        start_time = time.time()

        try:
            result = check.check_func()
            check.response_time = time.time() - start_time
            check.last_check = datetime.now().isoformat()
            check.last_error = None

            if result:
                check.consecutive_success += 1
                check.consecutive_failure = 0

                if check.consecutive_success >= check.healthy_threshold:
                    check.status = 'healthy'
            else:
                check.consecutive_failure += 1
                check.consecutive_success = 0
                check.last_error = '检查返回False'

                if check.consecutive_failure >= check.unhealthy_threshold:
                    check.status = 'unhealthy'

        except Exception as e:
            check.response_time = time.time() - start_time
            check.last_check = datetime.now().isoformat()
            check.last_error = str(e)
            check.consecutive_failure += 1
            check.consecutive_success = 0

            if check.consecutive_failure >= check.unhealthy_threshold:
                check.status = 'unhealthy'

        check.last_result = check.status
        self._update_check_in_db(check)
        self._log_check_history(check)

    def _update_check_in_db(self, check: HealthCheck):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE health_checks
                SET status = ?, last_check = ?, last_error = ?, response_time = ?
                WHERE check_id = ?
            ''', (
                check.status, check.last_check,
                check.last_error, check.response_time,
                check.check_id
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[健康] 更新检查失败: {e}")

    def _log_check_history(self, check: HealthCheck):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO health_check_history
                (check_id, name, status, response_time, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                check.check_id, check.name, check.status,
                check.response_time, check.last_error
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[健康] 记录历史失败: {e}")

    def _check_loop(self):
        """检查循环"""
        last_run: Dict[str, float] = {}

        while self.is_running:
            now = time.time()

            with self.lock:
                checks_to_run = [
                    check for check in self.checks.values()
                    if check.enabled and
                    now - last_run.get(check.check_id, 0) >= check.interval
                ]

            for check in checks_to_run:
                thread = threading.Thread(target=self._run_check, args=(check,), daemon=True)
                thread.start()
                last_run[check.check_id] = now

            time.sleep(5)

    def run_check_now(self, check_id: str) -> bool:
        with self.lock:
            check = self.checks.get(check_id)
            if not check:
                return False

        self._run_check(check)
        return True

    def run_all_checks(self):
        with self.lock:
            checks = list(self.checks.values())

        for check in checks:
            if check.enabled:
                self._run_check(check)

    def get_check(self, check_id: str) -> Optional[HealthCheck]:
        return self.checks.get(check_id)

    def get_checks(self, category: str = None, enabled_only: bool = False) -> List[HealthCheck]:
        with self.lock:
            checks = list(self.checks.values())

            if category:
                checks = [c for c in checks if c.category == category]
            if enabled_only:
                checks = [c for c in checks if c.enabled]

            return checks

    def get_overall_status(self) -> Dict[str, Any]:
        with self.lock:
            total = len(self.checks)
            healthy = sum(1 for c in self.checks.values() if c.status == 'healthy')
            unhealthy = sum(1 for c in self.checks.values() if c.status == 'unhealthy')
            unknown = sum(1 for c in self.checks.values() if c.status == 'unknown')

            if unhealthy > 0:
                status = 'unhealthy'
            elif unknown > 0:
                status = 'degraded'
            else:
                status = 'healthy'

            return {
                'overall_status': status,
                'total_checks': total,
                'healthy': healthy,
                'unhealthy': unhealthy,
                'unknown': unknown,
                'healthy_rate': round(healthy / max(1, total) * 100, 2)
            }

    def get_check_history(self, check_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM health_check_history WHERE 1=1'
            params = []

            if check_id:
                query += ' AND check_id = ?'
                params.append(check_id)

            query += ' ORDER BY checked_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return history
        except Exception as e:
            logger(f"[健康] 获取历史失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            **self.get_overall_status()
        }

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        self.check_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.check_thread.start()
        logger(f"[健康] 健康检查服务已启动")

    def stop(self):
        self.is_running = False
        if self.check_thread:
            self.check_thread.join()
        logger(f"[健康] 健康检查服务已停止")


health_check_service = HealthCheckService()
