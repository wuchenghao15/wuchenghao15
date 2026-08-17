#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS API配额服务
提供按用户/租户的API调用配额管理
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


class QuotaPolicy:
    """配额策略"""

    def __init__(self, policy_id: str, name: str,
                 requests_per_minute: int = 60,
                 requests_per_hour: int = 1000,
                 requests_per_day: int = 10000,
                 bandwidth_per_day: int = 1024 * 1024 * 1024,
                 description: str = ''):
        self.policy_id = policy_id
        self.name = name
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.bandwidth_per_day = bandwidth_per_day
        self.description = description
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'requests_per_minute': self.requests_per_minute,
            'requests_per_hour': self.requests_per_hour,
            'requests_per_day': self.requests_per_day,
            'bandwidth_per_day': self.bandwidth_per_day,
            'description': self.description,
            'created_at': self.created_at
        }


class QuotaUsage:
    """配额使用量"""

    def __init__(self, entity_id: str, entity_type: str, policy_id: str):
        self.entity_id = entity_id
        self.entity_type = entity_type  # user, tenant, api_key
        self.policy_id = policy_id
        self.minute_count = 0
        self.hour_count = 0
        self.day_count = 0
        self.bandwidth_used = 0
        self.minute_reset = time.time() + 60
        self.hour_reset = time.time() + 3600
        self.day_reset = time.time() + 86400
        self.total_requests = 0
        self.total_blocked = 0
        self.last_request = None

    def reset_if_needed(self):
        """按需重置计数器"""
        now = time.time()

        if now > self.minute_reset:
            self.minute_count = 0
            self.minute_reset = now + 60

        if now > self.hour_reset:
            self.hour_count = 0
            self.hour_reset = now + 3600

        if now > self.day_reset:
            self.day_count = 0
            self.bandwidth_used = 0
            self.day_reset = now + 86400

    def to_dict(self) -> Dict[str, Any]:
        self.reset_if_needed()
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'policy_id': self.policy_id,
            'minute_count': self.minute_count,
            'hour_count': self.hour_count,
            'day_count': self.day_count,
            'bandwidth_used': self.bandwidth_used,
            'minute_reset': self.minute_reset,
            'hour_reset': self.hour_reset,
            'day_reset': self.day_reset,
            'total_requests': self.total_requests,
            'total_blocked': self.total_blocked,
            'last_request': self.last_request
        }


