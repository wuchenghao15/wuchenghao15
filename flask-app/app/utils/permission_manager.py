# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Permission Manager for MTSCOS AI System
权限管理模块 - 硬件管理员最高权限体系
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import session, request
import sys

ROLE_HIERARCHY = ['guest', 'student', 'parent', 'designer', 'teacher', 'exam_proctor', 
                   'question_manager', 'ai_manager', 'cluster_manager', 'admin', 
                   'super_admin', 'hardware_admin']

ROLES = {
    'guest': {
        'name': '访客',
        'description': '未登录访客',
        'level': 0,
        'permissions': []
    },
    'student': {
        'name': '学生',
        'description': '学生用户',
        'level': 1,
        'permissions': [
            'view_profile', 'change_language', 'view_exams', 'take_exam',
            'view_results', 'view_learning_records',
            'view_student_dashboard', 'view_my_grades', 'view_exam_history',
            'use_ai_chat', 'view_ai_chat_history', 'manage_ai_chat_settings',
            'view_student_notifications', 'manage_student_account',
            'view_k12_materials', 'view_adult_education_materials'
        ]
    },
    'parent': {
        'name': '家长',
        'description': '学生家长',
        'level': 1,
        'permissions': [
            'view_profile', 'change_language', 'view_child_exams',
            'view_child_results', 'view_child_learning_records',
            'view_child_grades', 'view_parent_dashboard',
            'use_ai_chat', 'view_ai_chat_history', 'manage_ai_chat_settings',
            'view_parent_notifications'
        ]
    },
    'teacher': {
        'name': '教师',
        'description': '教师用户',
        'level': 2,
        'permissions': [
            'view_profile', 'change_language', 'view_exams', 'take_exam',
            'view_results', 'view_learning_records',
            'view_teacher_dashboard', 'manage_students', 'manage_homework',
            'manage_teacher_exams', 'view_teacher_grades', 'manage_question_bank',
            'view_teacher_reports', 'view_teacher_papers',
            'use_ai_chat', 'view_ai_chat_history', 'manage_ai_chat_settings',
            'ai_chat_advanced', 'ai_chat_export',
            'view_student_progress', 'generate_teacher_reports',
            'manage_class_groups', 'view_class_statistics'
        ]
    },
    'exam_proctor': {
        'name': '监考员',
        'description': '考试监考人员',
        'level': 2,
        'permissions': [
            'view_profile', 'change_language', 'view_exams',
            'monitor_exams', 'view_exam_status', 'manage_exam_sessions',
            'view_exam_results', 'manage_exam_proctoring',
            'view_proctor_dashboard', 'use_ai_chat', 'view_ai_chat_history'
        ]
    },
    'designer': {
        'name': '设计师',
        'description': '试题设计人员',
        'level': 1,
        'permissions': [
            'view_profile', 'change_language', 'view_exams', 'design_questions',
            'use_ai_chat', 'view_ai_chat_history', 'manage_ai_chat_settings',
            'view_question_designer_dashboard', 'manage_designer_templates'
        ]
    },
    'question_manager': {
        'name': '题库管理员',
        'description': '题库管理专职人员',
        'level': 3,
        'permissions': [
            'view_profile', 'change_language', 'manage_question_bank',
            'manage_question_categories', 'import_questions', 'export_questions',
            'view_question_stats', 'manage_k12_questions', 'manage_adult_questions',
            'view_question_dashboard', 'use_ai_chat', 'ai_chat_advanced',
            'manage_question_tags', 'view_question_quality'
        ]
    },
    'ai_manager': {
        'name': 'AI管理员',
        'description': 'AI模型和集群管理',
        'level': 3,
        'permissions': [
            'view_profile', 'change_language', 'manage_ai_models',
            'manage_ai_cluster', 'view_ai_status', 'view_ai_performance',
            'manage_ai_configurations', 'view_ai_dashboard',
            'use_ai_chat', 'ai_chat_advanced', 'ai_chat_admin',
            'manage_ai_workers', 'view_ai_logs'
        ]
    },
    'cluster_manager': {
        'name': '集群管理员',
        'description': '服务器集群和端口管理',
        'level': 3,
        'permissions': [
            'view_profile', 'change_language', 'manage_cluster_nodes',
            'manage_ports', 'view_cluster_status', 'manage_load_balance',
            'view_cluster_dashboard', 'manage_server_resources',
            'view_resource_monitoring', 'use_ai_chat', 'ai_chat_admin'
        ]
    },
    'admin': {
        'name': '系统管理员',
        'description': '系统管理员',
        'level': 4,
        'permissions': [
            'view_profile', 'change_language', 'view_exams', 'take_exam',
            'create_exam', 'manage_questions', 'view_settings', 'manage_settings',
            'manage_users', 'view_logs', 'manage_system', 'manage_exams',
            'use_ai_chat', 'view_ai_chat_history', 'manage_ai_chat_settings',
            'ai_chat_advanced', 'ai_chat_export', 'ai_chat_admin',
            'manage_permissions', 'view_system_reports', 'manage_system_updates',
            'view_admin_dashboard', 'manage_database_backups', 'view_system_health'
        ]
    },
    'super_admin': {
        'name': '超级管理员',
        'description': '超级管理员 - 完整系统控制',
        'level': 5,
        'permissions': ['*']
    },
    'hardware_admin': {
        'name': '硬件管理员',
        'description': '硬件管理员 - 最高权限,需硬件加密狗',
        'level': 6,
        'permissions': ['*'],
        'require_hardware': True
    }
}

