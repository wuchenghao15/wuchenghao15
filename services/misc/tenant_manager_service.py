#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS多租户管理服务
提供租户隔离和资源管理功能
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


class Tenant:
    """租户"""

    def __init__(self, tenant_id: str, name: str, plan: str = 'free',
                 status: str = 'active', description: str = '',
                 max_users: int = 10, max_storage: int = 1024 * 1024 * 1024,
                 max_api_calls: int = 10000, created_at: str = None):
        self.tenant_id = tenant_id
        self.name = name
        self.plan = plan  # free, basic, pro, enterprise
        self.status = status  # active, suspended, terminated
        self.description = description
        self.max_users = max_users
        self.max_storage = max_storage
        self.max_api_calls = max_api_calls
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.settings: Dict[str, Any] = {}
        self.used_storage = 0
        self.used_users = 0
        self.used_api_calls = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'name': self.name,
            'plan': self.plan,
            'status': self.status,
            'description': self.description,
            'max_users': self.max_users,
            'max_storage': self.max_storage,
            'max_api_calls': self.max_api_calls,
            'used_storage': self.used_storage,
            'used_users': self.used_users,
            'used_api_calls': self.used_api_calls,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'settings': self.settings
        }


class TenantUser:
    """租户用户关联"""

    def __init__(self, tenant_id: str, user_id: str, role: str = 'member',
                 joined_at: str = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role  # owner, admin, member, guest
        self.joined_at = joined_at or datetime.now().isoformat()
        self.last_active = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at,
            'last_active': self.last_active
        }


PLAN_CONFIGS = {
    'free': {
        'max_users': 10,
        'max_storage': 1024 * 1024 * 1024,  # 1GB
        'max_api_calls': 10000
    },
    'basic': {
        'max_users': 50,
        'max_storage': 10 * 1024 * 1024 * 1024,  # 10GB
        'max_api_calls': 100000
    },
    'pro': {
        'max_users': 200,
        'max_storage': 100 * 1024 * 1024 * 1024,  # 100GB
        'max_api_calls': 1000000
    },
    'enterprise': {
        'max_users': 10000,
        'max_storage': 1024 * 1024 * 1024 * 1024,  # 1TB
        'max_api_calls': 10000000
    }
}


