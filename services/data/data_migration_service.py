#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS数据迁移服务
提供数据迁移和同步功能
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

class Migration:
    """迁移"""
    
    def __init__(self, migration_id: str, name: str, source: str, target: str,
                 migration_type: str = 'copy', description: str = '',
                 filters: Dict[str, Any] = None, transforms: List[Dict[str, Any]] = None,
                 enabled: bool = True, created_at: str = None):
        self.migration_id = migration_id
        self.name = name
        self.source = source
        self.target = target
        self.migration_type = migration_type
        self.description = description
        self.filters = filters or {}
        self.transforms = transforms or []
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
        self.status = 'idle'
        self.last_run = None
        self.run_count = 0
        self.error_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'migration_id': self.migration_id,
            'name': self.name,
            'source': self.source,
            'target': self.target,
            'migration_type': self.migration_type,
            'description': self.description,
            'filters': self.filters,
            'transforms': self.transforms,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'status': self.status,
            'last_run': self.last_run,
            'run_count': self.run_count,
            'error_count': self.error_count
        }

class DataMigrationService:
    """数据迁移服务"""
    
    def __init__(self):
        self.migrations: Dict[str, Migration] = {}
        self.is_running = False
        self.lock = threading.Lock()
        
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'migration_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'batch_size': 1000,
            'commit_interval': 10000,
            'max_retries': 3,
            'retry_delay': 5,
            'enable_validation': True,
            'enable_rollback': True
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'migration_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    migration_type TEXT DEFAULT 'copy',
                    description TEXT,
                    filters TEXT,
                    transforms TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migration_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    records_read INTEGER DEFAULT 0,
                    records_written INTEGER DEFAULT 0,
                    records_failed INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migration_validation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_id TEXT NOT NULL,
                    run_id INTEGER,
                    validation_type TEXT,
                    source_count INTEGER,
                    target_count INTEGER,
                    matched_count INTEGER,
                    mismatched_count INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_migrations_id ON migrations(migration_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_migration_runs_migration ON migration_runs(migration_id)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[迁移] 初始化数据库失败: {e}")
    
    def _generate_migration_id(self) -> str:
        """生成迁移ID"""
        return f"migration_{int(time.time())}_{hash(os.urandom(16))}"
    
    def create_migration(self, name: str, source: str, target: str,
                        migration_type: str = 'copy', description: str = '',
                        filters: Dict[str, Any] = None, transforms: List[Dict[str, Any]] = None) -> str:
        """创建迁移"""
        migration_id = self._generate_migration_id()
        
        migration = Migration(
            migration_id=migration_id,
            name=name,
            source=source,
            target=target,
            migration_type=migration_type,
            description=description,
            filters=filters or {},
            transforms=transforms or []
        )
        
        with self.lock:
            self.migrations[migration_id] = migration
        
        self._save_migration_to_db(migration)
        logger(f"[迁移] 创建迁移: {name}")
        
        return migration_id
    
    def _save_migration_to_db(self, migration: Migration):
        """保存迁移到数据库"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO migrations 
                (migration_id, name, source, target, migration_type, description, filters, transforms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                migration.migration_id, migration.name, migration.source,
                migration.target, migration.migration_type, migration.description,
                json.dumps(migration.filters),
                json.dumps(migration.transforms)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[迁移] 保存迁移失败: {e}")
    
    def update_migration(self, migration_id: str, **kwargs) -> bool:
        """更新迁移"""
        with self.lock:
            if migration_id not in self.migrations:
                logger(f"[迁移] 迁移不存在: {migration_id}")
                return False
            
            migration = self.migrations[migration_id]
            
            if 'name' in kwargs:
                migration.name = kwargs['name']
            if 'description' in kwargs:
                migration.description = kwargs['description']
            if 'filters' in kwargs:
                migration.filters = kwargs['filters']
            if 'transforms' in kwargs:
                migration.transforms = kwargs['transforms']
            if 'enabled' in kwargs:
                migration.enabled = kwargs['enabled']
        
        self._update_migration_in_db(migration_id, kwargs)
        logger(f"[迁移] 更新迁移: {migration_id}")
        
        return True
    
    def _update_migration_in_db(self, migration_id: str, updates: Dict[str, Any]):
        """更新数据库中的迁移"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key in ['filters', 'transforms']:
                    set_clause.append(f"{key} = ?")
                    params.append(json.dumps(value))
                elif key == 'enabled':
                    set_clause.append(f"{key} = ?")
                    params.append(1 if value else 0)
                else:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            params.append(migration_id)
            
            cursor.execute(f'UPDATE migrations SET {", ".join(set_clause)} WHERE migration_id = ?', params)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[迁移] 更新迁移失败: {e}")
    
    def delete_migration(self, migration_id: str) -> bool:
        """删除迁移"""
        with self.lock:
            if migration_id not in self.migrations:
                logger(f"[迁移] 迁移不存在: {migration_id}")
                return False
            
            del self.migrations[migration_id]
        
        self._delete_migration_from_db(migration_id)
        logger(f"[迁移] 删除迁移: {migration_id}")
        
        return True
    
    def _delete_migration_from_db(self, migration_id: str):
        """从数据库删除迁移"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM migrations WHERE migration_id = ?', (migration_id,))
            cursor.execute('DELETE FROM migration_runs WHERE migration_id = ?', (migration_id,))
            cursor.execute('DELETE FROM migration_validation WHERE migration_id = ?', (migration_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[迁移] 删除迁移失败: {e}")
    
    def run_migration(self, migration_id: str) -> bool:
        """执行迁移"""
        with self.lock:
            if migration_id not in self.migrations:
                logger(f"[迁移] 迁移不存在: {migration_id}")
                return False
            
            migration = self.migrations[migration_id]
            
            if not migration.enabled:
                logger(f"[迁移] 迁移已禁用: {migration_id}")
                return False
            
            if migration.status == 'running':
                logger(f"[迁移] 迁移正在运行: {migration_id}")
                return False
            
            migration.status = 'running'
        
        started_at = datetime.now()
        run_id = None
        
        try:
            run_id = self._start_run(migration_id, started_at)
            
            records_read, records_written, records_failed = self._execute_migration(migration)
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            with self.lock:
                migration.status = 'completed'
                migration.last_run = completed_at.isoformat()
                migration.run_count += 1
            
            self._end_run(run_id, 'success', completed_at, duration,
                          records_read, records_written, records_failed)
            
            if self.config['enable_validation']:
                self._validate_migration(migration_id, run_id)
            
            logger(f"[迁移] 迁移完成: {migration.name}")
            
            return True
        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            with self.lock:
                migration.status = 'failed'
                migration.last_run = completed_at.isoformat()
                migration.error_count += 1
            
            if run_id:
                self._end_run(run_id, 'failed', completed_at, duration, error_message=str(e))
            
            logger(f"[迁移] 迁移失败: {migration.name} - {e}")
            
            return False
    
    def _execute_migration(self, migration: Migration) -> tuple:
        """执行实际迁移操作"""
        records_read = 0
        records_written = 0
        records_failed = 0
        
        try:
            source_conn = sqlite3.connect(migration.source) if '.db' in migration.source else sqlite3.connect('app.db')
            target_conn = sqlite3.connect(migration.target) if '.db' in migration.target else sqlite3.connect('app.db')
            
            source_cursor = source_conn.cursor()
            target_cursor = target_conn.cursor()
            
            table_name = migration.source.split('.')[0] if '.db' in migration.source else migration.source
            
            query = f'SELECT * FROM {table_name}'
            
            if migration.filters:
                conditions = []
                for key, value in migration.filters.items():
                    if isinstance(value, str):
                        conditions.append(f"{key} = '{value}'")
                    else:
                        conditions.append(f"{key} = {value}")
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
            
            source_cursor.execute(query)
            columns = [desc[0] for desc in source_cursor.description]
            
            target_table = migration.target.split('.')[0] if '.db' in migration.target else migration.target
            
            batch = []
            for row in source_cursor.fetchall():
                records_read += 1
                
                record = dict(zip(columns, row))
                
                for transform in migration.transforms:
                    field = transform.get('field')
                    operation = transform.get('operation')
                    value = transform.get('value')
                    
                    if field in record:
                        if operation == 'set':
                            record[field] = value
                        elif operation == 'map':
                            mapping = transform.get('mapping', {})
                            record[field] = mapping.get(record[field], record[field])
                        elif operation == 'calculate':
                            expr = transform.get('expression', '')
                            try:
                                record[field] = eval(expr, {}, record)
                            except:
                                pass
                
                batch.append(tuple(record.values()))
                
                if len(batch) >= self.config['batch_size']:
                    try:
                        placeholders = ', '.join(['?' for _ in columns])
                        target_cursor.executemany(
                            f'INSERT OR REPLACE INTO {target_table} ({", ".join(columns)}) VALUES ({placeholders})',
                            batch
                        )
                        records_written += len(batch)
                        batch = []
                    except Exception as e:
                        records_failed += len(batch)
                        batch = []
            
            if batch:
                try:
                    placeholders = ', '.join(['?' for _ in columns])
                    target_cursor.executemany(
                        f'INSERT OR REPLACE INTO {target_table} ({", ".join(columns)}) VALUES ({placeholders})',
                        batch
                    )
                    records_written += len(batch)
                except Exception as e:
                    records_failed += len(batch)
            
            target_conn.commit()
            
            source_conn.close()
            target_conn.close()
        except Exception as e:
            logger(f"[迁移] 执行迁移失败: {e}")
        
        return records_read, records_written, records_failed
    
    def _validate_migration(self, migration_id: str, run_id: int):
        """验证迁移"""
        try:
            migration = self.migrations.get(migration_id)
            if not migration:
                return
            
            source_conn = sqlite3.connect(migration.source) if '.db' in migration.source else sqlite3.connect('app.db')
            target_conn = sqlite3.connect(migration.target) if '.db' in migration.target else sqlite3.connect('app.db')
            
            source_cursor = source_conn.cursor()
            target_cursor = target_conn.cursor()
            
            source_table = migration.source.split('.')[0] if '.db' in migration.source else migration.source
            target_table = migration.target.split('.')[0] if '.db' in migration.target else migration.target
            
            source_cursor.execute(f'SELECT COUNT(*) FROM {source_table}')
            source_count = source_cursor.fetchone()[0]
            
            target_cursor.execute(f'SELECT COUNT(*) FROM {target_table}')
            target_count = target_cursor.fetchone()[0]
            
            source_conn.close()
            target_conn.close()
            
            status = 'success' if source_count == target_count else 'warning'
            matched_count = min(source_count, target_count)
            mismatched_count = abs(source_count - target_count)
            
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO migration_validation 
                (migration_id, run_id, validation_type, source_count, target_count, 
                 matched_count, mismatched_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (migration_id, run_id, 'count', source_count, target_count,
                  matched_count, mismatched_count, status))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[迁移] 验证迁移失败: {e}")
    
    def _start_run(self, migration_id: str, started_at: datetime) -> int:
        """开始迁移记录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO migration_runs (migration_id, status, started_at)
                VALUES (?, ?, ?)
            ''', (migration_id, 'running', started_at.isoformat()))
            
            run_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return run_id
        except Exception as e:
            logger(f"[迁移] 开始迁移记录失败: {e}")
            return 0
    
    def _end_run(self, run_id: int, status: str, completed_at: datetime,
                 duration: float, records_read: int = 0, records_written: int = 0,
                 records_failed: int = 0, error_message: str = None):
        """结束迁移记录"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE migration_runs 
                SET status = ?, completed_at = ?, duration = ?, records_read = ?, 
                    records_written = ?, records_failed = ?, error_message = ?
                WHERE id = ?
            ''', (status, completed_at.isoformat(), duration, records_read,
                  records_written, records_failed, error_message, run_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[迁移] 结束迁移记录失败: {e}")
    
    def get_migration(self, migration_id: str) -> Optional[Migration]:
        """获取迁移"""
        return self.migrations.get(migration_id)
    
    def get_migrations(self, enabled_only: bool = False) -> List[Migration]:
        """获取迁移列表"""
        with self.lock:
            if enabled_only:
                return [m for m in self.migrations.values() if m.enabled]
            return list(self.migrations.values())
    
    def get_run_history(self, migration_id: str = None, status: str = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """获取运行历史"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            
            query = 'SELECT * FROM migration_runs WHERE 1=1'
            params = []
            
            if migration_id:
                query += ' AND migration_id = ?'
                params.append(migration_id)
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY started_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            runs = []
            
            for row in cursor.fetchall():
                runs.append(dict(zip(columns, row)))
            
            conn.close()
            return runs
        except Exception as e:
            logger(f"[迁移] 获取运行历史失败: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        with self.lock:
            running_count = sum(1 for m in self.migrations.values() if m.status == 'running')
            enabled_count = sum(1 for m in self.migrations.values() if m.enabled)
            
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_migrations': len(self.migrations),
                'enabled_migrations': enabled_count,
                'running_migrations': running_count,
                'batch_size': self.config['batch_size'],
                'max_retries': self.config['max_retries'],
                'enable_validation': self.config['enable_validation'],
                'enable_rollback': self.config['enable_rollback']
            }
    
    def start(self):
        """启动迁移服务"""
        if self.is_running:
            return
        
        self.is_running = True
        logger(f"[迁移] 数据迁移服务已启动")
    
    def stop(self):
        """停止迁移服务"""
        self.is_running = False
        logger(f"[迁移] 数据迁移服务已停止")

data_migration_service = DataMigrationService()
