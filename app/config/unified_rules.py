#!/usr/bin/env python3
"""统一角色权限规则"""

ROLE_LEVELS = {
    'super_admin': 100,
    'system_admin': 90,
    'admin': 80,
    'designer': 70,
    'teacher': 60,
    'student_vip': 50,
    'student': 40,
    'user': 20,
    'guest': 0
}

ROLE_PERMISSIONS = {
    'super_admin': ['*'],
    'system_admin': ['manage_users', 'manage_exams', 'manage_courses', 'manage_settings',
                     'view_users', 'view_exams', 'view_courses', 'view_settings',
                     'view_notifications', 'view_data_analysis', 'view_ai_center'],
    'admin': ['manage_users', 'manage_exams', 'manage_courses', 'manage_settings',
              'view_users', 'view_exams', 'view_courses', 'view_settings',
              'view_notifications', 'view_data_analysis', 'view_ai_center',
              'view_resource_manager', 'view_monitor', 'view_health_monitor',
              'approve_basic', 'submit_for_approval'],
    'designer': ['manage_courses', 'view_courses', 'view_exams', 'view_profile'],
    'teacher': ['view_exams', 'view_courses', 'view_notifications', 'view_profile',
                'manage_exams', 'view_students'],
    'student_vip': ['view_exams', 'view_courses', 'view_profile', 'view_ai_tutor'],
    'student': ['view_exams', 'view_courses', 'view_profile'],
    'user': ['view_profile'],
    'guest': []
}


def get_role_level(role):
    """获取角色等级"""
    return ROLE_LEVELS.get(role, 0)


def get_role_permissions(role):
    """获取角色权限列表"""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role, permission):
    """检查角色是否有指定权限"""
    perms = get_role_permissions(role)
    if '*' in perms:
        return True
    return permission in perms


def can_access(role, required_role):
    """检查角色是否可以访问需要特定角色的资源"""
    if role == 'super_admin':
        return True
    return get_role_level(role) >= get_role_level(required_role)
