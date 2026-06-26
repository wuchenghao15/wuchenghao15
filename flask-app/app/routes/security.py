# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, render_template, session, redirect, url_for
import json

security_bp = Blueprint('security', __name__, url_prefix='/security')

def requires_admin(func):
    """管理员权限装饰器"""
    def decorated(*args, **kwargs):
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            return render_template('error.html',
                                 error_code=403,
                                 error_title='权限不足',
                                 error_message='您没有权限访问此资源',
                                 error_suggestion='如需访问，请联系管理员'), 403
        return func(*args, **kwargs)
    decorated.__name__ = func.__name__
    return decorated

@security_bp.route('/')
@requires_admin
def index():
    """安全监控页面"""
    from datetime import datetime
    return render_template('security.html', last_check=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@security_bp.route('/permissions')
@requires_admin
def permissions():
    """权限管理"""
    return render_template('permissions.html')

@security_bp.route('/audit')
@requires_admin
def audit():
    """安全审计"""
    return jsonify({'audit_logs': []})
