#!/usr/bin/env python3
"""
Unified Permission Decorators for MTSCOS AI System
统一权限装饰器集合 - 整合所有权限检查逻辑
提供一致的权限验证接口，便于各个视图模块使用
"""

from flask import request, session, redirect, jsonify, render_template
from functools import wraps
import logging

logger = logging.getLogger(__name__)

ROLE_HIERARCHY = {
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

STUDENT_ROLES = ['student', 'student_vip']
TEACHER_ROLES = ['teacher']
ADMIN_ROLES = ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']
K12_ROLES = ['student', 'student_vip', 'teacher']
ADULT_EDUCATION_ROLES = ['student', 'student_vip']

def get_role_level(role: str) -> int:
    """获取角色等级"""
    return ROLE_HIERARCHY.get(role, 0)

def _log_access(path, user_id, username, role, result, reason=''):
    """记录访问日志"""
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO access_logs (path, user_id, username, role, ip_address, user_agent, method, result, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (path, user_id, username, role, request.remote_addr, request.user_agent.string, request.method, result, reason))
            conn.commit()
    except Exception as e:
        logger.error(f"记录访问日志失败: {e}")

def require_login(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            logger.warning(f"[权限] 未登录用户尝试访问: {request.path}")
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Unauthorized',
                    'code': 'NOT_LOGGED_IN',
                    'message': '请先登录'
                }), 401
            
            return redirect('/login?next=' + request.path)
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(*allowed_roles):
    """装饰器:要求指定角色"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            role = session.get('role', 'guest')

            if not user_id:
                _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
                return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

            if role not in allowed_roles:
                logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 权限不足，需要角色: {allowed_roles}")
                _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'ROLE_NOT_ALLOWED')
                return jsonify({'success': False, 'error': 'Forbidden', 'message': f'需要以下角色之一: {allowed_roles}'}), 403

            _log_access(request.path, user_id, session.get('username'), role, 'allowed')
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
                _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
                return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

            current_level = get_role_level(role)
            if current_level < min_level:
                logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 权限等级不足，需要等级: {min_level}")
                _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'LEVEL_NOT_SUFFICIENT')
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '权限等级不足'}), 403

            _log_access(request.path, user_id, session.get('username'), role, 'allowed')
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
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in STUDENT_ROLES:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非学生角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'STUDENT_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限学生访问'}), 403
            
            return render_template('403.html', message='仅限学生访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_student_or_vip(f):
    """装饰器:要求学生或VIP学生角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in STUDENT_ROLES:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非学生角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'STUDENT_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限学生访问'}), 403
            
            return render_template('403.html', message='仅限学生访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_teacher(f):
    """装饰器:要求教师角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in TEACHER_ROLES:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非教师角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'TEACHER_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限教师访问'}), 403
            
            return render_template('403.html', message='仅限教师访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_teacher_or_admin(f):
    """装饰器:要求教师或管理员角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        allowed_roles = TEACHER_ROLES + ADMIN_ROLES
        if role not in allowed_roles:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非教师或管理员角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'TEACHER_OR_ADMIN_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限教师或管理员访问'}), 403
            
            return render_template('403.html', message='仅限教师或管理员访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """装饰器:要求管理员角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in ADMIN_ROLES:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非管理员角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'ADMIN_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限管理员访问'}), 403
            
            return render_template('403.html', message='仅限管理员访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_super_admin(f):
    """装饰器:要求超级管理员角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in ['super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非超级管理员角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'SUPER_ADMIN_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限超级管理员访问'}), 403
            
            return render_template('403.html', message='仅限超级管理员访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_hardware_admin(f):
    """装饰器:要求硬件管理员角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in ['hardware_admin', 'hardware_vikey_admin']:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非硬件管理员角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'HARDWARE_ADMIN_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限硬件管理员访问'}), 403
            
            return render_template('403.html', message='仅限硬件管理员访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_k12_role(f):
    """装饰器:要求K12角色(学生/教师)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if role not in K12_ROLES:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非K12角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'K12_ROLE_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': 'K12功能仅对学生和教师开放'}), 403
            
            return render_template('k12/403.html', message='K12功能仅对学生和教师开放'), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_grade(f):
    """装饰器:要求设置年级"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        grade = session.get('grade', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        if not grade:
            logger.warning(f"[权限] 用户 {session.get('username')} 未设置年级")
            _log_access(request.path, user_id, session.get('username'), session.get('role', ''), 'forbidden', 'GRADE_NOT_SET')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'GRADE_NOT_SET', 'message': '请先设置年级'}), 403
            
            return redirect('/k12/set_grade?next=' + request.full_path)

        _log_access(request.path, user_id, session.get('username'), session.get('role', ''), 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_adult_education(f):
    """装饰器:要求成人教育学生"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return redirect('/login?next=' + request.path)

        if role not in ADULT_EDUCATION_ROLES:
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'ADULT_STUDENT_ONLY')
            return jsonify({'success': False, 'error': 'ROLE_NOT_ALLOWED', 'message': '仅限学生访问'}), 403

        education = _get_user_education_system(user_id)
        if education != 'adult':
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'EDUCATION_NOT_ALLOWED')
            return jsonify({'success': False, 'error': 'EDUCATION_NOT_ALLOWED', 'message': '仅限成人制教育学生访问'}), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def require_k12_education(f):
    """装饰器:要求K12教育学生"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return redirect('/login?next=' + request.path)

        if role not in K12_ROLES:
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'K12_EDUCATION_ONLY')
            return jsonify({'success': False, 'error': 'ROLE_NOT_ALLOWED', 'message': '仅限学生和教师访问'}), 403

        education = _get_user_education_system(user_id)
        if education != 'k12':
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'EDUCATION_NOT_ALLOWED')
            return jsonify({'success': False, 'error': 'EDUCATION_NOT_ALLOWED', 'message': '仅限K12教育学生访问'}), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def _get_user_education_system(user_id=None):
    """获取用户教育体系"""
    if not user_id:
        user_id = session.get('user_id')
    
    if not user_id:
        return None
    
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT education_system FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
    except Exception as e:
        logger.error(f"获取用户教育体系失败: {e}")
    
    return None