PAGE_PERMISSIONS = {
    '/': ['guest', 'student', 'parent', 'designer', 'teacher', 'exam_proctor',
          'question_manager', 'ai_manager', 'cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/login': ['guest'],
    '/register': ['guest'],
    '/dashboard': ['student', 'parent', 'designer', 'teacher', 'exam_proctor',
                   'question_manager', 'ai_manager', 'cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/settings': ['admin', 'super_admin', 'hardware_admin'],
    '/admin_center': ['admin', 'super_admin', 'hardware_admin'],
    '/super_admin_dashboard': ['super_admin', 'hardware_admin'],
    '/exam': ['student', 'parent', 'designer', 'teacher', 'exam_proctor',
              'question_manager', 'ai_manager', 'cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/exam_system': ['student', 'parent', 'designer', 'teacher', 'exam_proctor',
                     'question_manager', 'ai_manager', 'cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/ai-chat': ['student', 'parent', 'designer', 'teacher', 'exam_proctor',
                 'question_manager', 'ai_manager', 'cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/profile': ['student', 'parent', 'designer', 'teacher', 'exam_proctor',
                 'question_manager', 'ai_manager', 'cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/notifications': ['student', 'parent', 'designer', 'teacher', 'exam_proctor',
                       'question_manager', 'ai_manager', 'cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/api/admin/users': ['admin', 'super_admin', 'hardware_admin'],
    '/api/admin/system': ['admin', 'super_admin', 'hardware_admin'],
    '/api/admin/monitor': ['admin', 'super_admin', 'hardware_admin'],
    '/api/admin/settings': ['admin', 'super_admin', 'hardware_admin'],
    '/api/admin/database': ['super_admin', 'hardware_admin'],
    '/api/admin/permissions': ['super_admin', 'hardware_admin'],
    '/api/admin/hardware': ['hardware_admin'],
    '/api/hardware/verify': ['hardware_admin'],
    '/api/enhancement/database': ['admin', 'super_admin', 'hardware_admin'],
    '/api/enhancement/ports': ['cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/api/enhancement/cluster': ['cluster_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/api/enhancement/ai-cluster': ['ai_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/api/enhancement/ai-models': ['ai_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/api/enhancement/questions': ['question_manager', 'admin', 'super_admin', 'hardware_admin'],
    '/api/enhancement/permissions': ['admin', 'super_admin', 'hardware_admin'],
    '/api/enhancement/git': ['admin', 'super_admin', 'hardware_admin']
}


class HardwareAuthManager:
    """硬件加密狗认证管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_hardware_db()

    def _init_hardware_db(self):
        """初始化硬件认证数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hardware_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardware_id TEXT UNIQUE NOT NULL,
            hardware_name TEXT NOT NULL,
            hardware_type TEXT DEFAULT 'usb',
            bound_user_id INTEGER,
            bound_username TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            use_count INTEGER DEFAULT 0
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hardware_auth_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardware_id TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            auth_result INTEGER NOT NULL,
            auth_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hardware_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            hardware_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_valid INTEGER DEFAULT 1
            )
            ''')
            
            conn.commit()

    def register_hardware_key(self, hardware_id: str, hardware_name: str, hardware_type: str = 'usb') -> bool:
        """注册硬件加密狗"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO hardware_keys
                (hardware_id, hardware_name, hardware_type, is_active)
                VALUES (?, ?, ?, 1)
                ''', (hardware_id, hardware_name, hardware_type))
                
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to register hardware key: {e}")
            return False

    def bind_hardware_to_user(self, hardware_id: str, user_id: int, username: str) -> bool:
        """绑定硬件到用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE hardware_keys
                SET bound_user_id = ?, bound_username = ?, is_active = 1
                WHERE hardware_id = ?
                ''', (user_id, username, hardware_id))
                
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to bind hardware: {e}")
            return False

    def verify_hardware(self, hardware_id: str, user_id: int) -> Tuple[bool, str]:
        """验证硬件是否有效"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT bound_user_id, is_active FROM hardware_keys
                WHERE hardware_id = ?
                ''', (hardware_id,))
                
                result = cursor.fetchone()

            if not result:
                return False, '硬件密钥不存在'

            bound_user_id, is_active = result

            if not is_active:
                return False, '硬件密钥已被禁用'

            if bound_user_id != user_id:
                return False, '硬件密钥与用户不匹配'

            return True, '硬件验证成功'

        except Exception as e:
            return False, f'验证失败: {str(e)}'

    def create_hardware_session(self, session_id: str, hardware_id: str, user_id: int, timeout_hours: int = 8) -> bool:
        """创建硬件会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                expires_at = datetime.now() + timedelta(hours=timeout_hours)
                
                cursor.execute('''
                INSERT INTO hardware_sessions
                (session_id, hardware_id, user_id, expires_at)
                VALUES (?, ?, ?, ?)
                ''', (session_id, hardware_id, user_id, expires_at))
                
                cursor.execute('''
                UPDATE hardware_keys SET last_used_at = ?, use_count = use_count + 1
                WHERE hardware_id = ?
                ''', (datetime.now(), hardware_id))
                
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to create hardware session: {e}")
            return False

    def validate_hardware_session(self, session_id: str, hardware_id: str) -> bool:
        """验证硬件会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT is_valid, expires_at FROM hardware_sessions
                WHERE session_id = ? AND hardware_id = ? AND is_valid = 1
                ''', (session_id, hardware_id))
                
                result = cursor.fetchone()

            if not result:
                return False

            is_valid, expires_at = result
            if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f'):
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate hardware session: {e}")
            return False

    def invalidate_hardware_session(self, session_id: str) -> bool:
        """使硬件会话失效"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE hardware_sessions SET is_valid = 0
                WHERE session_id = ?
                ''', (session_id,))
                
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate hardware session: {e}")
            return False

    def log_hardware_auth(self, hardware_id: str, user_id: int, username: str, success: bool, ip_address: str = '', user_agent: str = ''):
        """记录硬件认证日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO hardware_auth_logs
                (hardware_id, user_id, username, auth_result, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (hardware_id, user_id, username, 1 if success else 0, ip_address, user_agent))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log hardware auth: {e}")

    def get_hardware_keys(self, user_id: int = None) -> List[Dict]:
        """获取硬件密钥列表"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('SELECT * FROM hardware_keys WHERE bound_user_id = ?', (user_id,))
            else:
                cursor.execute('SELECT * FROM hardware_keys')
            
            columns = ['id', 'hardware_id', 'hardware_name', 'hardware_type', 'bound_user_id',
                       'bound_username', 'is_active', 'created_at', 'last_used_at', 'use_count']
            
            keys = []
            for row in cursor.fetchall():
                keys.append(dict(zip(columns, row)))
            
        return keys

    def get_hardware_auth_logs(self, hardware_id: str = None, limit: int = 100) -> List[Dict]:
        """获取硬件认证日志"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            if hardware_id:
                cursor.execute('''
                SELECT * FROM hardware_auth_logs
                WHERE hardware_id = ?
                ORDER BY auth_time DESC LIMIT ?
                ''', (hardware_id, limit))
            else:
                cursor.execute('SELECT * FROM hardware_auth_logs ORDER BY auth_time DESC LIMIT ?', (limit,))
            
            columns = ['id', 'hardware_id', 'user_id', 'username', 'auth_result', 'auth_time', 'ip_address', 'user_agent']
            
            logs = []
            for row in cursor.fetchall():
                logs.append(dict(zip(columns, row)))
            
        return logs


class PermissionManager:
    """权限管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.hardware_auth = HardwareAuthManager(db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            role_level INTEGER DEFAULT 0,
            require_hardware INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permission_code TEXT UNIQUE NOT NULL,
            permission_name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
            role_name TEXT NOT NULL,
            permission_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (role_name, permission_code)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER NOT NULL,
            role_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, role_name)
            )
            ''')
            
            conn.commit()

        self._init_default_roles()
        self._init_default_permissions()

    def _init_default_roles(self):
        """初始化默认角色"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            for role_code, role_info in ROLES.items():
                require_hw = 1 if role_info.get('require_hardware') else 0
                cursor.execute('SELECT COUNT(*) FROM roles WHERE role_name = ?', (role_code,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        'INSERT INTO roles (role_name, display_name, description, role_level, require_hardware) VALUES (?, ?, ?, ?, ?)',
                        (role_code, role_info['name'], role_info['description'], role_info['level'], require_hw)
                    )
            
            conn.commit()

    def _init_default_permissions(self):
        """初始化默认权限并关联角色"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            all_permissions = set()
            for role_code, role_info in ROLES.items():
                if role_info['permissions'] != ['*']:
                    all_permissions.update(role_info['permissions'])
            
            for perm in all_permissions:
                cursor.execute('SELECT COUNT(*) FROM permissions WHERE permission_code = ?', (perm,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        'INSERT INTO permissions (permission_code, permission_name, description) VALUES (?, ?, ?)',
                        (perm, perm.replace('_', ' ').title(), f'权限: {perm}')
                    )
            
            for role_code, role_info in ROLES.items():
                if role_info['permissions'] == ['*']:
                    cursor.execute('SELECT permission_code FROM permissions')
                    perms = [row[0] for row in cursor.fetchall()]
                    for perm in perms:
                        cursor.execute(
                            'INSERT OR IGNORE INTO role_permissions (role_name, permission_code) VALUES (?, ?)',
                            (role_code, perm)
                        )
                else:
                    for perm in role_info['permissions']:
                        cursor.execute(
                            'INSERT OR IGNORE INTO role_permissions (role_name, permission_code) VALUES (?, ?)',
                            (role_code, perm)
                        )
            
            conn.commit()

    def get_role_level(self, role_name: str) -> int:
        """获取角色等级"""
        return ROLES.get(role_name, {}).get('level', 0)

    def is_hardware_required(self, role_name: str) -> bool:
        """检查角色是否需要硬件验证"""
        return ROLES.get(role_name, {}).get('require_hardware', False)

    def compare_roles(self, role1: str, role2: str) -> int:
        """比较两个角色的等级"""
        level1 = self.get_role_level(role1)
        level2 = self.get_role_level(role2)
        if level1 > level2:
            return 1
        elif level1 < level2:
            return -1
        return 0

    def get_user_role(self, user_id: int) -> str:
        """获取用户角色"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT role_name FROM user_roles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,))
            result = cursor.fetchone()
            

        if result:
            return result[0]
        return 'guest'

    def set_user_role(self, user_id: int, role_name: str) -> bool:
        """设置用户角色"""
        if role_name not in ROLES:
            return False

        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    'INSERT OR REPLACE INTO user_roles (user_id, role_name) VALUES (?, ?)',
                    (user_id, role_name)
                )
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                return False
            finally:
                pass

    def get_role_permissions(self, role_name: str) -> List[str]:
        """获取角色权限"""
        if role_name not in ROLES:
            return []

        if ROLES[role_name]['permissions'] == ['*']:
            return ['*']

        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT permission_code FROM role_permissions WHERE role_name = ?', (role_name,))
            perms = [row[0] for row in cursor.fetchall()]
            

        return perms

    def has_permission(self, user_id: int, permission: str) -> bool:
        """检查用户是否有指定权限"""
        role = self.get_user_role(user_id)
        permissions = self.get_role_permissions(role)

        if '*' in permissions:
            return True

        return permission in permissions

    def check_page_access(self, user_id: Optional[int], path: str) -> bool:
        """检查用户是否有权限访问页面"""
        if path in PAGE_PERMISSIONS:
            allowed_roles = PAGE_PERMISSIONS[path]

            if not user_id:
                return 'guest' in allowed_roles

            user_role = self.get_user_role(user_id)
            return user_role in allowed_roles

        return True

    def check_hardware_access(self, user_id: int, hardware_id: str) -> Tuple[bool, str]:
        """检查硬件访问权限"""
        user_role = self.get_user_role(user_id)

        if not self.is_hardware_required(user_role):
            return True, '该角色不需要硬件验证'

        verified, message = self.hardware_auth.verify_hardware(hardware_id, user_id)
        return verified, message

    def requires_hardware_auth(self, role_name: str) -> bool:
        """检查角色是否需要硬件认证"""
        return self.is_hardware_required(role_name)

    def get_all_roles(self) -> List[Dict]:
        """获取所有角色"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT role_name, display_name, description, role_level, require_hardware FROM roles')
            roles = []
            for row in cursor.fetchall():
                roles.append({
                    'role_name': row[0],
                    'display_name': row[1],
                    'description': row[2],
                    'role_level': row[3],
                    'require_hardware': bool(row[4])
                })
            
        return roles

    def get_all_permissions(self) -> List[Dict]:
        """获取所有权限"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT permission_code, permission_name, description FROM permissions')
            perms = []
            for row in cursor.fetchall():
                perms.append({
                    'permission_code': row[0],
                    'permission_name': row[1],
                    'description': row[2]
                })
            
        return perms


permission_manager: Optional[PermissionManager] = None


def init_permission_manager(db_path: str):
    """初始化权限管理器"""
    global permission_manager
    permission_manager = PermissionManager(db_path)
    return permission_manager


def get_permission_manager() -> PermissionManager:
    """获取权限管理器实例"""
    global permission_manager
    if permission_manager is None:
        permission_manager = PermissionManager('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db')
    return permission_manager


def get_hardware_auth_manager() -> HardwareAuthManager:
    """获取硬件认证管理器"""
    pm = get_permission_manager()
    return pm.hardware_auth


def check_permission(permission: str):
    """装饰器:检查权限"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return {'success': False, 'error': 'Unauthorized', 'message': '请先登录'}, 401

            pm = get_permission_manager()
            if not pm.has_permission(user_id, permission):
                return {'success': False, 'error': 'Forbidden', 'message': '没有权限访问此资源'}, 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


def check_role(allowed_roles: List[str]):
    """装饰器:检查角色"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            pm = get_permission_manager()

            if user_id:
                user_role = pm.get_user_role(user_id)
            else:
                user_role = 'guest'

            if user_role not in allowed_roles:
                return {'success': False, 'error': 'Forbidden', 'message': '没有权限访问此资源'}, 403

            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_hardware_auth(f):
    """装饰器:需要硬件认证"""
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return {'success': False, 'error': 'Unauthorized', 'message': '请先登录'}, 401

        pm = get_permission_manager()
        user_role = pm.get_user_role(user_id)

        if pm.requires_hardware_auth(user_role):
            hardware_session = session.get('hardware_session_id')
            hardware_id = session.get('hardware_id')

            if not hardware_session or not hardware_id:
                return {'success': False, 'error': 'HardwareRequired', 'message': '需要硬件加密狗才能使用此权限'}, 403

            ham = get_hardware_auth_manager()
            if not ham.validate_hardware_session(hardware_session, hardware_id):
                return {'success': False, 'error': 'HardwareSessionInvalid', 'message': '硬件会话已失效,请重新验证'}, 403

        return f(*args, **kwargs)
    return wrapper