class TenantManagerService:
    """多租户管理服务"""

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_users: Dict[str, List[TenantUser]] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.current_tenant_context = threading.local()

        self._init_database()
        self._register_default_tenants()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    plan TEXT DEFAULT 'free',
                    status TEXT DEFAULT 'active',
                    description TEXT,
                    max_users INTEGER DEFAULT 10,
                    max_storage INTEGER DEFAULT 1073741824,
                    max_api_calls INTEGER DEFAULT 10000,
                    used_storage INTEGER DEFAULT 0,
                    used_users INTEGER DEFAULT 0,
                    used_api_calls INTEGER DEFAULT 0,
                    settings TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenant_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_active TEXT,
                    UNIQUE(tenant_id, user_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenant_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    amount INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tenants_id ON tenants(tenant_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant ON tenant_users(tenant_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tenant_users_user ON tenant_users(user_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[租户] 初始化数据库失败: {e}")

    def _register_default_tenants(self):
        """注册默认租户"""
        defaults = [
            Tenant('tenant_default', '默认租户', 'enterprise',
                  description='系统默认租户', max_users=10000,
                  max_storage=1024 * 1024 * 1024 * 1024,
                  max_api_calls=10000000),
            Tenant('tenant_demo', '演示租户', 'pro',
                  description='演示用租户', max_users=200,
                  max_storage=100 * 1024 * 1024 * 1024,
                  max_api_calls=1000000),
            Tenant('tenant_trial', '试用租户', 'free',
                  description='免费试用租户', max_users=10,
                  max_storage=1024 * 1024 * 1024,
                  max_api_calls=10000),
        ]

        for tenant in defaults:
            if tenant.tenant_id not in self.tenants:
                self.tenants[tenant.tenant_id] = tenant
                self._save_tenant_to_db(tenant)

    def _generate_tenant_id(self) -> str:
        import uuid
        return f"tenant_{uuid.uuid4().hex[:12]}"

    def create_tenant(self, name: str, plan: str = 'free',
                      description: str = '') -> str:
        """创建租户"""
        tenant_id = self._generate_tenant_id()

        config = PLAN_CONFIGS.get(plan, PLAN_CONFIGS['free'])

        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            plan=plan,
            description=description,
            max_users=config['max_users'],
            max_storage=config['max_storage'],
            max_api_calls=config['max_api_calls']
        )

        with self.lock:
            self.tenants[tenant_id] = tenant
            self.tenant_users[tenant_id] = []

        self._save_tenant_to_db(tenant)
        logger(f"[租户] 创建租户: {name} ({plan})")

        return tenant_id

    def _save_tenant_to_db(self, tenant: Tenant):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO tenants
                (tenant_id, name, plan, status, description, max_users,
                 max_storage, max_api_calls, used_storage, used_users,
                 used_api_calls, settings, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tenant.tenant_id, tenant.name, tenant.plan, tenant.status,
                tenant.description, tenant.max_users, tenant.max_storage,
                tenant.max_api_calls, tenant.used_storage, tenant.used_users,
                tenant.used_api_calls, json.dumps(tenant.settings),
                tenant.updated_at
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[租户] 保存租户失败: {e}")

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.tenants.get(tenant_id)

    def update_tenant(self, tenant_id: str, name: str = None,
                      plan: str = None, description: str = None,
                      status: str = None) -> bool:
        """更新租户"""
        with self.lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False

            if name:
                tenant.name = name
            if plan:
                tenant.plan = plan
                config = PLAN_CONFIGS.get(plan, PLAN_CONFIGS['free'])
                tenant.max_users = config['max_users']
                tenant.max_storage = config['max_storage']
                tenant.max_api_calls = config['max_api_calls']
            if description is not None:
                tenant.description = description
            if status:
                tenant.status = status

            tenant.updated_at = datetime.now().isoformat()

        self._save_tenant_to_db(tenant)
        return True

    def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        with self.lock:
            if tenant_id not in self.tenants:
                return False

            del self.tenants[tenant_id]
            self.tenant_users.pop(tenant_id, None)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tenants WHERE tenant_id = ?', (tenant_id,))
            cursor.execute('DELETE FROM tenant_users WHERE tenant_id = ?', (tenant_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[租户] 删除租户失败: {e}")

        logger(f"[租户] 删除租户: {tenant_id}")
        return True

    def add_user(self, tenant_id: str, user_id: str,
                 role: str = 'member') -> bool:
        """添加用户到租户"""
        with self.lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False

            if tenant.used_users >= tenant.max_users:
                logger(f"[租户] 用户数已达上限: {tenant_id}")
                return False

            if tenant_id not in self.tenant_users:
                self.tenant_users[tenant_id] = []

            for tu in self.tenant_users[tenant_id]:
                if tu.user_id == user_id:
                    return False

            tu = TenantUser(tenant_id, user_id, role)
            self.tenant_users[tenant_id].append(tu)
            tenant.used_users += 1

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO tenant_users
                (tenant_id, user_id, role)
                VALUES (?, ?, ?)
            ''', (tenant_id, user_id, role))

            cursor.execute('''
                UPDATE tenants SET used_users = ? WHERE tenant_id = ?
            ''', (tenant.used_users, tenant_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[租户] 添加用户失败: {e}")

        return True

    def remove_user(self, tenant_id: str, user_id: str) -> bool:
        """从租户移除用户"""
        with self.lock:
            if tenant_id not in self.tenant_users:
                return False

            users = self.tenant_users[tenant_id]
            for i, tu in enumerate(users):
                if tu.user_id == user_id:
                    users.pop(i)
                    tenant = self.tenants.get(tenant_id)
                    if tenant:
                        tenant.used_users = max(0, tenant.used_users - 1)
                    break
            else:
                return False

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM tenant_users WHERE tenant_id = ? AND user_id = ?
            ''', (tenant_id, user_id))

            if tenant_id in self.tenants:
                cursor.execute('''
                    UPDATE tenants SET used_users = ?
                    WHERE tenant_id = ?
                ''', (self.tenants[tenant_id].used_users, tenant_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[租户] 移除用户失败: {e}")

        return True

    def get_user_tenants(self, user_id: str) -> List[Tenant]:
        """获取用户所属租户"""
        result = []

        with self.lock:
            for tenant_id, users in self.tenant_users.items():
                for tu in users:
                    if tu.user_id == user_id:
                        tenant = self.tenants.get(tenant_id)
                        if tenant:
                            result.append(tenant)
                        break

        return result

    def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """获取租户用户列表"""
        return self.tenant_users.get(tenant_id, [])

    def record_usage(self, tenant_id: str, resource_type: str,
                     amount: int = 1):
        """记录资源使用"""
        with self.lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return

            if resource_type == 'storage':
                tenant.used_storage += amount
            elif resource_type == 'api_call':
                tenant.used_api_calls += amount

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO tenant_usage_logs (tenant_id, resource_type, amount)
                VALUES (?, ?, ?)
            ''', (tenant_id, resource_type, amount))

            if resource_type == 'storage':
                cursor.execute('''
                    UPDATE tenants SET used_storage = ? WHERE tenant_id = ?
                ''', (tenant.used_storage, tenant_id))
            elif resource_type == 'api_call':
                cursor.execute('''
                    UPDATE tenants SET used_api_calls = ? WHERE tenant_id = ?
                ''', (tenant.used_api_calls, tenant_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[租户] 记录使用失败: {e}")

    def check_quota(self, tenant_id: str, resource_type: str,
                    amount: int = 1) -> bool:
        """检查配额"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        if resource_type == 'storage':
            return tenant.used_storage + amount <= tenant.max_storage
        elif resource_type == 'api_call':
            return tenant.used_api_calls + amount <= tenant.max_api_calls
        elif resource_type == 'user':
            return tenant.used_users + amount <= tenant.max_users

        return True

    def set_context(self, tenant_id: str):
        """设置当前租户上下文"""
        self.current_tenant_context.tenant_id = tenant_id

    def get_context(self) -> Optional[str]:
        """获取当前租户上下文"""
        return getattr(self.current_tenant_context, 'tenant_id', None)

    def get_tenants(self, status: str = None) -> List[Tenant]:
        with self.lock:
            if status:
                return [t for t in self.tenants.values() if t.status == status]
            return list(self.tenants.values())

    def get_usage_stats(self, tenant_id: str = None,
                        days: int = 7) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            since = (datetime.now() - timedelta(days=days)).isoformat()

            query = '''
                SELECT resource_type, SUM(amount) as total
                FROM tenant_usage_logs
                WHERE created_at >= ?
            '''
            params = [since]

            if tenant_id:
                query += ' AND tenant_id = ?'
                params.append(tenant_id)

            query += ' GROUP BY resource_type'

            cursor.execute(query, params)

            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = row[1]

            conn.close()
            return stats
        except Exception as e:
            logger(f"[租户] 获取使用统计失败: {e}")
            return {}

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_tenants': len(self.tenants),
                'active_tenants': sum(1 for t in self.tenants.values() if t.status == 'active'),
                'total_users': sum(t.used_users for t in self.tenants.values()),
                'total_storage_used': sum(t.used_storage for t in self.tenants.values()),
                'total_api_calls': sum(t.used_api_calls for t in self.tenants.values())
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[租户] 多租户管理服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[租户] 多租户管理服务已停止")


tenant_manager_service = TenantManagerService()
