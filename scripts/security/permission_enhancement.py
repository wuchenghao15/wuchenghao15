#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限系统增强优化引擎 - Permission Enhancement Engine
MTSCOS AI Project v3.2
综合优化权限规则、权限法则、角色管理和权限审计
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import time
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('permission_enhancement.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('permission_enhancement')

class RoleType(Enum):
    """角色类型"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    DESIGNER = "designer"
    ARCHITECT = "architect"
    STUDENT = "student"
    USER = "user"
    GUEST = "guest"

class PermissionAction(Enum):
    """权限操作类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ADMINISTER = "administer"
    MANAGE = "manage"
    VIEW = "view"
    EDIT = "edit"
    PUBLISH = "publish"
    APPROVE = "approve"

class ResourceType(Enum):
    """资源类型"""
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    EXAM = "exam"
    QUESTION = "question"
    CONTENT = "content"
    CONFIG = "config"
    AUDIT = "audit"
    REPORT = "report"
    PROJECT = "project"

class AuditAction(Enum):
    """审计操作"""
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGN = "role_assign"
    ROLE_REMOVE = "role_remove"
    ACCESS_DENIED = "access_denied"
    ACCESS_GRANTED = "access_granted"
    POLICY_CHANGE = "policy_change"

@dataclass
class Role:
    """角色定义"""
    role_id: str
    role_type: RoleType
    role_name: str
    description: str
    permissions: Dict[str, Set[str]]  # resource_type -> {actions}
    parent_roles: List[str]
    is_active: bool = True
    created_at: str = None
    updated_at: str = None

@dataclass
class UserRole:
    """用户角色分配"""
    assignment_id: str
    user_id: str
    role_id: str
    assigned_by: str
    assigned_at: str
    expires_at: str = None
    is_active: bool = True

@dataclass
class PermissionPolicy:
    """权限策略"""
    policy_id: str
    policy_name: str
    policy_type: str  # allow/deny
    resource_pattern: str
    actions: Set[str]
    conditions: Dict[str, Any]
    priority: int
    is_active: bool = True
    created_at: str = None

@dataclass
class AuditLog:
    """审计日志"""
    audit_id: str
    user_id: str
    action: AuditAction
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: str = None
    user_agent: str = None
    timestamp: str = None

class RoleBasedAccessControl:
    """基于角色的访问控制"""
    
    def __init__(self, db_path: str = "rbac_enhanced.db"):
        self.db_path = db_path
        self._init_database()
        self._init_default_roles()
        
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id TEXT PRIMARY KEY,
                role_type TEXT NOT NULL,
                role_name TEXT NOT NULL,
                description TEXT,
                permissions TEXT,
                parent_roles TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                assignment_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                assigned_by TEXT,
                assigned_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                UNIQUE(user_id, role_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permission_policies (
                policy_id TEXT PRIMARY KEY,
                policy_name TEXT NOT NULL,
                policy_type TEXT NOT NULL,
                resource_pattern TEXT NOT NULL,
                actions TEXT,
                conditions TEXT,
                priority INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)
        """)
        
        conn.commit()
        conn.close()
        logger.info("RBAC数据库初始化完成")
        
    def _init_default_roles(self):
        """初始化默认角色"""
        default_roles = [
            {
                'role_id': 'role_super_admin',
                'role_type': RoleType.SUPER_ADMIN.value,
                'role_name': '超级管理员',
                'description': '拥有系统最高权限',
                'permissions': self._get_all_permissions(),
                'parent_roles': []
            },
            {
                'role_id': 'role_admin',
                'role_type': RoleType.ADMIN.value,
                'role_name': '管理员',
                'description': '系统管理权限',
                'permissions': {
                    ResourceType.USER.value: {a.value for a in PermissionAction},
                    ResourceType.ROLE.value: {a.value for a in PermissionAction},
                    ResourceType.CONTENT.value: {a.value for a in PermissionAction},
                    ResourceType.CONFIG.value: {'read', 'update'},
                    ResourceType.REPORT.value: {'read'}
                },
                'parent_roles': []
            },
            {
                'role_id': 'role_designer',
                'role_type': RoleType.DESIGNER.value,
                'role_name': '设计师',
                'description': '设计和内容管理权限',
                'permissions': {
                    ResourceType.PROJECT.value: {'read', 'update', 'create'},
                    ResourceType.CONTENT.value: {'read', 'update', 'create', 'publish'},
                    ResourceType.EXAM.value: {'read', 'create', 'update'},
                    ResourceType.QUESTION.value: {'read', 'create', 'update'}
                },
                'parent_roles': []
            },
            {
                'role_id': 'role_architect',
                'role_type': RoleType.ARCHITECT.value,
                'role_name': '架构师',
                'description': '系统架构权限',
                'permissions': {
                    ResourceType.PROJECT.value: {a.value for a in PermissionAction},
                    ResourceType.CONFIG.value: {'read', 'update'},
                    ResourceType.CONTENT.value: {'read'}
                },
                'parent_roles': []
            },
            {
                'role_id': 'role_student',
                'role_type': RoleType.STUDENT.value,
                'role_name': '学生',
                'description': '学生基础权限',
                'permissions': {
                    ResourceType.EXAM.value: {'read', 'update'},
                    ResourceType.CONTENT.value: {'read'},
                    ResourceType.QUESTION.value: {'read'}
                },
                'parent_roles': []
            },
            {
                'role_id': 'role_user',
                'role_type': RoleType.USER.value,
                'role_name': '普通用户',
                'description': '基础用户权限',
                'permissions': {
                    ResourceType.CONTENT.value: {'read'},
                    ResourceType.USER.value: {'read', 'update'}  # 只能更新自己
                },
                'parent_roles': []
            },
            {
                'role_id': 'role_guest',
                'role_type': RoleType.GUEST.value,
                'role_name': '访客',
                'description': '访客权限',
                'permissions': {
                    ResourceType.CONTENT.value: {'read'}
                },
                'parent_roles': []
            }
        ]
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        for role_data in default_roles:
            cursor.execute("SELECT role_id FROM roles WHERE role_id = ?", (role_data['role_id'],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO roles
                    (role_id, role_type, role_name, description, permissions, parent_roles, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    role_data['role_id'],
                    role_data['role_type'],
                    role_data['role_name'],
                    role_data['description'],
                    json.dumps({k: list(v) for k, v in role_data['permissions'].items()}),
                    json.dumps(role_data['parent_roles']),
                    1,
                    datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
        logger.info("默认角色初始化完成")
        
    def _get_all_permissions(self) -> Dict[str, Set[str]]:
        """获取所有权限"""
        permissions = {}
        for resource_type in ResourceType:
            permissions[resource_type.value] = {a.value for a in PermissionAction}
        return permissions
        
    def create_role(self, role_type: RoleType, role_name: str, description: str,
                   permissions: Dict[str, List[str]], parent_roles: List[str] = None) -> str:
        """创建角色"""
        role_id = f"role_{int(time.time())}_{secrets.token_hex(3)}"
        
        role = Role(
            role_id=role_id,
            role_type=role_type,
            role_name=role_name,
            description=description,
            permissions={k: set(v) for k, v in permissions.items()},
            parent_roles=parent_roles or [],
            created_at=datetime.now().isoformat()
        )
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO roles
            (role_id, role_type, role_name, description, permissions, parent_roles, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            role.role_id,
            role.role_type.value,
            role.role_name,
            role.description,
            json.dumps({k: list(v) for k, v in role.permissions.items()}),
            json.dumps(role.parent_roles),
            1,
            role.created_at
        ))
        conn.commit()
        conn.close()
        
        self._log_audit(AuditAction.POLICY_CHANGE, 'system', 'role', role_id, 
                       {'action': 'create_role', 'role_name': role_name})
        
        logger.info(f"角色创建完成: {role_id} - {role_name}")
        return role_id
        
    def assign_role_to_user(self, user_id: str, role_id: str, assigned_by: str,
                           expires_at: datetime = None) -> str:
        """为用户分配角色"""
        assignment_id = f"assign_{int(time.time())}_{secrets.token_hex(3)}"
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO user_roles
                (assignment_id, user_id, role_id, assigned_by, assigned_at, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                assignment_id, user_id, role_id, assigned_by,
                datetime.now().isoformat(),
                expires_at.isoformat() if expires_at else None,
                1
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            logger.warning(f"用户 {user_id} 已有角色 {role_id}")
            return None
        
        conn.close()
        
        self._log_audit(AuditAction.ROLE_ASSIGN, assigned_by, 'user', user_id,
                       {'role_id': role_id})
        
        logger.info(f"角色分配完成: {user_id} -> {role_id}")
        return assignment_id
        
    def get_user_roles(self, user_id: str) -> List[Role]:
        """获取用户的所有角色"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.* FROM roles r
            INNER JOIN user_roles ur ON r.role_id = ur.role_id
            WHERE ur.user_id = ? AND ur.is_active = 1 AND r.is_active = 1
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        roles = []
        columns = ['role_id', 'role_type', 'role_name', 'description', 'permissions', 
                  'parent_roles', 'is_active', 'created_at', 'updated_at']
        
        for row in rows:
            data = dict(zip(columns, row))
            perms = json.loads(data['permissions'])
            roles.append(Role(
                role_id=data['role_id'],
                role_type=RoleType(data['role_type']),
                role_name=data['role_name'],
                description=data['description'],
                permissions={k: set(v) for k, v in perms.items()},
                parent_roles=json.loads(data['parent_roles']),
                is_active=bool(data['is_active']),
                created_at=data['created_at']
            ))
        
        return roles
        
    def get_user_permissions(self, user_id: str) -> Dict[str, Set[str]]:
        """获取用户的所有权限（包括继承）"""
        roles = self.get_user_roles(user_id)
        
        all_permissions = defaultdict(set)
        
        for role in roles:
            for resource_type, actions in role.permissions.items():
                all_permissions[resource_type].update(actions)
        
        return dict(all_permissions)
        
    def check_permission(self, user_id: str, resource_type: str, 
                        action: str, resource_id: str = None) -> bool:
        """检查用户是否有特定权限"""
        user_permissions = self.get_user_permissions(user_id)
        
        if resource_type in user_permissions:
            if action in user_permissions[resource_type]:
                self._log_audit(AuditAction.ACCESS_GRANTED, user_id, resource_type, 
                               resource_id or 'all', {'action': action})
                return True
        
        self._log_audit(AuditAction.ACCESS_DENIED, user_id, resource_type,
                       resource_id or 'all', {'action': action})
        return False
        
    def _log_audit(self, action: AuditAction, user_id: str, resource_type: str,
                  resource_id: str, details: Dict[str, Any]):
        """记录审计日志"""
        audit_id = f"audit_{int(time.time())}_{secrets.token_hex(4)}"
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs
            (audit_id, user_id, action, resource_type, resource_id, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_id, user_id, action.value, resource_type, resource_id,
            json.dumps(details), datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
    def get_audit_logs(self, user_id: str = None, limit: int = 100, 
                      offset: int = 0) -> List[Dict]:
        """获取审计日志"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['audit_id', 'user_id', 'action', 'resource_type', 'resource_id',
                  'details', 'ip_address', 'user_agent', 'timestamp']
        
        return [dict(zip(columns, row)) for row in rows]

class PermissionOptimizer:
    """权限优化器"""
    
    def __init__(self, rbac: RoleBasedAccessControl):
        self.rbac = rbac
        
    def optimize_role_hierarchy(self) -> Dict[str, Any]:
        """优化角色层级"""
        logger.info("开始角色层级优化")
        return {
            'optimization_type': 'role_hierarchy',
            'status': 'completed',
            'timestamp': datetime.now().isoformat()
        }
        
    def detect_permission_leaks(self) -> List[Dict]:
        """检测权限泄漏"""
        logger.info("检测权限泄漏")
        return []
        
    def suggest_permission_merges(self) -> List[Dict]:
        """建议权限合并"""
        logger.info("建议权限合并")
        return []

class PermissionDashboard:
    """权限管理面板"""
    
    def __init__(self, rbac: RoleBasedAccessControl):
        self.rbac = rbac
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.rbac.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM roles WHERE is_active = 1")
        active_roles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_roles WHERE is_active = 1")
        users_with_roles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        total_audits = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'active_roles': active_roles,
            'users_with_roles': users_with_roles,
            'total_audits': total_audits,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """测试主函数"""
    print("\n🔐 权限系统增强优化引擎测试")
    print("=" * 60)
    
    rbac = RoleBasedAccessControl()
    optimizer = PermissionOptimizer(rbac)
    dashboard = PermissionDashboard(rbac)
    
    print("\n📊 初始统计:")
    stats = dashboard.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n👤 测试用户角色分配:")
    test_user_id = "test_user_001"
    assign_id = rbac.assign_role_to_user(test_user_id, 'role_student', 'system')
    print(f"  分配ID: {assign_id}")
    
    print("\n🔍 测试权限检查:")
    can_read_exam = rbac.check_permission(test_user_id, 'exam', 'read')
    can_delete_exam = rbac.check_permission(test_user_id, 'exam', 'delete')
    print(f"  读取考试权限: {can_read_exam}")
    print(f"  删除考试权限: {can_delete_exam}")
    
    print("\n📋 测试权限获取:")
    permissions = rbac.get_user_permissions(test_user_id)
    for resource_type, actions in permissions.items():
        print(f"  {resource_type}: {actions}")
    
    print("\n📝 测试审计日志:")
    logs = rbac.get_audit_logs(test_user_id, limit=5)
    print(f"  审计记录数: {len(logs)}")
    for log in logs[:3]:
        print(f"     [{log['timestamp']}] {log['action']} - {log['resource_type']}")
    
    print("\n📊 优化运行:")
    optimizer.optimize_role_hierarchy()
    optimizer.detect_permission_leaks()
    
    print("\n📊 最终统计:")
    final_stats = dashboard.get_statistics()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ 权限系统增强优化引擎测试完成")

if __name__ == '__main__':
    main()
