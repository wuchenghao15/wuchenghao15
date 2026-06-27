#!/usr/bin/env python3
"""
Access Control Middleware for MTSCOS AI System
页面访问校验中间件 - 硬件管理员最高权限体系
"""

from flask import request, session, redirect, url_for, jsonify, make_response, render_template
import logging
logger = logging.getLogger(__name__)
import time
from datetime import datetime
from functools import wraps
from typing import Dict
from app.utils.rule_manager import get_rule_manager, validate_access, check_security_rules

ROLE_HIERARCHY = ['guest', 'student', 'designer', 'admin', 'super_admin', 'hardware_admin']

LOGIN_REQUIRED_PAGES = [
    '/dashboard',
    '/settings',
    '/admin_center',
    '/super_admin_dashboard',
    '/exam',
    '/exam_system',
    '/smart_dashboard'
]

ADMIN_REQUIRED_PAGES = [
    '/admin_center',
    '/api/settings/general',
    '/api/settings/permissions',
    '/api/settings/errors',
    '/admin/student_behavior',
    '/admin/tournament'
]

SETTINGS_PAGES = [
    '/settings',
    '/settings/system',
    '/settings/security'
]

SUPER_ADMIN_REQUIRED_PAGES = [
    '/super_admin_dashboard',
    '/api/admin/database',
    '/api/admin/permissions'
]

HARDWARE_ADMIN_PAGES = [
    '/api/admin/hardware',
    '/api/hardware/verify'
]

PUBLIC_PAGES = [
    '/',
    '/login',
    '/register',
    '/api/health',
    '/api/system/status',
    '/api/user/ip',         # 新增：用户IP获取API（公开访问）
    '/api/user/info',       # 新增：用户信息API（公开访问）
    '/api/admin/dashboard_stats'  # 新增：仪表盘数据API（已登录即可访问）
]

PHYSICS_PATHS = [
    '/physics-engine/',
    '/api/physics/'
]

STATIC_PATHS = [
    '/static/',
    '/assets/',
    '/favicon.ico',
    '/robots.txt'
]


def get_role_level(role: str) -> int:
    """获取角色等级"""
    levels = {'guest': 0, 'student': 1, 'designer': 1, 'admin': 3, 'super_admin': 4, 'hardware_admin': 5, 'hardware_vikey_admin': 5}
    return levels.get(role, 0)


def is_hardware_admin(role: str) -> bool:
    """检查是否是硬件管理员"""
    return role in ['hardware_admin', 'hardware_vikey_admin']


def has_hardware_session() -> bool:
    """检查是否有有效的硬件会话"""
    hardware_session = session.get('hardware_session_id')
    hardware_id = session.get('hardware_id')
    return bool(hardware_session and hardware_id)


