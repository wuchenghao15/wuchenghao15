#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据存储管理器 - 使用数据库替代JSON文件存储
"""

import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional


class DataStorageManager:
    """统一数据存储管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认使用flask-app目录下的数据库
            self.db_path = os.path.join(os.path.dirname(__file__), '..', 'app.db')
        else:
            self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 任务数据存储表
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
        
        # 配置数据存储表
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
        
        # 权限数据存储表
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
        
        # 中间件配置表
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
        
        # 系统模块配置表
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
        
        # 系统依赖关系表
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
        
        # 证书数据表
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
        
        # AI能力数据表
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
        
        # AI能力详情表
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
        
        # AI专业领域表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_specializations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ai_id TEXT,
                specialization TEXT,
                FOREIGN KEY(ai_id) REFERENCES ai_capabilities(ai_id)
            )
        ''')
        
        # 会话数据表
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO task_data
                (task_id, task_type, priority, status, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (task_id, task_type, priority, 'pending', payload, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储任务失败: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM task_data WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'task_id': row[1],
                    'task_type': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'payload': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            return None
        except Exception as e:
            print(f"获取任务失败: {e}")
            return None
    
    def store_config(self, config_key: str, config_type: str, value: str) -> bool:
        """存储配置数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO config_data
                (config_key, config_type, value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (config_key, config_type, value, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储配置失败: {e}")
            return False
    
    def get_config(self, config_key: str) -> Optional[str]:
        """获取配置数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM config_data WHERE config_key = ?', (config_key,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"获取配置失败: {e}")
            return None
    
    def store_permission(self, permission_id: str, user_id: int, permissions: str, expires_at: str) -> bool:
        """存储权限数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO permission_data
                (permission_id, user_id, permissions, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (permission_id, user_id, permissions, expires_at, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储权限失败: {e}")
            return False
    
    def get_permission(self, permission_id: str) -> Optional[Dict]:
        """获取权限数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM permission_data WHERE permission_id = ?', (permission_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'permission_id': row[1],
                    'user_id': row[2],
                    'permissions': row[3],
                    'expires_at': row[4],
                    'created_at': row[5]
                }
            return None
        except Exception as e:
            print(f"获取权限失败: {e}")
            return None
    
    def store_middleware_config(self, name: str, priority: int, enabled: bool, config: str) -> bool:
        """存储中间件配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO middleware_config
                (name, priority, enabled, config, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, priority, 1 if enabled else 0, config, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储中间件配置失败: {e}")
            return False
    
    def store_system_module(self, system_id: str, name: str, type: str, status: str) -> bool:
        """存储系统模块"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_modules
                (system_id, name, type, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (system_id, name, type, status, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储系统模块失败: {e}")
            return False
    
    def add_dependency(self, system_id: str, dependency_id: str, dependency_type: str) -> bool:
        """添加系统依赖"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_dependencies
                (system_id, dependency_id, dependency_type)
                VALUES (?, ?, ?)
            ''', (system_id, dependency_id, dependency_type))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加依赖失败: {e}")
            return False
    
    def store_certificate(self, certificate_id: str, user_id: int, certificate_type: str, 
                          data: str, fingerprint: str, issuer: str, 
                          issued_at: str, expires_at: str, status: str) -> bool:
        """存储证书数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO certificate_data
                (certificate_id, user_id, certificate_type, data, fingerprint, 
                 issuer, issued_at, expires_at, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (certificate_id, user_id, certificate_type, data, fingerprint, 
                  issuer, issued_at, expires_at, status, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储证书失败: {e}")
            return False
    
    def get_certificate(self, certificate_id: str) -> Optional[Dict]:
        """获取证书数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM certificate_data WHERE certificate_id = ?', (certificate_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'certificate_id': row[1],
                    'user_id': row[2],
                    'certificate_type': row[3],
                    'data': row[4],
                    'fingerprint': row[5],
                    'issuer': row[6],
                    'issued_at': row[7],
                    'expires_at': row[8],
                    'status': row[9],
                    'created_at': row[10]
                }
            return None
        except Exception as e:
            print(f"获取证书失败: {e}")
            return None
    
    def store_ai_capability(self, ai_id: str, name: str, role: str, description: str, 
                            domain: str, status: str, capabilities: List[str],
                            expertise_levels: Dict[str, str], specializations: List[str],
                            accuracy: float) -> bool:
        """存储AI能力数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 存储AI基本信息
            cursor.execute('''
                INSERT OR REPLACE INTO ai_capabilities
                (ai_id, name, role, description, domain, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ai_id, name, role, description, domain, status, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            
            # 删除旧的能力详情
            cursor.execute('DELETE FROM ai_capability_details WHERE ai_id = ?', (ai_id,))
            
            # 存储能力详情
            for capability_name in capabilities:
                level = expertise_levels.get(capability_name, 'intermediate')
                cursor.execute('''
                    INSERT INTO ai_capability_details
                    (ai_id, capability_name, expertise_level, accuracy)
                    VALUES (?, ?, ?, ?)
                ''', (ai_id, capability_name, level, accuracy))
            
            # 删除旧的专业领域
            cursor.execute('DELETE FROM ai_specializations WHERE ai_id = ?', (ai_id,))
            
            # 存储专业领域
            for specialization in specializations:
                cursor.execute('''
                    INSERT INTO ai_specializations
                    (ai_id, specialization)
                    VALUES (?, ?)
                ''', (ai_id, specialization))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储AI能力失败: {e}")
            return False
    
    def get_ai_capability(self, ai_id: str) -> Optional[Dict]:
        """获取AI能力数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取基本信息
            cursor.execute('SELECT * FROM ai_capabilities WHERE ai_id = ?', (ai_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            # 获取能力详情
            cursor.execute('SELECT capability_name, expertise_level, accuracy FROM ai_capability_details WHERE ai_id = ?', (ai_id,))
            capabilities = []
            expertise_levels = {}
            accuracy = 0.0
            for cap_row in cursor.fetchall():
                capabilities.append(cap_row[0])
                expertise_levels[cap_row[0]] = cap_row[1]
                accuracy = cap_row[2]
            
            # 获取专业领域
            cursor.execute('SELECT specialization FROM ai_specializations WHERE ai_id = ?', (ai_id,))
            specializations = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'ai_id': row[1],
                'name': row[2],
                'role': row[3],
                'description': row[4],
                'domain': row[5],
                'status': row[6],
                'capabilities': capabilities,
                'expertise_level': expertise_levels,
                'specializations': specializations,
                'accuracy': accuracy,
                'created_at': row[7],
                'updated_at': row[8]
            }
        except Exception as e:
            print(f"获取AI能力失败: {e}")
            return None
    
    def store_session(self, session_id: str, user_id: int, csrf_token: str, 
                      refresh_token: str, expires_at: str) -> bool:
        """存储会话数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO session_data
                (session_id, user_id, csrf_token, refresh_token, expires_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, csrf_token, refresh_token, expires_at, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"存储会话失败: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM session_data WHERE session_id = ?', (session_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'session_id': row[1],
                    'user_id': row[2],
                    'csrf_token': row[3],
                    'refresh_token': row[4],
                    'expires_at': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            return None
        except Exception as e:
            print(f"获取会话失败: {e}")
            return None
    
    def generate_key(self, prefix: str = 'key') -> str:
        """生成唯一键 - 使用微秒级时间戳"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')  # 包含微秒
        random_part = hashlib.md5(f"{timestamp}{prefix}{os.urandom(16)}".encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{random_part}"


# 全局实例
storage_manager = DataStorageManager()