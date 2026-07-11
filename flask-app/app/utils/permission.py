# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限管理模块 - 统一权限体系
基于 permission_manager.py 的 ROLE_HIERARCHY 实现权限等级检查
"""

import logging
from functools import wraps
from flask import session, jsonify, request
import json

logger = logging.getLogger('permission')

# 权限等级体系（从低到高）
ROLE_HIERARCHY = ['guest', 'student', 'parent', 'designer', 'teacher', 'exam_proctor', 
                   'question_manager', 'ai_manager', 'cluster_manager', 'admin', 
                   'super_admin', 'hardware_admin']

ROLE_LEVELS = {role: idx for idx, role in enumerate(ROLE_HIERARCHY)}

def permission_required(required_roles):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = session.get('user_level', 'user')
            if role not in required_roles:
                return jsonify({'success': False, 'error': '权限不足'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def check_permission(required_role):
    """检查权限"""
    role = session.get('user_level', 'user')
    return role == required_role or role == 'admin'

def is_admin():
    """检查是否为管理员"""
    return session.get('user_level') == 'admin'

def get_current_user_role():
    """获取当前用户角色"""
    return session.get('user_level', 'user')

def has_role(role):
    """检查是否拥有指定角色"""
    current_role = session.get('user_level', 'guest')
    return current_role == role

def has_level(required_level):
    """检查权限等级"""
    current_role = session.get('user_level', 'guest')
    current_level = ROLE_LEVELS.get(current_role, -1)
    return current_level >= required_level

def require_login(f):
    """登录验证装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return wrapper

def require_role(minimum_role):
    """角色权限装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'error': '请先登录'}), 401
            
            user_role = session.get('user_level', 'guest')
            user_level = ROLE_LEVELS.get(user_role, -1)
            required_level = ROLE_LEVELS.get(minimum_role, 0)
            
            if user_level < required_level:
                return jsonify({
                    'success': False, 
                    'error': f'权限不足，需要{minimum_role}权限',
                    'current_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def require_super_admin(f):
    """超级管理员权限装饰器"""
    return require_role('super_admin')(f)

def require_admin(f):
    """管理员权限装饰器"""
    return require_role('admin')(f)

def require_teacher(f):
    """教师权限装饰器"""
    return require_role('teacher')(f)

def require_parent(f):
    """家长权限装饰器"""
    return require_role('parent')(f)

def require_student(f):
    """学生权限装饰器"""
    return require_role('student')(f)
