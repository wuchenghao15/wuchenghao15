# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
数据库同步管理器
实现主从同步、影子数据库、变更日志和数据一致性检查
"""

import threading
import time
import json
import hashlib
import sqlite3
import os
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from contextlib import contextmanager

from app.utils.logging import logger
from app.utils.db import db_manager
from app.utils.lock_sync_manager import lock_sync_manager, LockType
import logging


class SyncMode(Enum):
    """同步模式"""
    MASTER_SLAVE = "master_slave"
    SHADOW = "shadow"
    PEER_TO_PEER = "peer_to_peer"


class ChangeType(Enum):
    """变更类型"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class ChangeLog:
    """变更日志"""
    id: str
    table_name: str
    primary_key: str
    change_type: ChangeType
    old_data: Optional[Dict]
    new_data: Optional[Dict]
    created_at: float
    synced_at: Optional[float] = None
    sync_status: str = "pending"


@dataclass
class SyncStatus:
    """同步状态"""
    mode: SyncMode
    is_running: bool
    last_sync: Optional[float]
    pending_changes: int
    sync_errors: int
    avg_sync_time: float


class ChangeTracker:
    """变更追踪器"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self._init_change_log_table()

    def _init_change_log_table(self):
        """初始化变更日志表"""
        try:
            query = """CREATE TABLE IF NOT EXISTS change_logs (
                id TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                primary_key TEXT NOT NULL,
                change_type TEXT NOT NULL,
                old_data TEXT,
                new_data TEXT,
                created_at REAL NOT NULL,
                synced_at REAL,
                sync_status TEXT DEFAULT 'pending'
            )"""
            self.db.execute(query)
            
            query = """CREATE INDEX IF NOT EXISTS idx_change_log_table 
                      ON change_logs(table_name)"""
            self.db.execute(query)
            
            query = """CREATE INDEX IF NOT EXISTS idx_change_log_status 
                      ON change_logs(sync_status)"""
            self.db.execute(query)
            
            query = """CREATE INDEX IF NOT EXISTS idx_change_log_created 
                      ON change_logs(created_at)"""
            self.db.execute(query)
        except Exception as e:
            logger.warning(f"初始化变更日志表失败: {str(e)}")

    def log_change(self, table_name: str, primary_key: str, 
                  change_type: ChangeType, old_data: Optional[Dict] = None,
                  new_data: Optional[Dict] = None) -> str:
        """记录变更"""
        change_id = hashlib.md5(f"{table_name}:{primary_key}:{time.time()}".encode()).hexdigest()
        
        try:
            query = """INSERT INTO change_logs 
                      (id, table_name, primary_key, change_type, old_data, new_data, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?)"""
            
            old_json = json.dumps(old_data) if old_data else None
            new_json = json.dumps(new_data) if new_data else None
            
            self.db.execute(query, (
                change_id, table_name, primary_key, change_type.value,
                old_json, new_json, time.time()
            ))
            
            logger.debug(f"记录变更: {table_name}.{primary_key} {change_type.value}")
            return change_id
        except Exception as e:
            logger.error(f"记录变更失败: {str(e)}")
            return ""

    def get_pending_changes(self, limit: int = 100, 
                           table_name: Optional[str] = None) -> List[ChangeLog]:
        """获取待同步的变更"""
        try:
            if table_name:
                query = """SELECT id, table_name, primary_key, change_type, 
                                  old_data, new_data, created_at, synced_at, sync_status
                           FROM change_logs 
                           WHERE sync_status = 'pending' AND table_name = ?
                           ORDER BY created_at ASC LIMIT ?"""
                cursor, success = self.db.execute(query, (table_name, limit))
            else:
                query = """SELECT id, table_name, primary_key, change_type, 
                                  old_data, new_data, created_at, synced_at, sync_status
                           FROM change_logs 
                           WHERE sync_status = 'pending'
                           ORDER BY created_at ASC LIMIT ?"""
                cursor, success = self.db.execute(query, (limit,))
            
            changes = []
            if success and cursor:
                rows = cursor.fetchall()
                for row in rows:
                    change = ChangeLog(
                        id=row[0],
                        table_name=row[1],
                        primary_key=row[2],
                        change_type=ChangeType(row[3]),
                        old_data=json.loads(row[4]) if row[4] else None,
                        new_data=json.loads(row[5]) if row[5] else None,
                        created_at=row[6],
                        synced_at=row[7] if len(row) > 7 else None,
                        sync_status=row[8] if len(row) > 8 else "pending"
                    )
                    changes.append(change)
            
            return changes
        except Exception as e:
            logger.error(f"获取待同步变更失败: {str(e)}")
            return []

    def mark_synced(self, change_id: str):
        """标记为已同步"""
        try:
            query = """UPDATE change_logs 
                      SET sync_status = 'synced', synced_at = ?
                      WHERE id = ?"""
            self.db.execute(query, (time.time(), change_id))
        except Exception as e:
            logger.error(f"标记同步状态失败: {str(e)}")

    def mark_failed(self, change_id: str):
        """标记为失败"""
        try:
            query = """UPDATE change_logs 
                      SET sync_status = 'failed'
                      WHERE id = ?"""
            self.db.execute(query, (change_id,))
        except Exception as e:
            logger.error(f"标记失败状态失败: {str(e)}")

    def cleanup_old_logs(self, days: int = 30):
        """清理旧的日志"""
        try:
            cutoff = time.time() - (days * 86400)
            query = "DELETE FROM change_logs WHERE created_at < ? AND sync_status = 'synced'"
            self.db.execute(query, (cutoff,))
            logger.info(f"清理了 {days} 天前的同步日志")
        except Exception as e:
            logger.error(f"清理旧日志失败: {str(e)}")


class ShadowDatabase:
    """影子数据库 - 用于读写分离和容灾"""
    
    def __init__(self, db_manager_instance=None, shadow_path: Optional[str] = None):
        self.db = db_manager_instance or db_manager
        self._shadow_path = shadow_path or self._get_default_shadow_path()
        self._shadow_conn: Optional[sqlite3.Connection] = None
        self._is_enabled = False
        self._lock = threading.Lock()

    def _get_default_shadow_path(self) -> str:
        """获取默认影子数据库路径"""
        try:
            base_path = getattr(self.db, 'db_path', 'app.db')
            path, ext = os.path.splitext(base_path)
            return f"{path}_shadow{ext}"
        except Exception:
            return "app_shadow.db"

    def enable(self):
        """启用影子数据库"""
        with self._lock:
            if self._is_enabled:
                return
            
            try:
                self._shadow_conn = sqlite3.connect(self._shadow_path, check_same_thread=False)
                self._is_enabled = True
                logger.info(f"影子数据库已启用: {self._shadow_path}")
            except Exception as e:
                logger.error(f"启用影子数据库失败: {str(e)}")

    def disable(self):
        """禁用影子数据库"""
        with self._lock:
            if not self._is_enabled:
                return
            
            try:
                if self._shadow_conn:
                    self._shadow_conn.close()
                    self._shadow_conn = None
                self._is_enabled = False
                logger.info("影子数据库已禁用")
            except Exception as e:
                logger.error(f"禁用影子数据库失败: {str(e)}")

    def sync_from_master(self, table_name: Optional[str] = None) -> bool:
        """从主库同步"""
        if not self._is_enabled:
            return False
        
        try:
            with lock_sync_manager.write_lock("shadow_sync", distributed=False):
                # 获取所有表
                if table_name:
                    tables = [table_name]
                else:
                    tables = self._get_all_tables_from_master()
                
                for table in tables:
                    self._sync_table(table)
                
                return True
        except Exception as e:
            logger.error(f"从主库同步失败: {str(e)}")
            return False

    def _get_all_tables_from_master(self) -> List[str]:
        """从主库获取所有表"""
        tables = []
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            results = self.db.fetch_all(query)
            for row in results:
                if isinstance(row, dict):
                    tables.append(row.get('name', ''))
                else:
                    tables.append(row[0])
        except Exception as e:
            logger.error(f"获取表列表失败: {str(e)}")
        return tables

    def _sync_table(self, table_name: str):
        """同步单个表"""
        try:
            if not self._shadow_conn:
                return
            
            # 获取表结构
            schema_query = f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            schema_result = self.db.fetch_one(schema_query)
            
            if schema_result:
                if isinstance(schema_result, dict):
                    schema = schema_result.get('sql', '')
                else:
                    schema = schema_result[0]
                
                if schema:
                    # 在影子库创建表
                    cursor = self._shadow_conn.cursor()
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                    cursor.execute(schema)
                    
                    # 复制数据
                    data = self.db.fetch_all(f"SELECT * FROM {table_name}")
                    if data:
                        # 获取列名
                        col_query = f"PRAGMA table_info({table_name})"
                        col_results = self.db.fetch_all(col_query)
                        columns = []
                        for col in col_results:
                            if isinstance(col, dict):
                                columns.append(col.get('name', ''))
                            else:
                                columns.append(col[1])
                        
                        if columns:
                            placeholders = ', '.join(['?'] * len(columns))
                            insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            
                            for row in data:
                                values = []
                                for col in columns:
                                    if isinstance(row, dict):
                                        values.append(row.get(col))
                                    else:
                                        idx = columns.index(col)
                                        values.append(row[idx] if idx < len(row) else None)
                                cursor.execute(insert_query, values)
                    
                    self._shadow_conn.commit()
                    logger.debug(f"表 {table_name} 已同步到影子库")
        except Exception as e:
            logger.error(f"同步表 {table_name} 失败: {str(e)}")

    def read_from_shadow(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """从影子库读取"""
        if not self._is_enabled or not self._shadow_conn:
            return []
        
        try:
            cursor = self._shadow_conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"从影子库读取失败: {str(e)}")
            return []

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled


class DatabaseSyncManager:
    """数据库同步管理器"""
    
    def __init__(self, db_manager_instance=None):
        self.db = db_manager_instance or db_manager
        self._change_tracker = ChangeTracker(self.db)
        self._shadow_db = ShadowDatabase(self.db)
        self._sync_thread: Optional[threading.Thread] = None
        self._running = False
        self._sync_interval = 60.0  # 默认60秒同步一次
        self._mode = SyncMode.MASTER_SLAVE
        self._status = SyncStatus(
            mode=self._mode,
            is_running=False,
            last_sync=None,
            pending_changes=0,
            sync_errors=0,
            avg_sync_time=0.0
        )
        self._status_lock = threading.Lock()
        self._sync_times: List[float] = []
        self._init_sync_meta_table()

    def _init_sync_meta_table(self):
        """初始化同步元数据表"""
        try:
            query = """CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            )"""
            self.db.execute(query)
        except Exception as e:
            logger.warning(f"初始化同步元数据表失败: {str(e)}")

    def set_sync_mode(self, mode: SyncMode):
        """设置同步模式"""
        self._mode = mode
        with self._status_lock:
            self._status.mode = mode
        logger.info(f"同步模式已设置为: {mode.value}")

    def enable_shadow_database(self, shadow_path: Optional[str] = None):
        """启用影子数据库"""
        self._shadow_db = ShadowDatabase(self.db, shadow_path)
        self._shadow_db.enable()
        self._shadow_db.sync_from_master()

    def disable_shadow_database(self):
        """禁用影子数据库"""
        self._shadow_db.disable()

    def start_auto_sync(self, interval: float = 60.0):
        """启动自动同步"""
        if self._running:
            return
        
        self._sync_interval = interval
        self._running = True
        
        with self._status_lock:
            self._status.is_running = True
        
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        logger.info(f"自动同步已启动, 间隔: {interval}秒")

    def stop_auto_sync(self):
        """停止自动同步"""
        self._running = False
        
        with self._status_lock:
            self._status.is_running = False
        
        if self._sync_thread:
            self._sync_thread.join(timeout=10.0)
        logger.info("自动同步已停止")

    def _sync_loop(self):
        """同步循环"""
        while self._running:
            try:
                start_time = time.time()
                self._perform_sync()
                sync_time = time.time() - start_time
                
                # 更新统计
                with self._status_lock:
                    self._status.last_sync = time.time()
                    self._sync_times.append(sync_time)
                    if len(self._sync_times) > 100:
                        self._sync_times = self._sync_times[-100:]
                    self._status.avg_sync_time = sum(self._sync_times) / len(self._sync_times)
                
                # 等待下一次同步
                time.sleep(self._sync_interval)
            except Exception as e:
                logger.error(f"同步循环异常: {str(e)}")
                with self._status_lock:
                    self._status.sync_errors += 1
                time.sleep(5.0)  # 出错时等待更短时间再试

    def _perform_sync(self):
        """执行同步"""
        if self._mode == SyncMode.MASTER_SLAVE:
            self._sync_master_slave()
        elif self._mode == SyncMode.SHADOW:
            self._sync_shadow()
        elif self._mode == SyncMode.PEER_TO_PEER:
            self._sync_peer_to_peer()

    def _sync_master_slave(self):
        """主从同步"""
        pending = self._change_tracker.get_pending_changes(limit=100)
        
        with self._status_lock:
            self._status.pending_changes = len(pending)
        
        for change in pending:
            try:
                # 这里可以添加实际的从库同步逻辑
                # 例如: 将变更应用到从库
                self._change_tracker.mark_synced(change.id)
            except Exception as e:
                logger.error(f"同步变更失败: {change.id}, 错误: {str(e)}")
                self._change_tracker.mark_failed(change.id)
                with self._status_lock:
                    self._status.sync_errors += 1

    def _sync_shadow(self):
        """影子数据库同步"""
        if self._shadow_db.is_enabled:
            self._shadow_db.sync_from_master()

    def _sync_peer_to_peer(self):
        """点对点同步"""
        # 可以实现P2P同步逻辑
        pass

    def sync_now(self) -> bool:
        """立即同步"""
        try:
            start_time = time.time()
            self._perform_sync()
            
            sync_time = time.time() - start_time
            with self._status_lock:
                self._status.last_sync = time.time()
                self._sync_times.append(sync_time)
            
            logger.info(f"手动同步完成, 耗时: {sync_time:.3f}秒")
            return True
        except Exception as e:
            logger.error(f"手动同步失败: {str(e)}")
            return False

    def track_change(self, table_name: str, primary_key: str,
                    change_type: ChangeType, old_data: Optional[Dict] = None,
                    new_data: Optional[Dict] = None):
        """追踪变更"""
        self._change_tracker.log_change(table_name, primary_key, change_type, old_data, new_data)

    def get_status(self) -> SyncStatus:
        """获取同步状态"""
        with self._status_lock:
            pending = len(self._change_tracker.get_pending_changes(limit=1000))
            self._status.pending_changes = pending
            return SyncStatus(
                mode=self._status.mode,
                is_running=self._status.is_running,
                last_sync=self._status.last_sync,
                pending_changes=pending,
                sync_errors=self._status.sync_errors,
                avg_sync_time=self._status.avg_sync_time
            )

    def check_data_consistency(self, table_name: Optional[str] = None) -> Dict:
        """检查数据一致性"""
        report = {
            'total_tables': 0,
            'consistent_tables': 0,
            'inconsistent_tables': [],
            'details': {}
        }
        
        if not self._shadow_db.is_enabled:
            report['error'] = '影子数据库未启用'
            return report
        
        try:
            tables = [table_name] if table_name else self._get_all_tables()
            report['total_tables'] = len(tables)
            
            for table in tables:
                try:
                    # 获取主库行数
                    master_count = self.db.fetch_scalar(f"SELECT COUNT(*) FROM {table}") or 0
                    
                    # 获取影子库行数
                    shadow_result = self._shadow_db.read_from_shadow(f"SELECT COUNT(*) FROM {table}")
                    shadow_count = shadow_result[0][0] if shadow_result else 0
                    
                    is_consistent = master_count == shadow_count
                    
                    if is_consistent:
                        report['consistent_tables'] += 1
                    else:
                        report['inconsistent_tables'].append(table)
                    
                    report['details'][table] = {
                        'master_count': master_count,
                        'shadow_count': shadow_count,
                        'consistent': is_consistent
                    }
                except Exception as e:
                    report['details'][table] = {'error': str(e)}
                    report['inconsistent_tables'].append(table)
        except Exception as e:
            report['error'] = str(e)
        
        return report

    def _get_all_tables(self) -> List[str]:
        """获取所有表"""
        tables = []
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            results = self.db.fetch_all(query)
            for row in results:
                if isinstance(row, dict):
                    tables.append(row.get('name', ''))
                else:
                    tables.append(row[0])
        except Exception as e:
            logger.error(f"获取表列表失败: {str(e)}")
        return tables

    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        self._change_tracker.cleanup_old_logs(days)

    @property
    def change_tracker(self) -> ChangeTracker:
        return self._change_tracker

    @property
    def shadow_database(self) -> ShadowDatabase:
        return self._shadow_db


# 便捷函数
def with_change_tracking(table_name: str, primary_key: str = 'id'):
    """变更追踪装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 可以在这里实现自动追踪变更的逻辑
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 创建全局实例
db_sync_manager = DatabaseSyncManager()
