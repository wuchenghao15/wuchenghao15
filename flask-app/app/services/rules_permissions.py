# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""规则与权限模块 - 增强版"""
import logging
import time
import uuid
import json
import sqlite3
import threading
from datetime import datetime
from enum import Enum
from collections import defaultdict
from typing import Dict, Any, List, Callable, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    NONE = 0
    VIEW = 1
    EDIT = 2
    MANAGE = 3
    ADMIN = 4
    SUPER_ADMIN = 5


class ResourceType(Enum):
    USER = "user"
    ROLE = "role"
    EXAM = "exam"
    QUESTION = "question"
    SETTING = "setting"
    REPORT = "report"
    DATA = "data"
    SYSTEM = "system"


class ActionType(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    VIEW = "view"
    MANAGE = "manage"


class AuditAction(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    GRANT = "grant"
    REVOKE = "revoke"
    UPDATE = "update"
    ACCESS_DENIED = "access_denied"
    ACCESS_GRANTED = "access_granted"


class PermissionManager:
    def __init__(self):
        self.permissions = {}
        self.roles = {}
        self.role_permissions = {}
        self.rules = {}
        self.user_roles: Dict[str, List[Dict]] = {}
        
        self.lock = threading.Lock()
        self.cache_lock = threading.Lock()
        self.user_permissions_cache: Dict[str, set] = {}
        
        self._init_database()
        self._load_default_roles()
        
        logger.info("权限管理器初始化完成")

    def _init_database(self):
        """初始化数据库"""
        try:
            db_path = 'permission_manager.db'
            self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    role_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    level INTEGER NOT NULL,
                    is_system BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at REAL,
                    updated_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permission_rules (
                    rule_id TEXT PRIMARY KEY,
                    role_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    actions TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    conditions TEXT,
                    expires_at REAL,
                    created_at REAL,
                    FOREIGN KEY (role_id) REFERENCES roles(role_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    granted_at REAL,
                    granted_by TEXT,
                    expires_at REAL,
                    is_active BOOLEAN DEFAULT TRUE,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (role_id) REFERENCES roles(role_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_records (
                    audit_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    details TEXT,
                    timestamp REAL,
                    ip_address TEXT,
                    success BOOLEAN DEFAULT TRUE
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_permission_rules_role ON permission_rules(role_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_records_timestamp ON audit_records(timestamp)')
            
            self.db_conn.commit()
            logger.info("权限管理数据库初始化完成")
        except Exception as e:
            logger.error(f"权限管理数据库初始化失败: {str(e)}")

    def _load_default_roles(self):
        """加载默认角色"""
        default_roles = [
            {'role_id': 'guest', 'name': '访客', 'description': '系统访客，只读权限', 'level': PermissionLevel.NONE.value, 'is_system': True},
            {'role_id': 'user', 'name': '普通用户', 'description': '普通用户权限', 'level': PermissionLevel.VIEW.value, 'is_system': True},
            {'role_id': 'teacher', 'name': '教师', 'description': '教师权限', 'level': PermissionLevel.EDIT.value, 'is_system': True},
            {'role_id': 'researcher', 'name': '教研员', 'description': '教研员权限', 'level': PermissionLevel.MANAGE.value, 'is_system': True},
            {'role_id': 'admin', 'name': '管理员', 'description': '系统管理员权限', 'level': PermissionLevel.ADMIN.value, 'is_system': True},
            {'role_id': 'super_admin', 'name': '超级管理员', 'description': '超级管理员权限', 'level': PermissionLevel.SUPER_ADMIN.value, 'is_system': True},
            {'role_id': 'hardware_admin', 'name': '硬件管理员', 'description': '硬件管理权限', 'level': PermissionLevel.SUPER_ADMIN.value, 'is_system': True}
        ]
        
        with self.lock:
            for role in default_roles:
                if role['role_id'] not in self.roles:
                    self.roles[role['role_id']] = role
                    self._save_role(role)

    def _save_role(self, role: Dict):
        """保存角色到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO roles 
                (role_id, name, description, level, is_system, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                role['role_id'],
                role['name'],
                role['description'],
                role['level'],
                role.get('is_system', False),
                role.get('is_active', True),
                role.get('created_at', time.time()),
                role.get('updated_at', time.time())
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存角色失败: {str(e)}")

    def define_permission(self, permission_id: str, description: str):
        """定义权限"""
        self.permissions[permission_id] = {'id': permission_id, 'description': description, 'created_at': datetime.now().isoformat()}
        logger.info(f"定义权限: {permission_id}")

    def define_role(self, role_id: str, description: str, level: PermissionLevel = PermissionLevel.VIEW):
        """定义角色"""
        role = {
            'role_id': role_id,
            'name': role_id,
            'description': description,
            'level': level.value,
            'is_system': False,
            'is_active': True,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        self.roles[role_id] = role
        if role_id not in self.role_permissions:
            self.role_permissions[role_id] = []
        self._save_role(role)
        logger.info(f"定义角色: {role_id}")

    def assign_permission_to_role(self, role_id: str, permission_id: str):
        """分配权限给角色"""
        with self.lock:
            if role_id not in self.role_permissions:
                self.role_permissions[role_id] = []
            if permission_id not in self.role_permissions[role_id]:
                self.role_permissions[role_id].append(permission_id)
                self._invalidate_cache()
                logger.info(f"分配权限 {permission_id} 给角色 {role_id}")

    def check_permission(self, role_id: str, permission_id: str) -> bool:
        """检查角色是否有权限"""
        if role_id in self.role_permissions:
            return permission_id in self.role_permissions[role_id]
        return False

    def add_rule(self, rule_id: str, condition: Callable, action=None, priority: int = 1):
        """添加规则"""
        self.rules[rule_id] = {'condition': condition, 'action': action, 'priority': priority, 'enabled': True}
        logger.info(f"添加规则: {rule_id}")

    def evaluate_rules(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估规则"""
        results = []
        sorted_rules = sorted(self.rules.items(), key=lambda x: x[1]['priority'], reverse=True)
        for rule_id, rule in sorted_rules:
            if rule['enabled']:
                try:
                    if rule['condition'](context):
                        result = {'rule_id': rule_id, 'matched': True, 'priority': rule['priority']}
                        if rule['action']:
                            result['action_result'] = rule['action'](context)
                        results.append(result)
                except Exception as e:
                    logger.error(f"规则评估失败 {rule_id}: {str(e)}")
        return results

    def create_role(self, name: str, description: str = "", level: PermissionLevel = PermissionLevel.VIEW) -> str:
        """创建角色"""
        role_id = f"role_{uuid.uuid4().hex[:8]}"
        role = {
            'role_id': role_id,
            'name': name,
            'description': description,
            'level': level.value,
            'is_system': False,
            'is_active': True,
            'created_at': time.time(),
            'updated_at': time.time()
        }
        with self.lock:
            self.roles[role_id] = role
            self._save_role(role)
            if role_id not in self.role_permissions:
                self.role_permissions[role_id] = []
        logger.info(f"创建角色: {name} ({role_id})")
        return role_id

    def get_role(self, role_id: str) -> Optional[Dict]:
        """获取角色"""
        with self.lock:
            return self.roles.get(role_id)

    def update_role(self, role_id: str, **kwargs) -> bool:
        """更新角色"""
        with self.lock:
            role = self.roles.get(role_id)
            if not role:
                logger.error(f"角色不存在: {role_id}")
                return False
            
            if 'name' in kwargs:
                role['name'] = kwargs['name']
            if 'description' in kwargs:
                role['description'] = kwargs['description']
            if 'level' in kwargs:
                role['level'] = kwargs['level'].value if isinstance(kwargs['level'], PermissionLevel) else kwargs['level']
            if 'is_active' in kwargs:
                role['is_active'] = kwargs['is_active']
            
            role['updated_at'] = time.time()
            self._save_role(role)
        
        logger.info(f"更新角色: {role_id}")
        return True

    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        with self.lock:
            role = self.roles.get(role_id)
            if not role:
                logger.error(f"角色不存在: {role_id}")
                return False
            
            if role.get('is_system', False):
                logger.error(f"不能删除系统角色: {role_id}")
                return False
            
            del self.roles[role_id]
            if role_id in self.role_permissions:
                del self.role_permissions[role_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM roles WHERE role_id = ?', (role_id,))
            cursor.execute('DELETE FROM permission_rules WHERE role_id = ?', (role_id,))
            cursor.execute('DELETE FROM user_roles WHERE role_id = ?', (role_id,))
            self.db_conn.commit()
            self._invalidate_cache()
        
        logger.info(f"删除角色: {role_id}")
        return True

    def list_roles(self) -> List[Dict]:
        """列出所有角色"""
        with self.lock:
            return [{
                'role_id': role['role_id'],
                'name': role['name'],
                'description': role['description'],
                'level': role['level'],
                'is_system': role.get('is_system', False),
                'is_active': role.get('is_active', True),
                'created_at': role.get('created_at', 0)
            } for role in self.roles.values()]

    def grant_permission(self, role_id: str, resource_type: ResourceType, actions: List[ActionType],
                        resource_id: str = None, level: PermissionLevel = PermissionLevel.VIEW,
                        conditions: Dict = None) -> str:
        """授权权限"""
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        if conditions is None:
            conditions = {}
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO permission_rules 
                (rule_id, role_id, resource_type, resource_id, actions, level, conditions, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule_id,
                role_id,
                resource_type.value,
                resource_id,
                ','.join([a.value for a in actions]),
                level.value,
                str(conditions),
                None,
                time.time()
            ))
            self.db_conn.commit()
            
            with self.lock:
                if role_id not in self.role_permissions:
                    self.role_permissions[role_id] = []
                for action in actions:
                    perm_key = f"{resource_type.value}:{action.value}"
                    if perm_key not in self.role_permissions[role_id]:
                        self.role_permissions[role_id].append(perm_key)
                self._invalidate_cache()
            
            logger.info(f"授权权限: {role_id} -> {resource_type.value}")
            return rule_id
        except Exception as e:
            logger.error(f"授权权限失败: {str(e)}")
            return ""

    def revoke_permission(self, rule_id: str) -> bool:
        """撤销权限"""
        with self.lock:
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT role_id FROM permission_rules WHERE rule_id = ?', (rule_id,))
            row = cursor.fetchone()
            if row:
                role_id = row[0]
            
            cursor.execute('DELETE FROM permission_rules WHERE rule_id = ?', (rule_id,))
            self.db_conn.commit()
            
            self._invalidate_cache()
        
        logger.info(f"撤销权限: {rule_id}")
        return True

    def get_permissions_for_role(self, role_id: str) -> List[Dict]:
        """获取角色的所有权限"""
        with self.lock:
            if role_id in self.role_permissions:
                return [{'permission': p} for p in self.role_permissions[role_id]]
            return []

    def assign_role(self, user_id: str, role_id: str, granted_by: str = None) -> bool:
        """分配角色给用户"""
        with self.lock:
            if role_id not in self.roles:
                logger.error(f"角色不存在: {role_id}")
                return False
            
            if user_id not in self.user_roles:
                self.user_roles[user_id] = []
            
            for ur in self.user_roles[user_id]:
                if ur['role_id'] == role_id:
                    ur['is_active'] = True
                    ur['granted_at'] = time.time()
                    ur['granted_by'] = granted_by
                    self._save_user_role(ur)
                    self._invalidate_cache()
                    return True
            
            user_role = {
                'user_id': user_id,
                'role_id': role_id,
                'granted_at': time.time(),
                'granted_by': granted_by,
                'expires_at': None,
                'is_active': True
            }
            
            self.user_roles[user_id].append(user_role)
            self._save_user_role(user_role)
            self._invalidate_cache()
        
        logger.info(f"分配角色: {user_id} -> {role_id}")
        return True

    def _save_user_role(self, user_role: Dict):
        """保存用户角色关联到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_roles 
                (user_id, role_id, granted_at, granted_by, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_role['user_id'],
                user_role['role_id'],
                user_role['granted_at'],
                user_role['granted_by'],
                user_role['expires_at'],
                user_role['is_active']
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存用户角色关联失败: {str(e)}")

    def remove_role(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色"""
        with self.lock:
            if user_id not in self.user_roles:
                logger.error(f"用户不存在: {user_id}")
                return False
            
            user_role = None
            for ur in self.user_roles[user_id]:
                if ur['role_id'] == role_id:
                    user_role = ur
                    break
            
            if not user_role:
                logger.error(f"用户没有该角色: {user_id} -> {role_id}")
                return False
            
            user_role['is_active'] = False
            self._save_user_role(user_role)
            self._invalidate_cache()
        
        logger.info(f"移除角色: {user_id} -> {role_id}")
        return True

    def get_user_roles(self, user_id: str) -> List[Dict]:
        """获取用户的所有角色"""
        with self.lock:
            if user_id not in self.user_roles:
                return []
            
            return [{
                'role_id': ur['role_id'],
                'role_name': self.roles.get(ur['role_id'], {}).get('name', ur['role_id']),
                'granted_at': ur['granted_at'],
                'granted_by': ur['granted_by'],
                'expires_at': ur['expires_at'],
                'is_active': ur['is_active']
            } for ur in self.user_roles[user_id] if ur.get('is_active', True)]

    def has_permission(self, user_id: str, resource_type: str, action: str) -> bool:
        """检查用户是否有权限"""
        permissions = self.get_user_permissions(user_id)
        key = (resource_type, action)
        if key in permissions:
            return True
        return False

    def get_user_permissions(self, user_id: str) -> set:
        """获取用户的所有权限"""
        with self.cache_lock:
            if user_id in self.user_permissions_cache:
                return self.user_permissions_cache[user_id]
        
        permissions = set()
        
        with self.lock:
            if user_id not in self.user_roles:
                return permissions
            
            for user_role in self.user_roles[user_id]:
                if not user_role.get('is_active', True):
                    continue
                
                role_id = user_role['role_id']
                
                if role_id in self.role_permissions:
                    for perm in self.role_permissions[role_id]:
                        parts = perm.split(':')
                        if len(parts) == 2:
                            permissions.add((parts[0], parts[1]))
        
        with self.cache_lock:
            self.user_permissions_cache[user_id] = permissions
        
        return permissions

    def _invalidate_cache(self):
        """失效缓存"""
        with self.cache_lock:
            self.user_permissions_cache.clear()

    def check_access(self, user_id: str, resource_type: str, action: str,
                    resource_id: str = None, ip_address: str = None) -> bool:
        """检查访问权限并记录审计"""
        has_access = self.has_permission(user_id, resource_type, action)
        
        audit_action = AuditAction.ACCESS_GRANTED.value if has_access else AuditAction.ACCESS_DENIED.value
        
        self._log_audit(
            user_id=user_id,
            action=audit_action,
            resource_type=resource_type,
            resource_id=resource_id or "all",
            ip_address=ip_address,
            success=has_access
        )
        
        return has_access

    def _log_audit(self, user_id: str, action: str, resource_type: str, resource_id: str,
                   details: Dict = None, ip_address: str = None, success: bool = True):
        """记录审计日志"""
        if details is None:
            details = {}
        
        audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO audit_records 
                (audit_id, user_id, action, resource_type, resource_id, details, timestamp, ip_address, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audit_id,
                user_id,
                action,
                resource_type,
                resource_id,
                str(details),
                time.time(),
                ip_address,
                success
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")

    def get_audit_records(self, user_id: str = None, action: str = None,
                         start_time: float = None, end_time: float = None) -> List[Dict]:
        """获取审计记录"""
        query = 'SELECT * FROM audit_records WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if action:
            query += ' AND action = ?'
            params.append(action)
        
        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)
        
        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)
        
        query += ' ORDER BY timestamp DESC LIMIT 100'
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'audit_id': row[0],
                'user_id': row[1],
                'action': row[2],
                'resource_type': row[3],
                'resource_id': row[4],
                'details': row[5],
                'timestamp': row[6],
                'ip_address': row[7],
                'success': row[8]
            })
        
        return records

    def get_permission_stats(self) -> Dict:
        """获取权限统计信息"""
        with self.lock:
            total_roles = len(self.roles)
            system_roles = sum(1 for r in self.roles.values() if r.get('is_system', False))
            custom_roles = total_roles - system_roles
            
            total_rules = sum(len(v) for v in self.role_permissions.values())
            
            total_users = len(self.user_roles)
            total_role_assignments = sum(len(roles) for roles in self.user_roles.values())
            
            active_assignments = 0
            for roles in self.user_roles.values():
                active_assignments += sum(1 for r in roles if r.get('is_active', True))
        
        return {
            'total_roles': total_roles,
            'system_roles': system_roles,
            'custom_roles': custom_roles,
            'total_permission_rules': total_rules,
            'total_users_with_roles': total_users,
            'total_role_assignments': total_role_assignments,
            'active_role_assignments': active_assignments
        }


permission_manager = PermissionManager()
rule_engine = PermissionManager()


def init_rules_and_permissions():
    """初始化规则和权限"""
    logger.info("初始化规则和权限...")

    permissions = [
        ('users:read', '查看用户列表'), ('users:write', '创建/修改用户'), ('users:delete', '删除用户'),
        ('system:config', '系统配置'), ('system:logs', '查看系统日志'),
        ('ai:manage', '管理AI'), ('ai:monitor', '监控AI'),
        ('exam:create', '创建考试'), ('exam:view', '查看考试'), ('exam:grade', '批改考试'),
        ('content:read', '读取内容'), ('content:write', '创建/修改内容')
    ]

    for perm_id, desc in permissions:
        permission_manager.define_permission(perm_id, desc)

    roles = [('admin', '系统管理员'), ('teacher', '教师'), ('student', '学生'), ('guest', '访客')]
    for role_id, desc in roles:
        permission_manager.define_role(role_id, desc)

    admin_perms = ['users:read', 'users:write', 'users:delete', 'system:config', 'system:logs', 'ai:manage', 'ai:monitor', 'exam:create', 'exam:view', 'exam:grade', 'content:read', 'content:write']
    teacher_perms = ['exam:create', 'exam:view', 'exam:grade', 'content:read', 'content:write']
    student_perms = ['exam:view', 'content:read']
    guest_perms = ['content:read']

    for perm in admin_perms:
        permission_manager.assign_permission_to_role('admin', perm)
    for perm in teacher_perms:
        permission_manager.assign_permission_to_role('teacher', perm)
    for perm in student_perms:
        permission_manager.assign_permission_to_role('student', perm)
    for perm in guest_perms:
        permission_manager.assign_permission_to_role('guest', perm)

    rule_engine.add_rule('rate_limit', lambda ctx: ctx.get('request_count', 0) > 100, lambda ctx: {'action': 'throttle'}, priority=10)
    rule_engine.add_rule('access_control', lambda ctx: ctx.get('role') != 'admin' and ctx.get('resource') == 'system:config', lambda ctx: {'action': 'deny'}, priority=9)
    rule_engine.add_rule('session_timeout', lambda ctx: ctx.get('session_age', 0) > 3600, lambda ctx: {'action': 'logout'}, priority=8)

    logger.info("规则和权限初始化完成")


if __name__ == "__main__":
    init_rules_and_permissions()