def require_designer(f):
    """装饰器:要求设计师角色"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')

        if not user_id:
            _log_access(request.path, None, None, 'guest', 'unauthorized', 'NOT_LOGGED_IN')
            return jsonify({'success': False, 'error': 'Unauthorized', 'message': '请先登录'}), 401

        allowed_roles = ['designer', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']
        if role not in allowed_roles:
            logger.warning(f"[权限] 用户 {session.get('username')} ({role}) 非设计师角色")
            _log_access(request.path, user_id, session.get('username'), role, 'forbidden', 'DESIGNER_ONLY')
            
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Forbidden', 'message': '仅限设计师访问'}), 403
            
            return render_template('403.html', message='仅限设计师访问', role=role), 403

        _log_access(request.path, user_id, session.get('username'), role, 'allowed')
        return f(*args, **kwargs)
    return decorated_function

def check_permission(role: str, required_role: str) -> bool:
    """检查角色是否满足权限要求"""
    return get_role_level(role) >= get_role_level(required_role)

def has_permission(path: str, role: str) -> bool:
    """检查角色是否有权访问指定路径"""
    from app.middlewares.unified_permission import check_role_access
    return check_role_access(path, role)

def get_permission_info() -> dict:
    """获取当前用户权限信息"""
    user_id = session.get('user_id')
    role = session.get('role', 'guest')
    
    return {
        'user_id': user_id,
        'username': session.get('username'),
        'role': role,
        'role_level': get_role_level(role),
        'is_logged_in': bool(user_id),
        'is_student': role in STUDENT_ROLES,
        'is_teacher': role in TEACHER_ROLES,
        'is_admin': role in ADMIN_ROLES,
        'is_super_admin': role in ['super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'is_hardware_admin': role in ['hardware_admin', 'hardware_vikey_admin'],
        'is_designer': role == 'designer',
        'education_system': _get_user_education_system(user_id),
        'grade': session.get('grade'),
    }


def init_permission_decorators(app):
    """初始化权限装饰器中间件"""
    logger.info("权限装饰器中间件已注册")
    return app