def access_control_middleware(app):
    """访问控制中间件 - 硬件管理员最高权限体系"""

    @app.before_request
    def check_access():
        path = request.path

        for static_path in STATIC_PATHS:
            if path.startswith(static_path):
                return None

        user_id = session.get('user_id')
        username = session.get('username')
        role = session.get('role', 'guest')

        if path in PUBLIC_PAGES:
            return None
        
        # 跳过所有公开API路径
        if path.startswith('/api/user/') or path.startswith('/api/admin/') or path.startswith('/api/health') or path.startswith('/api/system/status'):
            return None

        rm = get_rule_manager()
        maintenance_mode = rm.get_rule('SYS_MAINTENANCE_MODE')
        if maintenance_mode and str(maintenance_mode).lower() == 'true':
            if role not in ['super_admin', 'hardware_admin', 'hardware_vikey_admin']:
                return jsonify({
                    'success': False,
                    'error': 'Maintenance',
                    'message': '系统维护中,请稍后再试'
                }), 503

        if path in LOGIN_REQUIRED_PAGES:
            if not user_id:
                log_access(path, None, None, 'guest', 'unauthorized')
                accept_header = request.headers.get('Accept', '')
                # API请求返回JSON，页面请求返回美化的HTML
                if 'application/json' in accept_header or request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': 'Unauthorized',
                        'message': '请先登录'
                    }), 401
                else:
                    # 返回美化的登录提示页面
                    return render_template('login_required.html', request_path=path), 401

        if user_id and role:
            validation_result = validate_access(path, role)
            logger.info(f"[DEBUG] validate_access(path={path}, role={role}) = {validation_result}")
            if not validation_result:
                log_access(path, user_id, username, role, 'forbidden')
                return jsonify({
                    'success': False,
                    'error': 'Forbidden',
                    'message': '您没有权限访问此资源'
                }), 403

        if path in ADMIN_REQUIRED_PAGES:
            if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
                log_access(path, user_id, username, role, 'forbidden')
                return jsonify({
                    'success': False,
                    'error': 'Forbidden',
                    'message': '需要管理员权限'
                }), 403

        if path in SETTINGS_PAGES or path.startswith('/settings/'):
            if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
                log_access(path, user_id, username, role, 'forbidden')
                return jsonify({
                    'success': False,
                    'error': 'Forbidden',
                    'message': '需要管理员权限'
                }), 403

        if path in SUPER_ADMIN_REQUIRED_PAGES:
            if role not in ['super_admin', 'hardware_admin', 'hardware_vikey_admin']:
                log_access(path, user_id, username, role, 'forbidden')
                return jsonify({
                    'success': False,
                    'error': 'Forbidden',
                    'message': '需要超级管理员权限'
                }), 403

        if path in HARDWARE_ADMIN_PAGES:
            if role not in ['hardware_admin', 'hardware_vikey_admin']:
                log_access(path, user_id, username, role, 'forbidden')
                return jsonify({
                    'success': False,
                    'error': 'Forbidden',
                    'message': '需要硬件管理员权限'
                }), 403

            hw_auth_required = rm.get_rule('HW_AUTH_REQUIRED')
            if hw_auth_required and str(hw_auth_required).lower() == 'true':
                if not has_hardware_session():
                    return jsonify({
                        'success': False,
                        'error': 'HardwareRequired',
                        'message': '需要硬件加密狗才能使用此权限'
                    }), 403

        for physics_path in PHYSICS_PATHS:
            if path.startswith(physics_path):
                if role == 'student':
                    log_access(path, user_id, username, role, 'forbidden')
                    return jsonify({
                        'success': False,
                        'error': 'Forbidden',
                        'message': '学生角色不允许访问物理引擎'
                    }), 403
                break

        log_access(path, user_id, username, role, 'allowed')
        rm.apply_rule('ACCESS_' + path.strip('/').upper(), user_id, username, request.remote_addr)

        return None

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    return app


def log_access(path: str, user_id: int = None, username: str = None, role: str = 'guest', result: str = 'allowed'):
    """记录访问日志"""
    import sqlite3
    
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            user_id INTEGER,
            username TEXT,
            role TEXT,
            ip_address TEXT,
            user_agent TEXT,
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            method TEXT,
            result TEXT
            )
            ''')

            cursor.execute('''
            INSERT INTO access_logs (path, user_id, username, role, ip_address, user_agent, method, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (path, user_id, username, role, request.remote_addr, request.user_agent.string, request.method, result))

            conn.commit()
    except Exception as e:
        logger.error(f"Failed to log access: {e}")


def require_login(f):
    """装饰器:要求登录"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            log_access(request.path, None, None, 'guest', 'unauthorized')
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': '请先登录'
            }), 401
        
        # 验证会话有效性
        from app.utils.session_manager import get_session_manager
        sm = get_session_manager()
        session_data = sm.validate_session(session.get('session_id'))
        
        if not session_data:
            session.clear()
            return jsonify({
                'success': False,
                'error': 'SessionExpired',
                'message': '会话已过期,请重新登录'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    """装饰器:要求管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role')

        if not user_id:
            log_access(request.path, None, None, 'guest', 'unauthorized')
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': '请先登录'
            }), 401

        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            log_access(request.path, user_id, session.get('username'), role, 'forbidden')
            return jsonify({
                'success': False,
                'error': 'Forbidden',
                'message': '需要管理员权限'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def require_super_admin(f):
    """装饰器:要求超级管理员或硬件管理员权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role')

        if not user_id:
            log_access(request.path, None, None, 'guest', 'unauthorized')
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': '请先登录'
            }), 401

        if role not in ['super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            log_access(request.path, user_id, session.get('username'), role, 'forbidden')
            return jsonify({
                'success': False,
                'error': 'Forbidden',
                'message': '需要超级管理员权限'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def require_hardware_admin(f):
    """装饰器:要求硬件管理员权限(需硬件加密狗)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role')

        if not user_id:
            log_access(request.path, None, None, 'guest', 'unauthorized')
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': '请先登录'
            }), 401

        if role not in ['hardware_admin', 'hardware_vikey_admin']:
            log_access(request.path, user_id, session.get('username'), role, 'forbidden')
            return jsonify({
                'success': False,
                'error': 'Forbidden',
                'message': '需要硬件管理员权限'
            }), 403

        rm = get_rule_manager()
        hw_auth_required = rm.get_rule('HW_AUTH_REQUIRED')
        if hw_auth_required and str(hw_auth_required).lower() == 'true':
            if not has_hardware_session():
                return jsonify({
                    'success': False,
                    'error': 'HardwareRequired',
                    'message': '需要硬件加密狗才能使用此权限'
                }), 403

        return f(*args, **kwargs)
    return decorated_function


