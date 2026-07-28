#!/usr/bin/env python3
import logging

logger = logging.getLogger(__name__)

class PermissionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._permissions = {
                'super_admin': ['*'],
                'system_admin': ['manage_users', 'manage_exams', 'manage_courses', 'manage_settings',
                                 'view_users', 'view_exams', 'view_courses', 'view_settings',
                                 'view_notifications', 'view_data_analysis', 'view_ai_center'],
                'admin': ['manage_users', 'manage_exams', 'manage_courses', 'manage_settings',
                          'view_users', 'view_exams', 'view_courses', 'view_settings',
                          'view_notifications', 'view_data_analysis', 'view_ai_center',
                          'view_resource_manager', 'view_monitor', 'view_health_monitor'],
                'hardware_admin': ['view_exams', 'view_courses', 'view_profile', 'view_monitor'],
                'hardware_vikey_admin': ['view_exams', 'view_courses', 'view_profile', 'view_monitor'],
                'designer': ['manage_courses', 'view_courses', 'view_exams', 'view_profile'],
                'teacher': ['view_exams', 'view_courses', 'view_notifications', 'view_profile',
                            'manage_exams', 'view_students'],
                'student_vip': ['view_exams', 'view_courses', 'view_profile', 'view_ai_tutor'],
                'student': ['view_exams', 'view_courses', 'view_profile'],
                'user': ['view_profile'],
                'guest': []
            }
        return cls._instance

    def has_permission(self, user_id, permission):
        from flask import session
        role = session.get('role', 'guest')
        role_perms = self._permissions.get(role, [])
        if '*' in role_perms:
            return True
        return permission in role_perms

    def get_permissions(self, role):
        return self._permissions.get(role, [])

    def get_user_permissions(self, user_id):
        from flask import session
        role = session.get('role', 'guest')
        return self.get_permissions(role)

    def check_role_access(self, required_roles):
        from flask import session
        role = session.get('role', 'guest')
        if '*' in required_roles:
            return True
        return role in required_roles

class HardwareAuthManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._authorized = True
        return cls._instance

    def is_authorized(self):
        return self._authorized

    def authorize(self, hardware_key):
        self._authorized = True
        return True

    def revoke(self):
        self._authorized = False
        return True

def get_permission_manager():
    return PermissionManager()

def get_hardware_auth_manager():
    return HardwareAuthManager()

def is_super_admin(user):
    """
    判断用户是否为超级管理员
    依据PERM_SUPER_ADMIN_UNIQUE_USER规则，只有配置的唯一用户才是真正的super_admin
    """
    if not user:
        return False
    
    username = user.get('username') if isinstance(user, dict) else getattr(user, 'username', None)
    role = user.get('role') if isinstance(user, dict) else getattr(user, 'role', None)
    
    if not username or role != 'super_admin':
        return False
    
    try:
        import sqlite3
        from app import DATABASE_PATH
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT rule_value FROM system_rules WHERE rule_code = ?', 
                         ('PERM_SUPER_ADMIN_UNIQUE_USER',))
            result = cursor.fetchone()
            
            if result and result[0] == username:
                return True
            return False
    except Exception as e:
        logger.error(f"检查超级管理员失败: {e}")
        return False
