# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限管理系统 V2.0 (Permission Manager)
增强版权限管理系统，支持角色权限、资源权限、权限继承和动态权限分配
"""

import time
import uuid
import logging
import threading
import sqlite3
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set, Tuple
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('permission_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PermissionManager')

class PermissionLevel(Enum):
    """权限等级枚举"""
    NONE = 0
    VIEW = 1
    EDIT = 2
    MANAGE = 3
    ADMIN = 4
    SUPER_ADMIN = 5

class ResourceType(Enum):
    """资源类型枚举"""
    USER = "user"
    ROLE = "role"
    EXAM = "exam"
    QUESTION = "question"
    SETTING = "setting"
    REPORT = "report"
    DATA = "data"
    SYSTEM = "system"

class ActionType(Enum):
    """操作类型枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    VIEW = "view"
    MANAGE = "manage"

class AuditAction(Enum):
    """审计操作枚举"""
    LOGIN = "login"
    LOGOUT = "logout"
    GRANT = "grant"
    REVOKE = "revoke"
    UPDATE = "update"
    ACCESS_DENIED = "access_denied"
    ACCESS_GRANTED = "access_granted"

@dataclass
class PermissionRule:
    """权限规则"""
    rule_id: str
    role_id: str
    resource_type: ResourceType
    resource_id: Optional[str] = None
    actions: List[ActionType] = None
    level: PermissionLevel = PermissionLevel.VIEW
    conditions: Dict = None
    expires_at: Optional[float] = None
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.conditions is None:
            self.conditions = {}
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class Role:
    """角色"""
    role_id: str
    name: str
    description: str = ""
    level: PermissionLevel = PermissionLevel.VIEW
    is_system: bool = False
    is_active: bool = True
    created_at: float = 0.0
    updated_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class UserRole:
    """用户角色关联"""
    user_id: str
    role_id: str
    granted_at: float = 0.0
    granted_by: Optional[str] = None
    expires_at: Optional[float] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.granted_at == 0.0:
            self.granted_at = time.time()

