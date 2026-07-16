#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS定时清理服务
提供统一的定时清理任务管理
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print

class CleanupTask:
    """清理任务"""
    
    def __init__(self, task_id: str, name: str, cleanup_type: str,
                 target: str, retention_days: int = 30,
                 interval_hours: int = 24, enabled: bool = True,
                 created_at: str = None):
        self.task_id = task_id
        self.name = name
        self.cleanup_type = cleanup_type
        self.target = target
        self.retention_days = retention_days
        self.interval_hours = interval_hours
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.items_cleaned = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'cleanup_type': self.cleanup_type,
            'target': self.target,
            'retention_days': self.retention_days,
            'interval_hours': self.interval_hours,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'last_run': self.last_run,
            'next_run': self.next_run,
            'run_count': self.run_count,
            'items_cleaned': self.items_cleaned
        }

class CleanupService:
    """定时清理服务"""
    
    def __init__(self):
        self.tasks: Dict[str, CleanupTask] = {}
        self.is_running = False
        self.cleanup_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
        self._register_default_tasks()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'cleanup_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'check_interval': 60,
            'default_retention_days': 30,
            'max_cleanup_per_run': 1000,
            'dry_run_enabled': False
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'cleanup_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cleanup_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    cleanup_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    retention_days INTEGER DEFAULT 30,
                    interval_hours INTEGER DEFAULT 24,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cleanup_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    items_found INTEGER DEFAULT 0,
                    items_cleaned INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cleanup_tasks_id ON cleanup_tasks(task_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cleanup_logs_task ON cleanup_logs(task_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[清理] 初始化数据库失败: {e}")
    
    def _register_default_tasks(self):
        """注册默认清理任务"""
        default_tasks = [
            CleanupTask('log_cleanup', '日志清理', 'database', 'audit_logs', 90, 24),
            CleanupTask('notification_cleanup', '通知清理', 'database', 'notifications', 30, 24),
            CleanupTask('temp_file_cleanup', '临时文件清理', 'files', 'uploads/temp', 7, 6),
            CleanupTask('report_cleanup', '报表清理', 'files', 'reports', 30, 24),
            CleanupTask('backup_cleanup', '备份清理', 'files', 'backups', 7, 24),
            CleanupTask('api_log_cleanup', 'API日志清理', 'database', 'api_request_logs', 30, 24),
            CleanupTask('search_log_cleanup', '搜索日志清理', 'database', 'search_queries', 30, 24),
            CleanupTask('migration_log_cleanup', '迁移日志清理', 'database', 'migration_runs', 90, 24)
        ]
        
        for task in default_tasks:
            if task.task_id not in self.tasks:
                self.tasks[task.task_id] = task
                self._save_task_to_db(task)
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        return f"cleanup_{int(time.time())}_{hash(os.urandom(16))}"
    
    def add_task(self, name: str, cleanup_type: str, target: str,
                retention_days: int = 30, interval_hours: int = 24,
                enabled: bool = True) -> str:
        """添加清理任务"""
        task_id = self._generate_task_id()
        
        task = CleanupTask(
            task_id=task_id,
            name=name,
            cleanup_type=cleanup_type,
            target=target,
            retention_days=retention_days,
            interval_hours=interval_hours,
            enabled=enabled
        )
        
        with self.lock:
            self.tasks[task_id] = task
        
        self._save_task_to_db(task)
        logger(f"[清理] 添加清理任务: {name}")
        
        return task_id
    
    def _save_task_to_db(self, task: CleanupTask):
        """保存任务到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO cleanup_tasks 
                (task_id, name, cleanup_type, target, retention_days, interval_hours, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id, task.name, task.cleanup_type,
                task.target, task.retention_days, task.interval_hours,
                1 if task.enabled else 0
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[清理] 保存任务失败: {e}")
    
    def remove_task(self, task_id: str) -> bool:
        """删除清理任务"""
        with self.lock:
            if task_id not in self.tasks:
                logger(f"[清理] 任务不存在: {task_id}")
                return False
            
            del self.tasks[task_id]
        
        self._delete_task_from_db(task_id)
        logger(f"[清理] 删除清理任务: {task_id}")
        
        return True
    
    def _delete_task_from_db(self, task_id: str):
        """从数据库删除任务"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cleanup_tasks WHERE task_id = ?', (task_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[清理] 删除任务失败: {e}")
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            self.tasks[task_id].enabled = True
        
        self._update_task_enabled(task_id, True)
        logger(f"[清理] 启用任务: {task_id}")
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            self.tasks[task_id].enabled = False
        
        self._update_task_enabled(task_id, False)
        logger(f"[清理] 禁用任务: {task_id}")
        return True
    
    def _update_task_enabled(self, task_id: str, enabled: bool):
        """更新任务启用状态"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('UPDATE cleanup_tasks SET enabled = ? WHERE task_id = ?',
                          (1 if enabled else 0, task_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[清理] 更新任务状态失败: {e}")
    
    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                time.sleep(self.config['check_interval'])
                
                now = datetime.now()
                
                with self.lock:
                    for task_id, task in list(self.tasks.items()):
                        if not task.enabled:
                            continue
                        
                        if task.last_run:
                            last_run_time = datetime.fromisoformat(task.last_run)
                            if (now - last_run_time).total_seconds() < task.interval_hours * 3600:
                                continue
                        
                        self._execute_cleanup(task_id)
            except Exception as e:
                logger(f"[清理] 清理循环错误: {e}")
    
    def _execute_cleanup(self, task_id: str):
        """执行清理"""
        with self.lock:
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
        
        started_at = datetime.now()
        
        def run_cleanup():
            try:
                items_found, items_cleaned = self._perform_cleanup(task)
                
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                
                with self.lock:
                    task.last_run = completed_at.isoformat()
                    task.next_run = (completed_at + timedelta(hours=task.interval_hours)).isoformat()
                    task.run_count += 1
                    task.items_cleaned += items_cleaned
                
                self._log_cleanup(task_id, 'success', started_at, completed_at, 
                                  duration, items_found, items_cleaned)
                
                logger(f"[清理] 完成: {task.name} - 清理 {items_cleaned}/{items_found} 条记录")
            except Exception as e:
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                
                self._log_cleanup(task_id, 'failed', started_at, completed_at, 
                                  duration, error_message=str(e))
                
                logger(f"[清理] 失败: {task.name} - {e}")
        
        thread = threading.Thread(target=run_cleanup, daemon=True)
        thread.start()
    
    def _perform_cleanup(self, task: CleanupTask) -> tuple:
        """执行实际清理操作"""
        items_found = 0
        items_cleaned = 0
        
        if task.cleanup_type == 'database':
            items_found, items_cleaned = self._cleanup_database(task)
        elif task.cleanup_type == 'files':
            items_found, items_cleaned = self._cleanup_files(task)
        
        return items_found, items_cleaned
    
    def _cleanup_database(self, task: CleanupTask) -> tuple:
        """清理数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cutoff_time = (datetime.now() - timedelta(days=task.retention_days)).isoformat()
            
            cursor.execute(f'SELECT COUNT(*) FROM {task.target} WHERE created_at < ?', (cutoff_time,))
            items_found = cursor.fetchone()[0]
            
            if not self.config['dry_run_enabled']:
                cursor.execute(f'DELETE FROM {task.target} WHERE created_at < ? LIMIT ?',
                              (cutoff_time, self.config['max_cleanup_per_run']))
                items_cleaned = cursor.rowcount
                conn.commit()
            
            conn.close()
            return items_found, items_cleaned
        except Exception as e:
            logger(f"[清理] 数据库清理失败: {e}")
            return 0, 0
    
    def _cleanup_files(self, task: CleanupTask) -> tuple:
        """清理文件"""
        items_found = 0
        items_cleaned = 0
        
        try:
            cutoff_time = datetime.now() - timedelta(days=task.retention_days)
            
            if os.path.exists(task.target):
                for filename in os.listdir(task.target):
                    filepath = os.path.join(task.target, filename)
                    
                    if os.path.isfile(filepath):
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        
                        if file_mtime < cutoff_time:
                            items_found += 1
                            
                            if not self.config['dry_run_enabled'] and items_cleaned < self.config['max_cleanup_per_run']:
                                os.remove(filepath)
                                items_cleaned += 1
            
            return items_found, items_cleaned
        except Exception as e:
            logger(f"[清理] 文件清理失败: {e}")
            return 0, 0
    
    def _log_cleanup(self, task_id: str, status: str, started_at: datetime,
                    completed_at: datetime, duration: float, items_found: int = 0,
                    items_cleaned: int = 0, error_message: str = None):
        """记录清理日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cleanup_logs 
                (task_id, status, started_at, completed_at, duration, items_found, items_cleaned, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, status,
                started_at.isoformat(),
                completed_at.isoformat(),
                duration,
                items_found,
                items_cleaned,
                error_message
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[清理] 记录日志失败: {e}")
    
    def run_task_now(self, task_id: str) -> bool:
        """立即执行任务"""
        with self.lock:
            if task_id not in self.tasks:
                logger(f"[清理] 任务不存在: {task_id}")
                return False
            
            task = self.tasks[task_id]
            
            if not task.enabled:
                logger(f"[清理] 任务已禁用: {task_id}")
                return False
        
        self._execute_cleanup(task_id)
        return True
    
    def run_all_tasks(self):
        """执行所有任务"""
        logger(f"[清理] 执行所有清理任务...")
        
        for task_id in self.tasks:
            self.run_task_now(task_id)
    
    def get_task(self, task_id: str) -> Optional[CleanupTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_tasks(self, enabled_only: bool = False) -> List[CleanupTask]:
        """获取任务列表"""
        with self.lock:
            if enabled_only:
                return [t for t in self.tasks.values() if t.enabled]
            return list(self.tasks.values())
    
    def get_cleanup_logs(self, task_id: str = None, status: str = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """获取清理日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM cleanup_logs WHERE 1=1'
            params = []
            
            if task_id:
                query += ' AND task_id = ?'
                params.append(task_id)
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY started_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            logs = []
            
            for row in cursor.fetchall():
                logs.append(dict(zip(columns, row)))
            
            conn.close()
            return logs
        except Exception as e:
            logger(f"[清理] 获取日志失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            enabled_count = sum(1 for t in self.tasks.values() if t.enabled)
            total_cleaned = sum(t.items_cleaned for t in self.tasks.values())
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_tasks': len(self.tasks),
                'enabled_tasks': enabled_count,
                'total_items_cleaned': total_cleaned,
                'check_interval': self.config['check_interval'],
                'dry_run_enabled': self.config['dry_run_enabled'],
                'max_cleanup_per_run': self.config['max_cleanup_per_run']
            }
    
    def start(self):
        """启动清理服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger(f"[清理] 定时清理服务已启动")
    
    def stop(self):
        """停止清理服务"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        
        logger(f"[清理] 定时清理服务已停止")

cleanup_service = CleanupService()
