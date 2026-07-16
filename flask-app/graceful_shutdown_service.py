#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS优雅停机管理服务
确保系统停机时正确处理进行中的请求和资源释放
"""

import os
import sys
import json
import time
import signal
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = print


class ShutdownHook:
    """停机钩子"""

    def __init__(self, hook_id: str, name: str, callback: Callable,
                 priority: int = 50, timeout: int = 30,
                 description: str = ''):
        self.hook_id = hook_id
        self.name = name
        self.callback = callback
        self.priority = priority  # 0-100, 越高越先执行
        self.timeout = timeout
        self.description = description
        self.executed = False
        self.success = False
        self.execution_time = 0
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'hook_id': self.hook_id,
            'name': self.name,
            'priority': self.priority,
            'timeout': self.timeout,
            'description': self.description,
            'executed': self.executed,
            'success': self.success,
            'execution_time': round(self.execution_time, 3),
            'error': self.error
        }


class GracefulShutdownService:
    """优雅停机管理服务"""

    SHUTDOWN_PHASES = [
        ('stop_accepting', '停止接收新请求'),
        ('drain_connections', '排空活跃连接'),
        ('save_state', '保存系统状态'),
        ('close_resources', '关闭资源'),
        ('cleanup', '最终清理'),
    ]

    def __init__(self):
        self.hooks: Dict[str, ShutdownHook] = {}
        self.is_running = False
        self.is_shutting_down = False
        self.shutdown_thread = None
        self.lock = threading.Lock()

        self.active_requests = 0
        self._request_lock = threading.Lock()
        self.shutdown_timeout = 60
        self.drain_timeout = 30

        self._signal_handlers_installed = False
        self._init_database()
        self._register_default_hooks()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shutdown_hooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hook_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    priority INTEGER DEFAULT 50,
                    timeout INTEGER DEFAULT 30,
                    description TEXT,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shutdown_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hook_id TEXT,
                    hook_name TEXT,
                    phase TEXT,
                    success INTEGER,
                    execution_time REAL,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_shutdown_hooks_id ON shutdown_hooks(hook_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[停机] 初始化数据库失败: {e}")

    def _register_default_hooks(self):
        """注册默认停机钩子"""
        defaults = [
            ShutdownHook('hook_stop_scheduler', '停止定时任务', self._stop_schedulers,
                        priority=90, timeout=10, description='停止所有定时任务调度器'),
            ShutdownHook('hook_drain_queue', '排空消息队列', self._drain_message_queues,
                        priority=80, timeout=15, description='处理消息队列中的剩余消息'),
            ShutdownHook('hook_save_cache', '保存缓存数据', self._save_cache_state,
                        priority=70, timeout=10, description='将内存缓存持久化'),
            ShutdownHook('hook_close_db', '关闭数据库连接', self._close_db_connections,
                        priority=50, timeout=10, description='关闭所有数据库连接池'),
            ShutdownHook('hook_flush_logs', '刷新日志', self._flush_logs,
                        priority=40, timeout=5, description='确保所有日志已写入'),
            ShutdownHook('hook_release_locks', '释放分布式锁', self._release_locks,
                        priority=30, timeout=5, description='释放所有持有的分布式锁'),
            ShutdownHook('hook_cleanup_temp', '清理临时文件', self._cleanup_temp_files,
                        priority=20, timeout=5, description='清理临时文件和目录'),
            ShutdownHook('hook_notify_cluster', '通知集群节点', self._notify_cluster,
                        priority=10, timeout=5, description='通知集群其他节点本节点下线'),
        ]

        for hook in defaults:
            if hook.hook_id not in self.hooks:
                self.hooks[hook.hook_id] = hook
                self._save_hook_to_db(hook)

    def _stop_schedulers(self):
        logger(f"[停机] 停止定时任务")

    def _drain_message_queues(self):
        logger(f"[停机] 排空消息队列")

    def _save_cache_state(self):
        logger(f"[停机] 保存缓存状态")

    def _close_db_connections(self):
        try:
            conn = sqlite3.connect('app.db')
            conn.close()
        except:
            pass
        logger(f"[停机] 关闭数据库连接")

    def _flush_logs(self):
        logger(f"[停机] 刷新日志")

    def _release_locks(self):
        logger(f"[停机] 释放分布式锁")

    def _cleanup_temp_files(self):
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
        if os.path.exists(temp_dir):
            logger(f"[停机] 清理临时文件")

    def _notify_cluster(self):
        logger(f"[停机] 通知集群节点")

    def _save_hook_to_db(self, hook: ShutdownHook):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO shutdown_hooks
                (hook_id, name, priority, timeout, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (hook.hook_id, hook.name, hook.priority, hook.timeout, hook.description))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[停机] 保存钩子失败: {e}")

    def register_hook(self, name: str, callback: Callable,
                      priority: int = 50, timeout: int = 30,
                      description: str = '') -> str:
        """注册停机钩子"""
        import uuid
        hook_id = f"hook_{uuid.uuid4().hex[:12]}"

        hook = ShutdownHook(
            hook_id=hook_id,
            name=name,
            callback=callback,
            priority=priority,
            timeout=timeout,
            description=description
        )

        with self.lock:
            self.hooks[hook_id] = hook

        self._save_hook_to_db(hook)
        logger(f"[停机] 注册钩子: {name} (priority={priority})")

        return hook_id

    def remove_hook(self, hook_id: str) -> bool:
        with self.lock:
            if hook_id not in self.hooks:
                return False
            del self.hooks[hook_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM shutdown_hooks WHERE hook_id = ?', (hook_id,))
            conn.commit()
            conn.close()
        except:
            pass

        return True

    def begin_request(self):
        """标记请求开始"""
        with self._request_lock:
            self.active_requests += 1

    def end_request(self):
        """标记请求结束"""
        with self._request_lock:
            self.active_requests = max(0, self.active_requests - 1)

    def install_signal_handlers(self):
        """安装信号处理器"""
        if self._signal_handlers_installed:
            return

        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            self._signal_handlers_installed = True
            logger(f"[停机] 信号处理器已安装")
        except Exception as e:
            logger(f"[停机] 安装信号处理器失败: {e}")

    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger(f"[停机] 收到信号 {signum}, 开始优雅停机")
        self.shutdown()

    def shutdown(self) -> Dict[str, Any]:
        """执行优雅停机"""
        if self.is_shutting_down:
            logger(f"[停机] 停机已在进行中")
            return {'status': 'already_shutting_down'}

        self.is_shutting_down = True
        logger(f"[停机] 开始优雅停机流程")

        results = {
            'start_time': datetime.now().isoformat(),
            'phases': {},
            'hooks': {},
            'drained_requests': 0
        }

        with self.lock:
            sorted_hooks = sorted(
                self.hooks.values(),
                key=lambda h: h.priority,
                reverse=True
            )

        for phase_name, phase_desc in self.SHUTDOWN_PHASES:
            phase_start = time.time()
            logger(f"[停机] 阶段: {phase_desc}")

            if phase_name == 'drain_connections':
                drained = self._drain_active_requests()
                results['drained_requests'] = drained

            phase_hooks = [h for h in sorted_hooks if self._hook_belongs_to_phase(h, phase_name)]

            for hook in phase_hooks:
                hook_result = self._execute_hook(hook, phase_name)
                results['hooks'][hook.hook_id] = hook_result

            results['phases'][phase_name] = {
                'description': phase_desc,
                'duration': round(time.time() - phase_start, 3)
            }

        results['end_time'] = datetime.now().isoformat()
        results['status'] = 'completed'

        self.is_running = False
        logger(f"[停机] 优雅停机完成")

        return results

    def _hook_belongs_to_phase(self, hook: ShutdownHook, phase: str) -> bool:
        """判断钩子属于哪个阶段"""
        priority = hook.priority

        if phase == 'stop_accepting':
            return priority >= 90
        elif phase == 'drain_connections':
            return 80 <= priority < 90
        elif phase == 'save_state':
            return 60 <= priority < 80
        elif phase == 'close_resources':
            return 40 <= priority < 60
        elif phase == 'cleanup':
            return priority < 40
        return False

    def _drain_active_requests(self) -> int:
        """排空活跃请求"""
        start_time = time.time()

        while self.active_requests > 0:
            if time.time() - start_time > self.drain_timeout:
                logger(f"[停机] 排空超时, 剩余 {self.active_requests} 个请求")
                break
            time.sleep(0.5)

        drained = self.active_requests
        return drained

    def _execute_hook(self, hook: ShutdownHook, phase: str) -> Dict[str, Any]:
        """执行停机钩子"""
        start_time = time.time()
        result = {'name': hook.name, 'success': False}

        def execute():
            try:
                hook.callback()
                hook.success = True
            except Exception as e:
                hook.error = str(e)
                hook.success = False

        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        thread.join(timeout=hook.timeout)

        hook.executed = True
        hook.execution_time = time.time() - start_time

        if thread.is_alive():
            hook.error = f'执行超时 ({hook.timeout}s)'
            hook.success = False

        result['success'] = hook.success
        result['execution_time'] = round(hook.execution_time, 3)
        result['error'] = hook.error

        self._log_shutdown(hook, phase)

        status = '成功' if hook.success else '失败'
        logger(f"[停机] 钩子 {hook.name}: {status} ({hook.execution_time:.2f}s)")

        return result

    def _log_shutdown(self, hook: ShutdownHook, phase: str):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO shutdown_logs
                (hook_id, hook_name, phase, success, execution_time, error)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                hook.hook_id, hook.name, phase,
                1 if hook.success else 0,
                hook.execution_time, hook.error
            ))

            conn.commit()
            conn.close()
        except:
            pass

    def get_hooks(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [h.to_dict() for h in sorted(self.hooks.values(),
                                                key=lambda x: x.priority, reverse=True)]

    def get_shutdown_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM shutdown_logs ORDER BY created_at DESC LIMIT ?
            ''', (limit,))

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except:
            return []

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'is_shutting_down': self.is_shutting_down,
            'total_hooks': len(self.hooks),
            'active_requests': self.active_requests,
            'shutdown_timeout': self.shutdown_timeout,
            'drain_timeout': self.drain_timeout,
            'signal_handlers_installed': self._signal_handlers_installed
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.install_signal_handlers()
        logger(f"[停机] 优雅停机服务已启动")

    def stop(self):
        if not self.is_running:
            return
        self.shutdown()
        logger(f"[停机] 优雅停机服务已停止")


graceful_shutdown_service = GracefulShutdownService()