@dataclass
class AuditRecord:
    """审计记录"""
    audit_id: str
    user_id: str
    action: AuditAction
    resource_type: ResourceType
    resource_id: str
    details: Dict = None
    timestamp: float = 0.0
    ip_address: Optional[str] = None
    success: bool = True
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class PermissionManager:
    """增强版权限管理系统"""
    
    def __init__(self):
        """初始化权限管理器"""
        self.roles: Dict[str, Role] = {}
        self.permission_rules: Dict[str, PermissionRule] = {}
        self.user_roles: Dict[str, List[UserRole]] = {}
        
        self.lock = threading.Lock()
        self.cache_lock = threading.Lock()
        self.user_permissions_cache: Dict[str, Set[Tuple[str, str]]] = {}
        
        self._init_database()
        self._load_default_roles()
        
        logger.info("权限管理系统初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect('permission_manager.db', check_same_thread=False)
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
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def _load_default_roles(self):
        """加载默认角色"""
        default_roles = [
            Role("guest", "访客", "系统访客，只读权限", PermissionLevel.NONE, is_system=True),
            Role("user", "普通用户", "普通用户权限", PermissionLevel.VIEW, is_system=True),
            Role("teacher", "教师", "教师权限", PermissionLevel.EDIT, is_system=True),
            Role("researcher", "教研员", "教研员权限", PermissionLevel.MANAGE, is_system=True),
            Role("admin", "管理员", "系统管理员权限", PermissionLevel.ADMIN, is_system=True),
            Role("super_admin", "超级管理员", "超级管理员权限", PermissionLevel.SUPER_ADMIN, is_system=True),
            Role("hardware_admin", "硬件管理员", "硬件管理权限", PermissionLevel.SUPER_ADMIN, is_system=True)
        ]
        
        with self.lock:
            for role in default_roles:
                if role.role_id not in self.roles:
                    self.roles[role.role_id] = role
                    self._save_role(role)
    
    def _save_role(self, role: Role):
        """保存角色到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO roles 
                (role_id, name, description, level, is_system, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                role.role_id,
                role.name,
                role.description,
                role.level.value,
                role.is_system,
                role.is_active,
                role.created_at,
                role.updated_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存角色失败: {str(e)}")
    
    def create_role(self, name: str, description: str = "", 
                    level: PermissionLevel = PermissionLevel.VIEW) -> str:
        """创建角色"""
        role_id = f"role_{uuid.uuid4().hex[:8]}"
        
        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            level=level
        )
        
        with self.lock:
            self.roles[role_id] = role
            self._save_role(role)
        
        logger.info(f"创建角色: {name} ({role_id})")
        return role_id
    
    def get_role(self, role_id: str) -> Optional[Role]:
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
                role.name = kwargs['name']
            if 'description' in kwargs:
                role.description = kwargs['description']
            if 'level' in kwargs:
                role.level = kwargs['level']
            if 'is_active' in kwargs:
                role.is_active = kwargs['is_active']
            
            role.updated_at = time.time()
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
            
            if role.is_system:
                logger.error(f"不能删除系统角色: {role_id}")
                return False
            
            del self.roles[role_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM roles WHERE role_id = ?', (role_id,))
            cursor.execute('DELETE FROM permission_rules WHERE role_id = ?', (role_id,))
            cursor.execute('DELETE FROM user_roles WHERE role_id = ?', (role_id,))
            self.db_conn.commit()
        
        logger.info(f"删除角色: {role_id}")
        return True
    
    def list_roles(self) -> List[Dict]:
        """列出所有角色"""
        with self.lock:
            return [{
                "role_id": role.role_id,
                "name": role.name,
                "description": role.description,
                "level": role.level.name,
                "is_system": role.is_system,
                "is_active": role.is_active,
                "created_at": role.created_at
            } for role in self.roles.values()]
    
    def grant_permission(self, role_id: str, resource_type: ResourceType, 
                        actions: List[ActionType], resource_id: str = None,
                        level: PermissionLevel = PermissionLevel.VIEW,
                        conditions: Dict = None) -> str:
        """授权权限"""
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        if conditions is None:
            conditions = {}
        
        rule = PermissionRule(
            rule_id=rule_id,
            role_id=role_id,
            resource_type=resource_type,
            resource_id=resource_id,
            actions=actions,
            level=level,
            conditions=conditions
        )
        
        with self.lock:
            self.permission_rules[rule_id] = rule
            self._save_permission_rule(rule)
            self._invalidate_cache()
        
        logger.info(f"授权权限: {role_id} -> {resource_type.value}")
        return rule_id
    
    def _save_permission_rule(self, rule: PermissionRule):
        """保存权限规则到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO permission_rules 
                (rule_id, role_id, resource_type, resource_id, actions, level, conditions, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.rule_id,
                rule.role_id,
                rule.resource_type.value,
                rule.resource_id,
                ",".join([a.value for a in rule.actions]),
                rule.level.value,
                str(rule.conditions),
                rule.expires_at,
                rule.created_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存权限规则失败: {str(e)}")
    
    def revoke_permission(self, rule_id: str) -> bool:
        """撤销权限"""
        with self.lock:
            rule = self.permission_rules.get(rule_id)
            if not rule:
                logger.error(f"权限规则不存在: {rule_id}")
                return False
            
            del self.permission_rules[rule_id]
            
            cursor = self.db_conn.cursor()
            cursor.execute('DELETE FROM permission_rules WHERE rule_id = ?', (rule_id,))
            self.db_conn.commit()
            
            self._invalidate_cache()
        
        logger.info(f"撤销权限: {rule_id}")
        return True
    
    def get_permissions_for_role(self, role_id: str) -> List[Dict]:
        """获取角色的所有权限"""
        with self.lock:
            return [{
                "rule_id": rule.rule_id,
                "resource_type": rule.resource_type.value,
                "resource_id": rule.resource_id,
                "actions": [a.value for a in rule.actions],
                "level": rule.level.name,
                "conditions": rule.conditions
            } for rule in self.permission_rules.values() if rule.role_id == role_id]
    
    def assign_role(self, user_id: str, role_id: str, granted_by: str = None) -> bool:
        """分配角色给用户"""
        with self.lock:
            if role_id not in self.roles:
                logger.error(f"角色不存在: {role_id}")
                return False
            
            if user_id not in self.user_roles:
                self.user_roles[user_id] = []
            
            for ur in self.user_roles[user_id]:
                if ur.role_id == role_id:
                    ur.is_active = True
                    ur.granted_at = time.time()
                    ur.granted_by = granted_by
                    self._save_user_role(ur)
                    self._invalidate_cache()
                    return True
            
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                granted_by=granted_by
            )
            
            self.user_roles[user_id].append(user_role)
            self._save_user_role(user_role)
            self._invalidate_cache()
        
        logger.info(f"分配角色: {user_id} -> {role_id}")
        return True
    
    def _save_user_role(self, user_role: UserRole):
        """保存用户角色关联到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_roles 
                (user_id, role_id, granted_at, granted_by, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_role.user_id,
                user_role.role_id,
                user_role.granted_at,
                user_role.granted_by,
                user_role.expires_at,
                user_role.is_active
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
                if ur.role_id == role_id:
                    user_role = ur
                    break
            
            if not user_role:
                logger.error(f"用户没有该角色: {user_id} -> {role_id}")
                return False
            
            user_role.is_active = False
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
                "role_id": ur.role_id,
                "role_name": self.roles.get(ur.role_id, Role("", "")).name,
                "granted_at": ur.granted_at,
                "granted_by": ur.granted_by,
                "expires_at": ur.expires_at,
                "is_active": ur.is_active
            } for ur in self.user_roles[user_id] if ur.is_active]
    
    def has_permission(self, user_id: str, resource_type: ResourceType, 
                      action: ActionType, resource_id: str = None) -> bool:
        """检查用户是否有权限"""
        permissions = self.get_user_permissions(user_id)
        
        key = (resource_type.value, action.value)
        if key in permissions:
            return True
        
        if resource_id:
            resource_key = (resource_type.value + ":" + resource_id, action.value)
            if resource_key in permissions:
                return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> Set[Tuple[str, str]]:
        """获取用户的所有权限"""
        with self.cache_lock:
            if user_id in self.user_permissions_cache:
                return self.user_permissions_cache[user_id]
        
        permissions: Set[Tuple[str, str]] = set()
        
        with self.lock:
            if user_id not in self.user_roles:
                return permissions
            
            for user_role in self.user_roles[user_id]:
                if not user_role.is_active:
                    continue
                
                role_id = user_role.role_id
                role_level = self.roles.get(role_id)
                
                for rule in self.permission_rules.values():
                    if rule.role_id == role_id:
                        if rule.expires_at and rule.expires_at < time.time():
                            continue
                        
                        resource_key = rule.resource_type.value
                        if rule.resource_id:
                            resource_key += ":" + rule.resource_id
                        
                        for action in rule.actions:
                            permissions.add((resource_key, action.value))
                
                if role_level:
                    permissions.add((role_level.level.name, "access"))
        
        with self.cache_lock:
            self.user_permissions_cache[user_id] = permissions
        
        return permissions
    
    def _invalidate_cache(self):
        """失效缓存"""
        with self.cache_lock:
            self.user_permissions_cache.clear()
    
    def check_access(self, user_id: str, resource_type: ResourceType, 
                    action: ActionType, resource_id: str = None,
                    ip_address: str = None) -> bool:
        """检查访问权限并记录审计"""
        has_access = self.has_permission(user_id, resource_type, action, resource_id)
        
        audit_action = AuditAction.ACCESS_GRANTED if has_access else AuditAction.ACCESS_DENIED
        
        self._log_audit(
            user_id=user_id,
            action=audit_action,
            resource_type=resource_type,
            resource_id=resource_id or "all",
            ip_address=ip_address,
            success=has_access
        )
        
        return has_access
    
    def _log_audit(self, user_id: str, action: AuditAction, 
                   resource_type: ResourceType, resource_id: str,
                   details: Dict = None, ip_address: str = None, 
                   success: bool = True):
        """记录审计日志"""
        if details is None:
            details = {}
        
        audit = AuditRecord(
            audit_id=f"audit_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            success=success
        )
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO audit_records 
                (audit_id, user_id, action, resource_type, resource_id, details, timestamp, ip_address, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audit.audit_id,
                audit.user_id,
                audit.action.value,
                audit.resource_type.value,
                audit.resource_id,
                str(audit.details),
                audit.timestamp,
                audit.ip_address,
                audit.success
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")
    
    def get_audit_records(self, user_id: str = None, action: AuditAction = None,
                         start_time: float = None, end_time: float = None) -> List[Dict]:
        """获取审计记录"""
        query = 'SELECT * FROM audit_records WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if action:
            query += ' AND action = ?'
            params.append(action.value)
        
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
                "audit_id": row[0],
                "user_id": row[1],
                "action": row[2],
                "resource_type": row[3],
                "resource_id": row[4],
                "details": row[5],
                "timestamp": row[6],
                "ip_address": row[7],
                "success": row[8]
            })
        
        return records
    
    def get_permission_stats(self) -> Dict:
        """获取权限统计信息"""
        with self.lock:
            total_roles = len(self.roles)
            system_roles = sum(1 for r in self.roles.values() if r.is_system)
            custom_roles = total_roles - system_roles
            
            total_rules = len(self.permission_rules)
            
            total_users = len(self.user_roles)
            total_role_assignments = sum(len(roles) for roles in self.user_roles.values())
            
            active_assignments = 0
            for roles in self.user_roles.values():
                active_assignments += sum(1 for r in roles if r.is_active)
        
        return {
            "total_roles": total_roles,
            "system_roles": system_roles,
            "custom_roles": custom_roles,
            "total_permission_rules": total_rules,
            "total_users_with_roles": total_users,
            "total_role_assignments": total_role_assignments,
            "active_role_assignments": active_assignments
        }
    
    def validate_permission_hierarchy(self) -> List[Dict]:
        """验证权限层级"""
        issues = []
        
        with self.lock:
            for role_id, role in self.roles.items():
                for rule in self.permission_rules.values():
                    if rule.role_id == role_id:
                        if rule.level.value > role.level.value:
                            issues.append({
                                "type": "level_mismatch",
                                "message": f"权限规则级别({rule.level.name})超过角色级别({role.level.name})",
                                "role_id": role_id,
                                "rule_id": rule.rule_id
                            })
        
        return issues


def test_permission_manager():
    """测试权限管理器"""
    print("权限管理系统 V2.0 测试")
    print("=" * 60)
    
    pm = PermissionManager()
    
    print("列出默认角色:")
    roles = pm.list_roles()
    for role in roles:
        print(f"  {role['role_id']}: {role['name']} - {role['level']}")
    
    print("\n创建自定义角色:")
    new_role_id = pm.create_role("测试角色", "测试角色描述", PermissionLevel.MANAGE)
    print(f"  创建角色成功: {new_role_id}")
    
    print("\n为角色授权:")
    rule_id = pm.grant_permission(
        new_role_id,
        ResourceType.EXAM,
        [ActionType.CREATE, ActionType.READ, ActionType.UPDATE],
        level=PermissionLevel.MANAGE
    )
    print(f"  授权成功: {rule_id}")
    
    print("\n获取角色权限:")
    permissions = pm.get_permissions_for_role(new_role_id)
    for p in permissions:
        print(f"  {p['resource_type']}: {p['actions']}")
    
    print("\n分配角色给用户:")
    pm.assign_role("user123", new_role_id, granted_by="admin")
    pm.assign_role("user123", "teacher")
    print("  角色分配成功")
    
    print("\n获取用户角色:")
    user_roles = pm.get_user_roles("user123")
    for ur in user_roles:
        print(f"  {ur['role_name']}")
    
    print("\n检查权限:")
    has_perm = pm.has_permission("user123", ResourceType.EXAM, ActionType.CREATE)
    print(f"  user123 是否有创建考试权限: {'是' if has_perm else '否'}")
    
    has_perm = pm.has_permission("user123", ResourceType.SYSTEM, ActionType.MANAGE)
    print(f"  user123 是否有管理系统权限: {'是' if has_perm else '否'}")
    
    print("\n检查访问(带审计):")
    access = pm.check_access("user123", ResourceType.EXAM, ActionType.READ, ip_address="192.168.1.100")
    print(f"  访问结果: {'允许' if access else '拒绝'}")
    
    print("\n获取审计记录:")
    records = pm.get_audit_records(user_id="user123")
    for record in records:
        print(f"  {record['action']}: {record['resource_type']} - {'成功' if record['success'] else '失败'}")
    
    print("\n权限统计:")
    stats = pm.get_permission_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n验证权限层级:")
    issues = pm.validate_permission_hierarchy()
    if issues:
        for issue in issues:
            print(f"  ⚠️ {issue['message']}")
    else:
        print("  ✅ 权限层级验证通过")
    
    print("\n删除自定义角色:")
    pm.delete_role(new_role_id)
    print("  删除成功")
    
    print("\n权限管理系统 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_permission_manager()