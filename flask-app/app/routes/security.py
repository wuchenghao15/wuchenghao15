# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, render_template
import json

security_bp = Blueprint('security', __name__, url_prefix='/security')

@security_bp.route('/')
def index():
    """安全监控页面"""
    return render_template('security.html')

@security_bp.route('/permissions')
def permissions():
    """权限管理"""
    return render_template('permissions.html')

@security_bp.route('/audit')
def audit():
    """安全审计"""
    return jsonify({'audit_logs': []})
