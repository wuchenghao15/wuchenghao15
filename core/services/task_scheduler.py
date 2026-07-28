#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS定时任务调度服务
支持定时任务、周期性任务、一次性任务
"""

import os
import sys
import json
import time
import threading
import traceback
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = print

class ScheduledTask:
    """定时任务"""
    
    def __init__(self, task_id: str, name: str, func: Callable, 
                 schedule_type: str = 'interval', interval_seconds: int = 60,
                 cron_expression: str = None, run_at: datetime = None,
                 args: tuple = (), kwargs: dict = None, enabled: bool = True):
        self.task_id = task_id
        self.name = name
        self.func = func
        self.schedule_type = schedule_type
        self.interval_seconds = interval_seconds
        self.cron_expression = cron_expression
        self.run_at = run_at
        self.args = args
        self.kwargs = kwargs or {}
        self.enabled = enabled
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
    
    def should_run(self) -> bool:
        """判断是否应该运行"""
        if not self.enabled:
            return False
        
        now = datetime.now()
        
        if self.schedule_type == 'interval':
            if self.last_run is None:
                return True
            return (now - self.last_run).total_seconds() >= self.interval_seconds
        elif self.schedule_type == 'cron':
            return self._check_cron(now)
        elif self.schedule_type == 'once':
            return self.run_at is not None and now >= self.run_at and self.run_count == 0
        
        return False
    
    def _check_cron(self, now: datetime) -> bool:
        """检查cron表达式"""
        if not self.cron_expression:
            return False
        
        parts = self.cron_expression.split()
        if len(parts) != 5:
            return False
        
        minute, hour, day, month, weekday = parts
        
        if not self._matches(minute, now.minute):
            return False
        if not self._matches(hour, now.hour):
            return False
        if not self._matches(day, now.day):
            return False
        if not self._matches(month, now.month):
            return False
        if not self._matches(weekday, now.weekday() + 1):
            return False
        
        if self.last_run and now.minute == self.last_run.minute:
            return False
        
        return True
    
    def _matches(self, cron_part: str, value: int) -> bool:
        """检查cron部分是否匹配"""
        if cron_part == '*':
            return True
        if ',' in cron_part:
            return str(value) in cron_part.split(',')
        if '-' in cron_part:
            start, end = cron_part.split('-')
            return int(start) <= value <= int(end)
        return str(value) == cron_part
    
    def run(self):
        """运行任务"""
        if not self.enabled:
            return
        
        try:
            self.last_run = datetime.now()
            result = self.func(*self.args, **self.kwargs)
            self.run_count += 1
            logger(f"[调度] 任务执行成功: {self.name}")
            return result
        except Exception as e:
            self.error_count += 1
            logger(f"[调度] 任务执行失败: {self.name} - {e}")
            return None

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.is_running = False
        self.scheduler_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'scheduler_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'check_interval': 10,
            'max_concurrent_tasks': 5,
            'task_timeout': 300,
            'logging_enabled': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'scheduler_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('scheduler.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    schedule_type TEXT DEFAULT 'interval',
                    interval_seconds INTEGER DEFAULT 60,
                    cron_expression TEXT,
                    run_at TEXT,
                    args TEXT,
                    kwargs TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_run TEXT,
                    next_run TEXT,
                    run_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[调度] 初始化数据库失败: {e}")
    
    def add_task(self, task_id: str, name: str, func: Callable,
                 schedule_type: str = 'interval', interval_seconds: int = 60,
                 cron_expression: str = None, run_at: datetime = None,
                 args: tuple = (), kwargs: dict = None, enabled: bool = True):
        """添加任务"""
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            func=func,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            run_at=run_at,
            args=args,
            kwargs=kwargs,
            enabled=enabled
        )
        
        with self.lock:
            self.tasks[task_id] = task
        
        self._save_task_to_db(task)
        logger(f"[调度] 添加任务: {name}")
        
        return task
    
    def remove_task(self, task_id: str):
        """删除任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
        
        self._delete_task_from_db(task_id)
        logger(f"[调度] 删除任务: {task_id}")
    
    def enable_task(self, task_id: str):
        """启用任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = True
        
        self._update_task_enabled(task_id, True)
        logger(f"[调度] 启用任务: {task_id}")
    
    def disable_task(self, task_id: str):
        """禁用任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = False
        
        self._update_task_enabled(task_id, False)
        logger(f"[调度] 禁用任务: {task_id}")
    
    def _save_task_to_db(self, task: ScheduledTask):
        """保存任务到数据库"""
        try:
            conn = sqlite3.connect('scheduler.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (task_id, name, schedule_type, interval_seconds, cron_expression, 
                 run_at, args, kwargs, enabled, last_run, next_run, run_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id, task.name, task.schedule_type, task.interval_seconds,
                task.cron_expression,
                task.run_at.isoformat() if task.run_at else None,
                json.dumps(task.args), json.dumps(task.kwargs),
                1 if task.enabled else 0,
                task.last_run.isoformat() if task.last_run else None,
                task.next_run.isoformat() if task.next_run else None,
                task.run_count, task.error_count
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[调度] 保存任务失败: {e}")
    
    def _delete_task_from_db(self, task_id: str):
        """从数据库删除任务"""
        try:
            conn = sqlite3.connect('scheduler.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[调度] 删除任务失败: {e}")
    
    def _update_task_enabled(self, task_id: str, enabled: bool):
        """更新任务启用状态"""
        try:
            conn = sqlite3.connect('scheduler.db')
            cursor = conn.cursor()
            
            cursor.execute('UPDATE tasks SET enabled = ? WHERE task_id = ?', 
                          (1 if enabled else 0, task_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[调度] 更新任务状态失败: {e}")
    
    def _log_task_run(self, task_id: str, status: str, started_at: datetime, 
                     completed_at: datetime = None, duration: float = 0, 
                     error_message: str = None):
        """记录任务运行日志"""
        try:
            conn = sqlite3.connect('scheduler.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO task_logs 
                (task_id, status, started_at, completed_at, duration, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task_id, status,
                started_at.isoformat(),
                completed_at.isoformat() if completed_at else None,
                duration, error_message
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[调度] 记录日志失败: {e}")
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.is_running:
            try:
                now = datetime.now()
                
                with self.lock:
                    for task_id, task in list(self.tasks.items()):
                        if task.should_run():
                            self._execute_task(task)
                
                time.sleep(self.config['check_interval'])
            except Exception as e:
                logger(f"[调度] 调度循环错误: {e}")
    
    def _execute_task(self, task: ScheduledTask):
        """执行任务"""
        started_at = datetime.now()
        
        def run_task():
            try:
                result = task.run()
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                self._log_task_run(task.task_id, 'success', started_at, completed_at, duration)
                return result
            except Exception as e:
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                self._log_task_run(task.task_id, 'failed', started_at, completed_at, duration, str(e))
        
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger(f"[调度] 任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger(f"[调度] 任务调度器已停止")
    
    def get_tasks(self) -> Dict[str, Any]:
        """获取所有任务"""
        with self.lock:
            result = {}
            for task_id, task in self.tasks.items():
                result[task_id] = {
                    'name': task.name,
                    'schedule_type': task.schedule_type,
                    'interval_seconds': task.interval_seconds,
                    'cron_expression': task.cron_expression,
                    'run_at': task.run_at.isoformat() if task.run_at else None,
                    'enabled': task.enabled,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'run_count': task.run_count,
                    'error_count': task.error_count
                }
        return result
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取单个任务"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                return {
                    'name': task.name,
                    'schedule_type': task.schedule_type,
                    'interval_seconds': task.interval_seconds,
                    'cron_expression': task.cron_expression,
                    'run_at': task.run_at.isoformat() if task.run_at else None,
                    'enabled': task.enabled,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'run_count': task.run_count,
                    'error_count': task.error_count
                }
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        with self.lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'task_count': len(self.tasks),
                'enabled_tasks': sum(1 for t in self.tasks.values() if t.enabled),
                'check_interval': self.config['check_interval'],
                'max_concurrent_tasks': self.config['max_concurrent_tasks']
            }

task_scheduler = TaskScheduler()

def scheduled_task(task_id: str, name: str, schedule_type: str = 'interval', 
                   interval_seconds: int = 60, cron_expression: str = None,
                   run_at: datetime = None):
    """装饰器：注册定时任务"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        task_scheduler.add_task(
            task_id=task_id,
            name=name,
            func=func,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            run_at=run_at
        )
        
        return wrapper
    
    return decorator
