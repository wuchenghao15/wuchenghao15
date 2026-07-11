#!/usr/bin/env python3
"""
Unified Permission Middleware for MTSCOS AI System
统一权限控制中间件 - 实现deny-by-default模式
所有未明确授权的路由默认拒绝访问
"""

from flask import request, session, redirect, url_for, jsonify, render_template
from functools import wraps
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

ROLE_HIERARCHY = ['guest', 'student', 'student_vip', 'designer', 'teacher', 'admin', 'super_admin', 'hardware_admin']

GLOBAL_PUBLIC_ROUTES = [
    '/',
    '/login',
    '/register',
    '/forgot_password',
    '/reset_password',
    '/api/health',
    '/api/system/status',
    '/api/server-time',
    '/api/k12/status',
    '/api/exam/enhancement/',  # 考试增强系统API（智能组卷、防作弊、数据分析）
    '/api/learning/enhancement/',  # 学习增强系统API（学习路径、错题推荐、知识图谱）
    '/api/k12/parent/',  # K12家长端API
    '/api/k12/teacher/',  # K12教师端API
    '/api/admin/monitoring/',  # 运维监控API
    '/api/alert/',  # 告警系统API
    '/api/brain_bank/',  # AI脑库API
    '/api/proactive_ai/',  # 主动AI系统API
    '/api/data_integrity/',  # 数据完整性API
    '/api/ai_employee/',  # AI员工API
    '/api/local-agents/',  # 本地Agent管理API
    '/api/routes/list',  # 路由列表API
    '/api/routes/reload',  # 路由刷新API
    '/api/routes/check',  # 路由检查API
    '/api/role/info',  # 角色信息API
    '/api/role/list',  # 角色列表API
    '/api/role/check_access',  # 权限检查API
    '/favicon.ico',
    '/robots.txt',
    '/auth/login',
    '/auth/register',
    '/auth/logout',
]

GLOBAL_STATIC_PATHS = [
    '/static/',
    '/assets/',
    '/webfonts/',
    '/audio/',
    '/about/',
    '/products/',
    '/contact/',
    '/mobile/',
]

ROLE_PAGE_MAPPING = {
    'student': ['/exam_system', '/dashboard', '/profile', '/ai-chat', '/learning_system', '/math_training', '/k12'],
    'student_vip': ['/exam_system', '/dashboard', '/profile', '/ai-chat', '/learning_system', '/math_training', '/k12'],
    'teacher': ['/teacher', '/dashboard', '/profile', '/ai-chat', '/k12'],
    'designer': ['/arduino', '/dashboard', '/profile', '/ai-chat'],
    'admin': ['/settings', '/admin_center', '/dashboard', '/profile', '/ai-chat'],
    'super_admin': ['/super_admin_dashboard', '/admin_center', '/settings', '/dashboard', '/profile', '/ai-chat'],
    'hardware_admin': ['/super_admin_dashboard', '/hardware/dashboard', '/admin_center', '/settings', '/dashboard', '/profile', '/ai-chat'],
    'hardware_vikey_admin': ['/super_admin_dashboard', '/hardware/dashboard', '/admin_center', '/settings', '/dashboard', '/profile', '/ai-chat'],
}

ADMIN_ONLY_ROUTES = [
    '/admin_center',
    '/settings',
    '/api/admin/',
    '/admin_app/',
]

SUPER_ADMIN_ONLY_ROUTES = [
    '/super_admin_dashboard',
    '/api/admin/database',
    '/api/admin/permissions',
]

HARDWARE_ADMIN_ONLY_ROUTES = [
    '/hardware/dashboard',
    '/api/hardware/',
]

STUDENT_ONLY_ROUTES = [
    '/exam_system',
    '/learning_system',
    '/math_training',
]

K12_ROUTES = [
    '/k12',
    '/k12/subject/',
    '/k12/exam',
    '/k12/report',
    '/k12/practice',
]

