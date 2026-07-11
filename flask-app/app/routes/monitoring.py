# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, render_template, session, abort
from functools import wraps
import json

monitoring_bp = Blueprint('monitoring', __name__)

def requires_admin(func):
    def decorated(*args, **kwargs):
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin', 'teacher', 'researcher']:
            return render_template('error.html',
                                 error_code=403,
                                 error_title='权限不足',
                                 error_message='您没有权限访问此资源',
                                 error_suggestion='如需访问，请联系管理员'), 403
        return func(*args, **kwargs)
    decorated.__name__ = func.__name__
    return decorated

@monitoring_bp.route('/')
@requires_admin
def index():
    return render_template('monitoring.html')

@monitoring_bp.route('/status')
@requires_admin
def status():
    return jsonify({'status': 'ok', 'message': 'Monitoring is active'})

@monitoring_bp.route('/logs')
@requires_admin
def logs():
    return jsonify({'logs': []})