class APIQuotaService:
    """API配额服务"""

    def __init__(self):
        self.policies: Dict[str, QuotaPolicy] = {}
        self.usages: Dict[str, QuotaUsage] = {}
        self.entity_policies: Dict[str, str] = {}
        self.is_running = False
        self.lock = threading.Lock()

        self._init_database()
        self._register_default_policies()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quota_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    requests_per_minute INTEGER DEFAULT 60,
                    requests_per_hour INTEGER DEFAULT 1000,
                    requests_per_day INTEGER DEFAULT 10000,
                    bandwidth_per_day INTEGER DEFAULT 1073741824,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quota_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    policy_id TEXT NOT NULL,
                    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(entity_id, entity_type)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quota_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    policy_id TEXT,
                    endpoint TEXT,
                    method TEXT,
                    response_size INTEGER DEFAULT 0,
                    allowed INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_quota_policies_id ON quota_policies(policy_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_quota_assignments_entity ON quota_assignments(entity_id, entity_type)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_quota_usage_logs_entity ON quota_usage_logs(entity_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配额] 初始化数据库失败: {e}")

    def _register_default_policies(self):
        """注册默认配额策略"""
        defaults = [
            QuotaPolicy('policy_free', '免费版', 10, 100, 1000,
                       100 * 1024 * 1024, '免费用户配额'),
            QuotaPolicy('policy_basic', '基础版', 30, 500, 5000,
                       500 * 1024 * 1024, '基础版用户配额'),
            QuotaPolicy('policy_pro', '专业版', 60, 2000, 20000,
                       1024 * 1024 * 1024, '专业版用户配额'),
            QuotaPolicy('policy_enterprise', '企业版', 300, 10000, 100000,
                       10 * 1024 * 1024 * 1024, '企业版用户配额'),
            QuotaPolicy('policy_unlimited', '无限制版', 999999, 999999, 999999,
                       999 * 1024 * 1024 * 1024, '无限制配额'),
        ]

        for policy in defaults:
            if policy.policy_id not in self.policies:
                self.policies[policy.policy_id] = policy
                self._save_policy_to_db(policy)

    def _save_policy_to_db(self, policy: QuotaPolicy):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO quota_policies
                (policy_id, name, requests_per_minute, requests_per_hour,
                 requests_per_day, bandwidth_per_day, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                policy.policy_id, policy.name,
                policy.requests_per_minute, policy.requests_per_hour,
                policy.requests_per_day, policy.bandwidth_per_day,
                policy.description
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配额] 保存策略失败: {e}")

    def create_policy(self, name: str, requests_per_minute: int = 60,
                      requests_per_hour: int = 1000,
                      requests_per_day: int = 10000,
                      bandwidth_per_day: int = 1024 * 1024 * 1024,
                      description: str = '') -> str:
        """创建配额策略"""
        import uuid
        policy_id = f"policy_{uuid.uuid4().hex[:12]}"

        policy = QuotaPolicy(
            policy_id=policy_id,
            name=name,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day,
            bandwidth_per_day=bandwidth_per_day,
            description=description
        )

        with self.lock:
            self.policies[policy_id] = policy

        self._save_policy_to_db(policy)
        logger(f"[配额] 创建策略: {name}")

        return policy_id

    def assign_policy(self, entity_id: str, entity_type: str,
                      policy_id: str) -> bool:
        """分配配额策略"""
        with self.lock:
            if policy_id not in self.policies:
                return False

            key = f"{entity_type}_{entity_id}"
            self.entity_policies[key] = policy_id

            if key not in self.usages:
                self.usages[key] = QuotaUsage(entity_id, entity_type, policy_id)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO quota_assignments
                (entity_id, entity_type, policy_id)
                VALUES (?, ?, ?)
            ''', (entity_id, entity_type, policy_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配额] 分配策略失败: {e}")

        return True

    def check_quota(self, entity_id: str, entity_type: str = 'user',
                    response_size: int = 0, endpoint: str = '',
                    method: str = 'GET') -> Dict[str, Any]:
        """检查配额"""
        key = f"{entity_type}_{entity_id}"

        with self.lock:
            policy_id = self.entity_policies.get(key, 'policy_free')
            policy = self.policies.get(policy_id)

            if not policy:
                return {'allowed': True, 'reason': 'no_policy'}

            usage = self.usages.get(key)
            if not usage:
                usage = QuotaUsage(entity_id, entity_type, policy_id)
                self.usages[key] = usage

            usage.reset_if_needed()

            if usage.minute_count >= policy.requests_per_minute:
                usage.total_blocked += 1
                self._log_usage(entity_id, entity_type, policy_id,
                               endpoint, method, response_size, False)
                return {
                    'allowed': False,
                    'reason': 'minute_limit_exceeded',
                    'limit': policy.requests_per_minute,
                    'current': usage.minute_count,
                    'reset_at': usage.minute_reset
                }

            if usage.hour_count >= policy.requests_per_hour:
                usage.total_blocked += 1
                self._log_usage(entity_id, entity_type, policy_id,
                               endpoint, method, response_size, False)
                return {
                    'allowed': False,
                    'reason': 'hour_limit_exceeded',
                    'limit': policy.requests_per_hour,
                    'current': usage.hour_count,
                    'reset_at': usage.hour_reset
                }

            if usage.day_count >= policy.requests_per_day:
                usage.total_blocked += 1
                self._log_usage(entity_id, entity_type, policy_id,
                               endpoint, method, response_size, False)
                return {
                    'allowed': False,
                    'reason': 'day_limit_exceeded',
                    'limit': policy.requests_per_day,
                    'current': usage.day_count,
                    'reset_at': usage.day_reset
                }

            if usage.bandwidth_used + response_size > policy.bandwidth_per_day:
                usage.total_blocked += 1
                self._log_usage(entity_id, entity_type, policy_id,
                               endpoint, method, response_size, False)
                return {
                    'allowed': False,
                    'reason': 'bandwidth_limit_exceeded',
                    'limit': policy.bandwidth_per_day,
                    'current': usage.bandwidth_used,
                    'reset_at': usage.day_reset
                }

            usage.minute_count += 1
            usage.hour_count += 1
            usage.day_count += 1
            usage.bandwidth_used += response_size
            usage.total_requests += 1
            usage.last_request = datetime.now().isoformat()

        self._log_usage(entity_id, entity_type, policy_id,
                       endpoint, method, response_size, True)

        return {
            'allowed': True,
            'remaining_minute': policy.requests_per_minute - usage.minute_count,
            'remaining_hour': policy.requests_per_hour - usage.hour_count,
            'remaining_day': policy.requests_per_day - usage.day_count,
            'remaining_bandwidth': policy.bandwidth_per_day - usage.bandwidth_used
        }

    def _log_usage(self, entity_id: str, entity_type: str,
                   policy_id: str, endpoint: str, method: str,
                   response_size: int, allowed: bool):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO quota_usage_logs
                (entity_id, entity_type, policy_id, endpoint, method,
                 response_size, allowed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity_id, entity_type, policy_id,
                endpoint, method, response_size, 1 if allowed else 0
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[配额] 记录使用失败: {e}")

    def get_usage(self, entity_id: str, entity_type: str = 'user') -> Optional[Dict[str, Any]]:
        """获取使用量"""
        key = f"{entity_type}_{entity_id}"
        usage = self.usages.get(key)

        if not usage:
            return None

        return usage.to_dict()

    def get_policy(self, policy_id: str) -> Optional[QuotaPolicy]:
        return self.policies.get(policy_id)

    def get_policies(self) -> List[QuotaPolicy]:
        return list(self.policies.values())

    def get_entity_policy(self, entity_id: str, entity_type: str = 'user') -> Optional[QuotaPolicy]:
        """获取实体配额策略"""
        key = f"{entity_type}_{entity_id}"
        policy_id = self.entity_policies.get(key, 'policy_free')
        return self.policies.get(policy_id)

    def reset_usage(self, entity_id: str, entity_type: str = 'user'):
        """重置使用量"""
        key = f"{entity_type}_{entity_id}"

        with self.lock:
            if key in self.usages:
                usage = self.usages[key]
                usage.minute_count = 0
                usage.hour_count = 0
                usage.day_count = 0
                usage.bandwidth_used = 0

    def get_usage_logs(self, entity_id: str = None, allowed: bool = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM quota_usage_logs WHERE 1=1'
            params = []

            if entity_id:
                query += ' AND entity_id = ?'
                params.append(entity_id)
            if allowed is not None:
                query += ' AND allowed = ?'
                params.append(1 if allowed else 0)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except Exception as e:
            logger(f"[配额] 获取使用日志失败: {e}")
            return []

    def get_usage_stats(self, entity_id: str = None, days: int = 7) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            since = (datetime.now() - timedelta(days=days)).isoformat()

            query = '''
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN allowed = 1 THEN 1 ELSE 0 END) as allowed_count,
                    SUM(CASE WHEN allowed = 0 THEN 1 ELSE 0 END) as blocked_count,
                    SUM(response_size) as total_bandwidth
                FROM quota_usage_logs
                WHERE created_at >= ?
            '''
            params = [since]

            if entity_id:
                query += ' AND entity_id = ?'
                params.append(entity_id)

            cursor.execute(query, params)

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'total_requests': row[0] or 0,
                    'allowed_requests': row[1] or 0,
                    'blocked_requests': row[2] or 0,
                    'total_bandwidth': row[3] or 0,
                    'block_rate': round((row[2] or 0) / max(1, row[0] or 1) * 100, 2)
                }
            return {}
        except Exception as e:
            logger(f"[配额] 获取使用统计失败: {e}")
            return {}

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_policies': len(self.policies),
                'total_entities': len(self.entity_policies),
                'total_usages': len(self.usages)
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[配额] API配额服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[配额] API配额服务已停止")


api_quota_service = APIQuotaService()
