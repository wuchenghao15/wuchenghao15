#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS API版本管理服务
提供多版本API共存和版本路由功能
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


class APIVersion:
    """API版本"""

    def __init__(self, version_id: str, version: str, status: str = 'active',
                 release_date: str = None, sunset_date: str = None,
                 description: str = '', deprecated: bool = False):
        self.version_id = version_id
        self.version = version
        self.status = status
        self.release_date = release_date or datetime.now().isoformat()
        self.sunset_date = sunset_date
        self.description = description
        self.deprecated = deprecated
        self.endpoints: Dict[str, Dict[str, Any]] = {}
        self.changes: List[Dict[str, Any]] = []
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'version_id': self.version_id,
            'version': self.version,
            'status': self.status,
            'release_date': self.release_date,
            'sunset_date': self.sunset_date,
            'description': self.description,
            'deprecated': self.deprecated,
            'endpoint_count': len(self.endpoints),
            'change_count': len(self.changes),
            'created_at': self.created_at
        }


class APIVersionService:
    """API版本管理服务"""

    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
        self.current_version = 'v1'
        self.is_running = False
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_versions()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id TEXT NOT NULL UNIQUE,
                    version TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    release_date TEXT,
                    sunset_date TEXT,
                    description TEXT,
                    deprecated INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_version_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id TEXT NOT NULL,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    handler TEXT,
                    description TEXT,
                    deprecated INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_version_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    description TEXT,
                    breaking INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_version_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    path TEXT NOT NULL,
                    method TEXT NOT NULL,
                    client_ip TEXT,
                    user_agent TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_api_versions_id ON api_versions(version_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_api_versions_version ON api_versions(version)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_api_version_endpoints_version ON api_version_endpoints(version_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[版本] 初始化数据库失败: {e}")

    def _register_default_versions(self):
        """注册默认API版本"""
        versions = [
            APIVersion('ver_v1', 'v1', 'active',
                      release_date='2025-01-01',
                      description='初始版本'),
            APIVersion('ver_v2', 'v2', 'active',
                      release_date='2025-06-01',
                      description='增强版本，新增高级搜索和数据导出'),
            APIVersion('ver_v3', 'v3', 'active',
                      release_date='2026-01-01',
                      description='企业版本，新增灰度发布和API文档'),
            APIVersion('ver_v4', 'v4', 'active',
                      release_date='2026-07-16',
                      description='分布式版本，新增分布式锁、事件总线等'),
        ]

        for ver in versions:
            if ver.version_id not in self.versions:
                self.versions[ver.version_id] = ver
                self._save_version_to_db(ver)

        self.current_version = 'v4'

    def _generate_version_id(self) -> str:
        import uuid
        return f"ver_{uuid.uuid4().hex[:12]}"

    def create_version(self, version: str, description: str = '',
                      status: str = 'active') -> str:
        version_id = self._generate_version_id()

        ver = APIVersion(
            version_id=version_id,
            version=version,
            status=status,
            description=description
        )

        with self.lock:
            self.versions[version_id] = ver

        self._save_version_to_db(ver)
        self._add_change(version_id, 'release', f'发布版本 {version}', False)
        logger(f"[版本] 创建版本: {version}")

        return version_id

    def _save_version_to_db(self, ver: APIVersion):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO api_versions
                (version_id, version, status, release_date, sunset_date,
                 description, deprecated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                ver.version_id, ver.version, ver.status,
                ver.release_date, ver.sunset_date,
                ver.description, 1 if ver.deprecated else 0
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[版本] 保存版本失败: {e}")

    def deprecate_version(self, version_id: str, sunset_date: str = None) -> bool:
        with self.lock:
            ver = self.versions.get(version_id)
            if not ver:
                return False

            ver.deprecated = True
            ver.status = 'deprecated'
            if sunset_date:
                ver.sunset_date = sunset_date

        self._save_version_to_db(ver)
        self._add_change(version_id, 'deprecation',
                        f'弃用版本 {ver.version}', True)
        logger(f"[版本] 弃用版本: {ver.version}")

        return True

    def sunset_version(self, version_id: str) -> bool:
        with self.lock:
            ver = self.versions.get(version_id)
            if not ver:
                return False

            ver.status = 'sunset'
            ver.sunset_date = datetime.now().isoformat()

        self._save_version_to_db(ver)
        self._add_change(version_id, 'sunset',
                        f'下线版本 {ver.version}', True)
        logger(f"[版本] 下线版本: {ver.version}")

        return True

    def register_endpoint(self, version_id: str, path: str, method: str,
                          handler: str = '', description: str = '',
                          deprecated: bool = False) -> bool:
        with self.lock:
            ver = self.versions.get(version_id)
            if not ver:
                return False

            endpoint_key = f"{method.upper()}_{path}"
            ver.endpoints[endpoint_key] = {
                'path': path,
                'method': method.upper(),
                'handler': handler,
                'description': description,
                'deprecated': deprecated
            }

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO api_version_endpoints
                (version_id, path, method, handler, description, deprecated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                version_id, path, method.upper(),
                handler, description, 1 if deprecated else 0
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[版本] 注册端点失败: {e}")

        return True

    def _add_change(self, version_id: str, change_type: str,
                    description: str, breaking: bool = False):
        with self.lock:
            ver = self.versions.get(version_id)
            if ver:
                ver.changes.append({
                    'type': change_type,
                    'description': description,
                    'breaking': breaking,
                    'timestamp': datetime.now().isoformat()
                })

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO api_version_changes
                (version_id, change_type, description, breaking)
                VALUES (?, ?, ?, ?)
            ''', (version_id, change_type, description, 1 if breaking else 0))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[版本] 记录变更失败: {e}")

    def get_version(self, version_id: str) -> Optional[APIVersion]:
        return self.versions.get(version_id)

    def get_version_by_name(self, version: str) -> Optional[APIVersion]:
        for ver in self.versions.values():
            if ver.version == version:
                return ver
        return None

    def get_versions(self, status: str = None) -> List[APIVersion]:
        with self.lock:
            if status:
                return [v for v in self.versions.values() if v.status == status]
            return list(self.versions.values())

    def get_endpoints(self, version_id: str) -> List[Dict[str, Any]]:
        ver = self.versions.get(version_id)
        if not ver:
            return []
        return list(ver.endpoints.values())

    def get_changes(self, version_id: str) -> List[Dict[str, Any]]:
        ver = self.versions.get(version_id)
        if not ver:
            return []

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM api_version_changes
                WHERE version_id = ?
                ORDER BY created_at DESC
            ''', (version_id,))

            columns = [desc[0] for desc in cursor.description]
            changes = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return changes
        except Exception as e:
            logger(f"[版本] 获取变更失败: {e}")
            return []

    def log_usage(self, version: str, path: str, method: str,
                  client_ip: str = '', user_agent: str = ''):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO api_version_usage_logs
                (version, path, method, client_ip, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (version, path, method, client_ip, user_agent))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[版本] 记录使用失败: {e}")

    def get_usage_stats(self, version: str = None, days: int = 7) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            since = (datetime.now() - timedelta(days=days)).isoformat()

            query = '''
                SELECT version, COUNT(*) as count
                FROM api_version_usage_logs
                WHERE created_at >= ?
            '''
            params = [since]

            if version:
                query += ' AND version = ?'
                params.append(version)

            query += ' GROUP BY version ORDER BY count DESC'

            cursor.execute(query, params)

            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = row[1]

            conn.close()
            return stats
        except Exception as e:
            logger(f"[版本] 获取使用统计失败: {e}")
            return {}

    def resolve_version(self, requested_version: str = None,
                       header_version: str = None,
                       param_version: str = None) -> str:
        """解析请求的API版本"""
        if header_version:
            return header_version

        if param_version:
            return param_version

        if requested_version:
            return requested_version

        return self.current_version

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            active = sum(1 for v in self.versions.values() if v.status == 'active')
            deprecated = sum(1 for v in self.versions.values() if v.status == 'deprecated')
            sunset = sum(1 for v in self.versions.values() if v.status == 'sunset')

            return {
                'status': 'running' if self.is_running else 'stopped',
                'current_version': self.current_version,
                'total_versions': len(self.versions),
                'active_versions': active,
                'deprecated_versions': deprecated,
                'sunset_versions': sunset
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[版本] API版本管理服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[版本] API版本管理服务已停止")


api_version_service = APIVersionService()
