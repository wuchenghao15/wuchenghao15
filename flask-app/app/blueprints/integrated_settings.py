# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify, request
from flask import session
import sys
import logging

logger = logging.getLogger(__name__)

integrated_settings_bp = Blueprint('integrated_settings', __name__, url_prefix='/settings')

def require_admin_role():
    """检查是否具有管理员权限"""
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401
    
    if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
        logger.warning(f"[权限检查] 用户 {session.get('username')} ({role}) 尝试访问设置页面，被拒绝")
        return jsonify({'success': False, 'error': 'Forbidden', 'message': '需要管理员权限'}), 403
    
    return None

@integrated_settings_bp.route('/')
def index():
    """集成设置页面"""
    result = require_admin_role()
    if result:
        return result
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', '')
    }
    return render_template('integrated_settings.html', user=user)

@integrated_settings_bp.route('/system')
def system_settings():
    """系统设置"""
    result = require_admin_role()
    if result:
        return result
    return render_template('system_config.html')

@integrated_settings_bp.route('/security')
def security_settings():
    """安全设置"""
    result = require_admin_role()
    if result:
        return result
    return render_template('security_settings.html')
