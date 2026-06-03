# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限管理模块
"""

import logging
from functools import wraps
from flask import session, jsonify
import json

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
    return role == required_role or role == 'admin'

def is_admin():
    """检查是否为管理员"""
    return session.get('user_level') == 'admin'

def get_current_user_role():
    """获取当前用户角色"""
    return session.get('user_level', 'user')
