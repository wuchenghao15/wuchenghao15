#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本管理服务
将系统版本事实绑定数据库，并同步到各个页面
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from app.utils.logging import logger
from app.models.database_version_manager import db_version_manager


class VersionService:
    """版本管理服务"""
    
    VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'VERSION')
    
    def __init__(self):
        self._init_version_db()
        self._sync_version_to_db()
    
    def _init_version_db(self):
        """初始化版本数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL UNIQUE,
                    major_version INTEGER DEFAULT 1,
                    minor_version INTEGER DEFAULT 0,
                    patch_version INTEGER DEFAULT 0,
                    build_number TEXT,
                    build_date TEXT,
                    build_metadata TEXT,
                    codename TEXT,
                    status TEXT DEFAULT 'stable',
                    description TEXT,
                    features TEXT,
                    release_notes TEXT,
                    is_current INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_key TEXT NOT NULL UNIQUE,
                    fact_value TEXT,
                    data_type TEXT DEFAULT 'string',
                    description TEXT,
                    category TEXT DEFAULT 'version',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    action TEXT NOT NULL,
                    action_by TEXT DEFAULT 'system',
                    action_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            ''')
            
            logger.info("版本管理数据库表初始化完成")
    
    @staticmethod
    def _get_connection():
        """获取数据库连接"""
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _parse_version_file(self) -> Dict[str, Any]:
        """解析VERSION文件"""
        version_data = {}
        if os.path.exists(self.VERSION_FILE):
            with open(self.VERSION_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        version_data[key.strip()] = value.strip()
        return version_data
    
    def _sync_version_to_db(self):
        """将版本文件同步到数据库"""
        version_data = self._parse_version_file()
        
        version = version_data.get('VERSION', '7.4.0')
        version_parts = version.split('.')
        major = int(version_parts[0]) if len(version_parts) > 0 else 1
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        patch = int(version_parts[2]) if len(version_parts) > 2 else 0
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('UPDATE system_version SET is_current = 0 WHERE is_current = 1')
            
            cursor.execute('''
                INSERT OR REPLACE INTO system_version 
                (version, major_version, minor_version, patch_version, build_number, 
                 build_date, build_metadata, codename, status, description, features)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                version, major, minor, patch,
                version_data.get('BUILD_NUMBER', ''),
                version_data.get('BUILD_DATE', datetime.now().strftime('%Y-%m-%d')),
                version_data.get('BUILD_METADATA', ''),
                version_data.get('CODENAME', 'Enhanced Permission Edition'),
                version_data.get('STATUS', 'stable'),
                version_data.get('DESCRIPTION', '系统版本'),
                version_data.get('FEATURE_FLAGS', '')
            ))
            
            try:
                cursor.execute('''
                    INSERT INTO version_history (version, action, action_by, details)
                    VALUES (?, ?, ?, ?)
                ''', (version, 'sync_from_file', 'system', json.dumps(version_data)))
            except sqlite3.IntegrityError:
                pass
            
            logger.info(f"版本已同步到数据库: {version}")
    
    def get_current_version(self) -> Dict[str, Any]:
        """获取当前版本信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_version WHERE is_current = 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}
    
    def get_version_facts(self, category: str = None) -> Dict[str, Any]:
        """获取版本事实"""
        facts = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT fact_key, fact_value, data_type FROM version_facts WHERE category = ? AND is_active = 1", (category,))
            else:
                cursor.execute("SELECT fact_key, fact_value, data_type FROM version_facts WHERE is_active = 1")
            
            for row in cursor.fetchall():
                key = row['fact_key']
                value = row['fact_value']
                data_type = row['data_type']
                
                try:
                    if data_type == 'json':
                        facts[key] = json.loads(value)
                    elif data_type == 'integer':
                        facts[key] = int(value)
                    elif data_type == 'float':
                        facts[key] = float(value)
                    elif data_type == 'boolean':
                        facts[key] = value.lower() == 'true'
                    else:
                        facts[key] = value
                except:
                    facts[key] = value
        
        return facts
    
    def set_version_fact(self, fact_key: str, fact_value: Any, data_type: str = 'string', 
                         description: str = '', category: str = 'version') -> bool:
        """设置版本事实"""
        try:
            if data_type == 'json':
                value_str = json.dumps(fact_value, ensure_ascii=False)
            else:
                value_str = str(fact_value)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO version_facts 
                    (fact_key, fact_value, data_type, description, category, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (fact_key, value_str, data_type, description, category, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            logger.info(f"版本事实已设置: {fact_key} = {fact_value}")
            return True
        except Exception as e:
            logger.error(f"设置版本事实失败: {e}")
            return False
    
    def get_version_for_template(self) -> Dict[str, Any]:
        """获取用于模板渲染的版本信息"""
        version = self.get_current_version()
        facts = self.get_version_facts()
        
        return {
            'version': version.get('version', '7.4.0'),
            'major_version': version.get('major_version', 7),
            'minor_version': version.get('minor_version', 4),
            'patch_version': version.get('patch_version', 0),
            'build_number': version.get('build_number', ''),
            'build_date': version.get('build_date', ''),
            'codename': version.get('codename', ''),
            'status': version.get('status', 'stable'),
            **facts
        }
    
    def get_version_history(self, limit: int = 20) -> list:
        """获取版本历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM version_history ORDER BY id DESC LIMIT {limit}")
            return [dict(row) for row in cursor.fetchall()]
    
    def create_version_record(self, version: str, description: str = '', 
                              features: list = None, release_notes: str = '') -> bool:
        """创建版本记录"""
        try:
            version_parts = version.split('.')
            major = int(version_parts[0]) if len(version_parts) > 0 else 1
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            patch = int(version_parts[2]) if len(version_parts) > 2 else 0
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('UPDATE system_version SET is_current = 0 WHERE is_current = 1')
                
                cursor.execute('''
                    INSERT INTO system_version 
                    (version, major_version, minor_version, patch_version, 
                     build_date, description, features, release_notes, is_current)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    version, major, minor, patch,
                    datetime.now().strftime('%Y-%m-%d'),
                    description,
                    json.dumps(features or [], ensure_ascii=False),
                    release_notes
                ))
                
                try:
                    cursor.execute('''
                        INSERT INTO version_history (version, action, action_by, details)
                        VALUES (?, ?, ?, ?)
                    ''', (version, 'create_version', 'system', description))
                except sqlite3.IntegrityError:
                    pass
            
            db_version_manager.create_version(version, description, features or [])
            
            logger.info(f"版本记录已创建: {version}")
            return True
        except Exception as e:
            logger.error(f"创建版本记录失败: {e}")
            return False
    
    def increment_version(self, level: str = 'patch') -> str:
        """版本号递增"""
        current = self.get_current_version()
        major = current.get('major_version', 5)
        minor = current.get('minor_version', 3)
        patch = current.get('patch_version', 0)
        
        if level == 'major':
            major += 1
            minor = 0
            patch = 0
        elif level == 'minor':
            minor += 1
            patch = 0
        else:
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        self.create_version_record(new_version, f"自动递增版本: {level}")
        
        return new_version


version_service = VersionService()