SPECIAL_ACCESS_RULES = {
    '/ai-chat': ['student', 'student_vip', 'designer', 'teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    '/physics-engine/': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin', 'teacher', 'designer'],
    '/exam_center': ['student', 'student_vip'],
    '/exam_page/': ['student', 'student_vip'],
    '/exam_results': ['student', 'student_vip'],
    '/exam_history': ['student', 'student_vip'],
    '/learning/': ['student', 'student_vip', 'teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    '/teacher': ['teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    '/arduino': ['designer', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
    '/admin_app': ['admin', 'super_admin', 'hardware_admin'],
    '/hardware/dashboard': ['hardware_admin', 'hardware_vikey_admin'],
}

def get_role_level(role: str) -> int:
    """获取角色等级"""
    levels = {
        'guest': 0,
        'student': 1,
        'student_vip': 1,
        'designer': 1,
        'teacher': 2,
        'admin': 3,
        'super_admin': 4,
        'hardware_admin': 5,
        'hardware_vikey_admin': 5,
    }
    return levels.get(role, 0)

def is_static_request(path: str) -> bool:
    """检查是否为静态资源请求"""
    for static_path in GLOBAL_STATIC_PATHS:
        if path.startswith(static_path):
            return True
    return False

def is_public_route(path: str) -> bool:
    """检查是否为公开路由"""
    if path in GLOBAL_PUBLIC_ROUTES:
        return True
    for public_route in GLOBAL_PUBLIC_ROUTES:
        if path.startswith(public_route):
            return True
    return False

def check_role_access(path: str, role: str) -> bool:
    """检查角色是否有权访问路径"""
    if role == 'guest':
        return is_public_route(path)

    if role == 'hardware_admin' or role == 'hardware_vikey_admin':
        return True

    if role == 'super_admin':
        for restricted in HARDWARE_ADMIN_ONLY_ROUTES:
            if path.startswith(restricted):
                return False
        return True

    for admin_route in ADMIN_ONLY_ROUTES:
        if path.startswith(admin_route):
            return role in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']

    for super_route in SUPER_ADMIN_ONLY_ROUTES:
        if path.startswith(super_route):
            return role in ['super_admin', 'hardware_admin', 'hardware_vikey_admin']

    for student_route in STUDENT_ONLY_ROUTES:
        if path.startswith(student_route):
            return role in ['student', 'student_vip']

    for k12_route in K12_ROUTES:
        if path.startswith(k12_route):
            return role in ['student', 'student_vip', 'teacher']

    for special_path, allowed_roles in SPECIAL_ACCESS_RULES.items():
        if path.startswith(special_path):
            return role in allowed_roles

    if role in ROLE_PAGE_MAPPING:
        for allowed_path in ROLE_PAGE_MAPPING[role]:
            if path.startswith(allowed_path):
                return True

    return True

def unified_permission_middleware(app):
    """统一权限控制中间件 - deny-by-default模式"""

    @app.before_request
    def check_unified_permission():
        path = request.path
        method = request.method

        if method == 'OPTIONS':
            return None

        if is_static_request(path):
            return None

        if is_public_route(path):
            return None

        user_id = session.get('user_id')
        role = session.get('role', 'guest')

        if not user_id:
            return handle_unauthorized(path, '未登录用户')

        if not role:
            role = 'guest'
            return handle_unauthorized(path, '角色未设置')

        if not check_role_access(path, role):
            return handle_forbidden(path, user_id, session.get('username'), role)

        return None

    def handle_unauthorized(path: str, reason: str):
        """处理未授权访问"""
        logger.warning(f"[权限拦截] 未授权访问 - 路径: {path}, 原因: {reason}, IP: {request.remote_addr}")
        log_access(path, None, None, 'guest', 'unauthorized')

        if request.is_json or path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'code': 'NOT_LOGGED_IN',
                'message': '请先登录'
            }), 401

        return redirect('/login?next=' + request.path)

    def handle_forbidden(path: str, user_id, username, role):
        """处理权限不足"""
        logger.warning(f"[权限拦截] 权限不足 - 路径: {path}, 用户: {username}, 角色: {role}")
        log_access(path, user_id, username, role, 'forbidden')

        if request.is_json or path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Forbidden',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'message': '您没有权限访问此资源',
                'role': role,
                'path': path
            }), 403

        return render_template('403.html', 
                              message=f'您的角色({role})没有权限访问此页面',
                              path=path,
                              role=role), 403

    def log_access(path: str, user_id, username, role, result):
        """记录访问日志"""
        try:
            import sqlite3
            db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO access_logs (path, user_id, username, role, ip_address, user_agent, method, result, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (path, user_id, username, role, request.remote_addr, request.user_agent.string, request.method, result, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"记录访问日志失败: {e}")

    return app

def require_role(*allowed_roles):
    """装饰器:要求指定角色"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            role = session.get('role', 'guest')

            if not user_id:
                return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

            if role not in allowed_roles:
                log_decorator_access(request.path, user_id, session.get('username'), role, 'forbidden')
                return jsonify({'success': False, 'error': 'Forbidden', 'message': f'需要以下角色之一: {allowed_roles}'}), 403

            log_decorator_access(request.path, user_id, session.get('username'), role, 'allowed')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_min_role_level(min_level):
    """装饰器:要求最小角色等级"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            role = session.get('role', 'guest')

            if not user_id:
                return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

            current_level = get_role_level(role)
            if current_level < min_level:
                log_decorator_access(request.path, user_id, session.get('username'), role, 'forbidden')
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '权限等级不足'}), 403

            log_decorator_access(request.path, user_id, session.get('username'), role, 'allowed')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_student(f):
    """装饰器:要求学生角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in ['student', 'student_vip']:
            log_decorator_access(request.path, user_id, session.get('username'), role, 'forbidden')
            return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限学生访问'}), 403

        log_decorator_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_teacher(f):
    """装饰器:要求教师角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role != 'teacher':
            log_decorator_access(request.path, user_id, session.get('username'), role, 'forbidden')
            return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限教师访问'}), 403

        log_decorator_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_admin_or_higher(f):
    """装饰器:要求管理员及以上权限"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if get_role_level(role) < 3:
            log_decorator_access(request.path, user_id, session.get('username'), role, 'forbidden')
            return jsonify({'success': False, 'error': 'Forbidden', 'message': '需要管理员权限'}), 403

        log_decorator_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def log_decorator_access(path, user_id, username, role, result):
    """记录装饰器访问日志"""
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO access_logs (path, user_id, username, role, ip_address, user_agent, method, result, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (path, user_id, username, role, request.remote_addr, request.user_agent.string, request.method, result, datetime.now().isoformat()))
            conn.commit()
    except Exception:
        pass

def get_redirect_url_for_role(role: str) -> str:
    """获取角色对应的默认重定向URL"""
    try:
        from app.utils.role_router import get_smart_redirect_url
        return get_smart_redirect_url(role)
    except ImportError:
        role_redirect = {
            'student': '/exam_system',
            'student_vip': '/exam_system',
            'teacher': '/teacher',
            'designer': '/arduino',
            'admin': '/admin_app/settings',
            'super_admin': '/admin_app/settings',
            'hardware_admin': '/hardware/dashboard',
            'hardware_vikey_admin': '/hardware/dashboard',
        }
        return role_redirect.get(role, '/')

def validate_session() -> bool:
    """验证会话有效性"""
    user_id = session.get('user_id')
    session_id = session.get('session_id')

    if not user_id or not session_id:
        return False

    try:
        from app.utils.session_manager import get_session_manager
        sm = get_session_manager()
        return sm.validate_session(session_id) is not None
    except Exception:
        return False

def get_current_user_info() -> dict:
    """获取当前用户信息"""
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role', 'guest'),
        'grade': session.get('grade'),
        'is_logged_in': validate_session(),
        'role_level': get_role_level(session.get('role', 'guest')),
    }

def get_permission_rules() -> dict:
    """获取所有权限规则"""
    return {
        'role_hierarchy': ROLE_HIERARCHY,
        'role_page_mapping': ROLE_PAGE_MAPPING,
        'admin_only_routes': ADMIN_ONLY_ROUTES,
        'super_admin_only_routes': SUPER_ADMIN_ONLY_ROUTES,
        'hardware_admin_only_routes': HARDWARE_ADMIN_ONLY_ROUTES,
        'student_only_routes': STUDENT_ONLY_ROUTES,
        'k12_routes': K12_ROUTES,
        'special_access_rules': SPECIAL_ACCESS_RULES,
        'public_routes': GLOBAL_PUBLIC_ROUTES,
        'static_paths': GLOBAL_STATIC_PATHS,
    }