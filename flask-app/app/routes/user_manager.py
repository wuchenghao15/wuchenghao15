# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, render_template, session
import json

user_manager_bp = Blueprint('user_manager', __name__, url_prefix='/user-manager')

def requires_admin(func):
    """管理员权限装饰器"""
    def decorated(*args, **kwargs):
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        return func(*args, **kwargs)
    decorated.__name__ = func.__name__
    return decorated

@user_manager_bp.route('/')
@requires_admin
def index():
    """用户管理页面"""
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', '')
    }
    return render_template('smart_user_management.html', user=user)

@user_manager_bp.route('/users')
def users():
    """获取用户列表"""
    return jsonify({'users': []})

@user_manager_bp.route('/groups')
def groups():
    """用户组管理"""
    return render_template('user_groups.html')
