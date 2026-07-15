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
                'admin': ['view_profile', 'view_users', 'view_exams', 'view_courses',
                          'view_settings', 'view_notifications', 'view_data_analysis',
                          'view_resource_manager', 'view_monitor', 'view_health_monitor',
                          'view_ai_center', 'manage_users', 'manage_exams', 'manage_courses',
                          'manage_settings', 'manage_notifications'],
                'system_admin': ['view_profile', 'view_users', 'view_exams', 'view_courses',
                                 'view_settings', 'manage_users', 'manage_exams'],
                'teacher': ['view_profile', 'view_exams', 'view_courses', 'view_notifications'],
                'student': ['view_profile', 'view_exams'],
                'designer': ['view_profile', 'view_courses'],
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
