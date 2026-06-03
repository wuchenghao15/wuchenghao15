# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据存储管理器 - 使用数据库替代JSON文件存储
"""

import logging
import os
import sqlite3
from contextlib import contextmanager
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

logger = logging.getLogger(__name__)


class DataStorageManager:
    """统一数据存储管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(__file__), '..', 'app.db')
        else:
            self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                task_type TEXT,
                priority INTEGER,
                status TEXT,
                payload TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_type TEXT,
                value TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permission_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                permissions TEXT,
                expires_at TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS middleware_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                priority INTEGER,
                enabled INTEGER,
                config TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id TEXT UNIQUE NOT NULL,
                name TEXT,
                type TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id TEXT,
                dependency_id TEXT,
                dependency_type TEXT,
                FOREIGN KEY(system_id) REFERENCES system_modules(system_id),
                FOREIGN KEY(dependency_id) REFERENCES system_modules(system_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificate_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                certificate_type TEXT,
                data TEXT,
                fingerprint TEXT,
                issuer TEXT,
                issued_at TEXT,
                expires_at TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_id TEXT UNIQUE NOT NULL,
                name TEXT,
                role TEXT,
                description TEXT,
                domain TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_capability_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_id TEXT,
                capability_name TEXT,
                expertise_level TEXT,
                accuracy REAL,
                FOREIGN KEY(ai_id) REFERENCES ai_capabilities(ai_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_specializations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_id TEXT,
                specialization TEXT,
                FOREIGN KEY(ai_id) REFERENCES ai_capabilities(ai_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                csrf_token TEXT,
                refresh_token TEXT,
                expires_at TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_task(self, task_id: str, task_type: str, priority: int, payload: str) -> bool:
        """存储任务数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO task_data
                    (task_id, task_type, priority, status, payload, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (task_id, task_type, priority, 'pending', payload, 
                      datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"存储任务数据失败: {e}")
            return False
