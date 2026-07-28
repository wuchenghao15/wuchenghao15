#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS数据同步服务
提供数据同步和状态管理功能
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class SyncTask:
    """同步任务"""
    
    def __init__(self, task_id: str, name: str, source: str, target: str,
                 sync_type: str = 'full', interval_seconds: int = 3600,
                 enabled: bool = True, last_sync: str = None,
                 last_status: str = 'pending'):
        self.task_id = task_id
        self.name = name
        self.source = source
        self.target = target
        self.sync_type = sync_type
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.last_sync = last_sync
        self.last_status = last_status
        self.sync_count = 0
        self.error_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'source': self.source,
            'target': self.target,
            'sync_type': self.sync_type,
            'interval_seconds': self.interval_seconds,
            'enabled': self.enabled,
            'last_sync': self.last_sync,
            'last_status': self.last_status,
            'sync_count': self.sync_count,
            'error_count': self.error_count
        }

class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        self.tasks: Dict[str, SyncTask] = {}
        self.is_running = False
        self.sync_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'data_sync_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'sync_interval': 60,
            'max_concurrent_syncs': 5,
            'timeout': 300,
            'retry_count': 3,
            'retry_delay': 10
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'data_sync_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    sync_type TEXT DEFAULT 'full',
                    interval_seconds INTEGER DEFAULT 3600,
                    enabled INTEGER DEFAULT 1,
                    last_sync TEXT,
                    last_status TEXT DEFAULT 'pending',
                    sync_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    records_synced INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sync_tasks_id ON sync_tasks(task_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sync_logs_task ON sync_logs(task_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[同步] 初始化数据库失败: {e}")
    
    def add_sync_task(self, task_id: str, name: str, source: str, target: str,
                      sync_type: str = 'full', interval_seconds: int = 3600,
                      enabled: bool = True) -> bool:
        """添加同步任务"""
        if task_id in self.tasks:
            logger(f"[同步] 任务已存在: {task_id}")
            return False
        
        task = SyncTask(
            task_id=task_id,
            name=name,
            source=source,
            target=target,
            sync_type=sync_type,
            interval_seconds=interval_seconds,
            enabled=enabled
        )
        
        with self.lock:
            self.tasks[task_id] = task
        
        self._save_task_to_db(task)
        logger(f"[同步] 添加同步任务: {name}")
        
        return True
    
    def _save_task_to_db(self, task: SyncTask):
        """保存任务到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_tasks 
                (task_id, name, source, target, sync_type, interval_seconds, enabled, last_sync, last_status,
                sync_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id, task.name, task.source, task.target,
                task.sync_type, task.interval_seconds,
                1 if task.enabled else 0,
                task.last_sync, task.last_status,
                task.sync_count, task.error_count
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[同步] 保存任务失败: {e}")
    
    def remove_sync_task(self, task_id: str) -> bool:
        """删除同步任务"""
        with self.lock:
            if task_id not in self.tasks:
                logger(f"[同步] 任务不存在: {task_id}")
                return False
            
            del self.tasks[task_id]
        
        self._delete_task_from_db(task_id)
        logger(f"[同步] 删除同步任务: {task_id}")
        
        return True
    
    def _delete_task_from_db(self, task_id: str):
        """从数据库删除任务"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sync_tasks WHERE task_id = ?', (task_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[同步] 删除任务失败: {e}")
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            self.tasks[task_id].enabled = True
        
        self._update_task_enabled(task_id, True)
        logger(f"[同步] 启用任务: {task_id}")
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            self.tasks[task_id].enabled = False
        
        self._update_task_enabled(task_id, False)
        logger(f"[同步] 禁用任务: {task_id}")
        return True
    
    def _update_task_enabled(self, task_id: str, enabled: bool):
        """更新任务启用状态"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('UPDATE sync_tasks SET enabled = ? WHERE task_id = ?',
                          (1 if enabled else 0, task_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[同步] 更新任务状态失败: {e}")
    
    def _sync_loop(self):
        """同步循环"""
        while self.is_running:
            try:
                time.sleep(self.config['sync_interval'])
                
                now = datetime.now()
                
                with self.lock:
                    for task_id, task in list(self.tasks.items()):
                        if not task.enabled:
                            continue
                        
                        if task.last_sync:
                            last_sync_time = datetime.fromisoformat(task.last_sync)
                            if (now - last_sync_time).total_seconds() < task.interval_seconds:
                                continue
                        
                        self._execute_sync(task_id)
            except Exception as e:
                logger(f"[同步] 同步循环错误: {e}")
    
    def _execute_sync(self, task_id: str):
        """执行同步"""
        with self.lock:
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            task.last_status = 'running'
        
        started_at = datetime.now()
        
        def run_sync():
            try:
                records_synced = self._perform_sync(task)
                
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                
                with self.lock:
                    task.last_sync = completed_at.isoformat()
                    task.last_status = 'success'
                    task.sync_count += 1
                
                self._log_sync(task_id, 'success', started_at, completed_at, duration, records_synced)
                logger(f"[同步] 同步完成: {task.name}")
            except Exception as e:
                completed_at = datetime.now()
                duration = (completed_at - started_at).total_seconds()
                
                with self.lock:
                    task.last_sync = completed_at.isoformat()
                    task.last_status = 'failed'
                    task.error_count += 1
                
                self._log_sync(task_id, 'failed', started_at, completed_at, duration, error_message=str(e))
                logger(f"[同步] 同步失败: {task.name} - {e}")
        
        thread = threading.Thread(target=run_sync, daemon=True)
        thread.start()
    
    def _perform_sync(self, task: SyncTask) -> int:
        """执行实际同步操作"""
        records_synced = 0
        
        if task.sync_type == 'full':
            records_synced = self._full_sync(task.source, task.target)
        elif task.sync_type == 'incremental':
            records_synced = self._incremental_sync(task.source, task.target)
        elif task.sync_type == 'one_way':
            records_synced = self._one_way_sync(task.source, task.target)
        
        return records_synced
    
    def _full_sync(self, source: str, target: str) -> int:
        """全量同步"""
        return self._copy_data(source, target)
    
    def _incremental_sync(self, source: str, target: str) -> int:
        """增量同步"""
        return self._copy_data(source, target)
    
    def _one_way_sync(self, source: str, target: str) -> int:
        """单向同步"""
        return self._copy_data(source, target)
    
    def _copy_data(self, source: str, target: str) -> int:
        """复制数据"""
        return 0
    
    def _log_sync(self, task_id: str, status: str, started_at: datetime,
                  completed_at: datetime, duration: float, records_synced: int = 0,
                  error_message: str = None):
        """记录同步日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_logs 
                (task_id, status, started_at, completed_at, duration, records_synced, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, status,
                started_at.isoformat(),
                completed_at.isoformat(),
                duration,
                records_synced,
                error_message
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[同步] 记录日志失败: {e}")
    
    def sync_now(self, task_id: str) -> bool:
        """立即同步"""
        with self.lock:
            if task_id not in self.tasks:
                logger(f"[同步] 任务不存在: {task_id}")
                return False
            
            task = self.tasks[task_id]
            
            if task.last_status == 'running':
                logger(f"[同步] 任务正在运行: {task_id}")
                return False
        
        self._execute_sync(task_id)
        return True
    
    def get_task(self, task_id: str) -> Optional[SyncTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_tasks(self) -> List[SyncTask]:
        """获取任务列表"""
        with self.lock:
            return list(self.tasks.values())
    
    def get_sync_logs(self, task_id: str = None, status: str = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """获取同步日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM sync_logs WHERE 1=1'
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
            logger(f"[同步] 获取日志失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            running_count = sum(1 for task in self.tasks.values() if task.last_status == 'running')
            enabled_count = sum(1 for task in self.tasks.values() if task.enabled)
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_tasks': len(self.tasks),
                'enabled_tasks': enabled_count,
                'running_tasks': running_count,
                'sync_interval': self.config['sync_interval'],
                'max_concurrent_syncs': self.config['max_concurrent_syncs']
            }
    
    def start(self):
        """启动同步服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger(f"[同步] 数据同步服务已启动")
    
    def stop(self):
        """停止同步服务"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join()
        
        logger(f"[同步] 数据同步服务已停止")

data_sync_service = DataSyncService()