def require_role(allowed_roles):
    """装饰器:要求指定角色"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            role = session.get('role', 'guest')
            
            if not user_id:
                log_access(request.path, None, None, 'guest', 'unauthorized')
                return jsonify({
                    'success': False,
                    'error': 'Unauthorized',
                    'message': '请先登录'
                }), 401
            
            if role not in allowed_roles:
                log_access(request.path, user_id, session.get('username'), role, 'forbidden')
                return jsonify({
                    'success': False,
                    'error': 'Forbidden',
                    'message': '没有权限访问此资源'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user_info():
    """获取当前用户信息"""
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role', 'guest')
    }


def is_logged_in():
    """检查是否已登录"""
    user_id = session.get('user_id')
    if not user_id:
        return False
    
    # 验证会话
    from app.utils.session_manager import get_session_manager
    sm = get_session_manager()
    return sm.validate_session(session.get('session_id')) is not None


def is_admin():
    """检查是否是管理员"""
    role = session.get('role')
    return role in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']


def is_super_admin():
    """检查是否是超级管理员或硬件管理员"""
    role = session.get('role')
    return role in ['super_admin', 'hardware_admin', 'hardware_vikey_admin']


def is_hardware_admin():
    """检查是否是硬件管理员"""
    role = session.get('role')
    return role in ['hardware_admin', 'hardware_vikey_admin']


def has_hardware_key():
    """检查是否有硬件加密狗会话"""
    return has_hardware_session()


def validate_user_access(path: str) -> Dict:
    """验证用户访问权限(返回详细信息)"""
    user_id = session.get('user_id')
    role = session.get('role', 'guest')

    if not user_id:
        return {
            'allowed': False,
            'reason': 'not_logged_in',
            'message': '请先登录'
        }

    from app.utils.session_manager import get_session_manager
    sm = get_session_manager()
    session_data = sm.validate_session(session.get('session_id'))

    if not session_data:
        return {
            'allowed': False,
            'reason': 'session_expired',
            'message': '会话已过期'
        }

    if not validate_access(path, role):
        return {
            'allowed': False,
            'reason': 'insufficient_permissions',
            'message': '权限不足',
            'role': role,
            'path': path
        }

    return {
        'allowed': True,
        'user_id': user_id,
        'role': role,
        'message': '访问允许'
    }


def get_permission_hierarchy():
    """获取权限等级说明"""
    return {
        'levels': [
            {'level': 5, 'role': 'hardware_admin', 'name': '硬件管理员', 'description': '最高权限,需硬件加密狗'},
            {'level': 4, 'role': 'super_admin', 'name': '超级管理员', 'description': '系统最高管理权限'},
            {'level': 3, 'role': 'admin', 'name': '管理员', 'description': '系统管理权限'},
            {'level': 1, 'role': 'student', 'name': '学生', 'description': '学生用户权限'},
            {'level': 1, 'role': 'designer', 'name': '设计师', 'description': '设计人员权限'},
            {'level': 0, 'role': 'guest', 'name': '访客', 'description': '未登录用户'}
        ],
        'hierarchy': '硬件管理员 > 超级管理员 > 管理员 > 学生/设计师 > 访客'
    }
