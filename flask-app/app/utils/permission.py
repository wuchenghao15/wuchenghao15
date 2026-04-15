#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限管理模块
"""

import logging
from functools import wraps
from flask import session, jsonify

logger = logging.getLogger('permission')

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
    return role in required_role
