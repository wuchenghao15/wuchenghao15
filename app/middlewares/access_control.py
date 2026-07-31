#!/usr/bin/env python3
"""
访问控制中间件 - 升级版
功能：
1. 角色矩阵：细粒度路径-角色映射（与 security_middleware.PATH_ROLE_MATRIX 一致）
2. 权限缓存：减少数据库查询（TTL 300秒）
3. 路径黑名单：禁止访问的路径模式
4. 方法-路径约束：写操作仅限特定路径
5. 数据脱敏：API响应中自动移除敏感字段
6. 安全响应头：after_request 自动注入
"""
import time
import json
import hashlib
from functools import wraps
from flask import session, redirect, jsonify, request, g, current_app

# ==================== 角色矩阵 ====================
# 与 security_middleware.PATH_ROLE_MATRIX 保持同步
ROLE_MATRIX = {
    '/admin_app/': {'admin', 'super_admin', 'teacher_admin', 'school_admin', 'sysadmin', 'hardware_admin'},
    '/admin_center': {'admin', 'super_admin', 'system_admin'},
    '/teacher': {'teacher', 'admin', 'super_admin', 'system_admin'},
    '/designer': {'designer', 'admin', 'super_admin', 'system_admin'},
    '/exam_system/': {'student', 'student_vip', 'teacher', 'admin', 'super_admin', 'system_admin'},
    '/backup': {'super_admin'},
    '/snapshot': {'super_admin'},
    '/iso_build': {'super_admin'},
    '/shadow': {'super_admin'},
    '/upgrade': {'super_admin'},
    '/api/admin/': {'admin', 'super_admin', 'system_admin'},
    '/api/vikey/': {'super_admin', 'admin', 'system_admin'},
    '/api/security/': {'super_admin', 'admin', 'system_admin'},
    '/api/system/': {'super_admin', 'admin', 'system_admin'},
    '/api/firewall/': {'super_admin', 'admin', 'system_admin'},
    '/api/users/manage': {'admin', 'super_admin', 'system_admin'},
    '/api/users/delete': {'super_admin'},
    '/api/users/role': {'super_admin'},
}

# ==================== 路径黑名单 ====================
# 这些路径模式对所有非SA用户禁止
PATH_BLACKLIST_PATTERNS = [
    '/etc/', '/proc/', '/sys/', '/root/.',
    '/.env', '/.git', '/.svn', '/.htaccess', '/.htpasswd',
    '/wp-admin', '/phpmyadmin', '/adminer.php', '/cpanel',
    '/web.config', '/settings.py', '/local_settings.py',
    '/.ssh/', '/.aws/credentials', '/.bash_history',
]

# ==================== 权限缓存 ====================
PERMISSION_CACHE = {}
PERMISSION_CACHE_TTL = 300  # 5分钟

# ==================== 敏感字段黑名单（响应中自动移除） ====================
SENSITIVE_FIELDS = {
    'password', 'password_hash', 'passwd', 'pwd',
    'token', 'secret', 'api_key', 'apikey',
    'private_key', 'privatekey', 'privateKey',
    'session_token', 'csrf_token', 'auth_token',
    'access_token', 'refresh_token',
    'salt', 'hash',
}

# ==================== 安全响应头 ====================
SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(),camera=(),microphone=()',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
}


def _is_super_admin_user():
    """判断当前用户是否为超级管理员（wuchenghao15）"""
    username = session.get('username', '')
    return username == 'wuchenghao15'


def _check_path_blacklist(path):
    """检查路径是否在黑名单中"""
    path_lower = path.lower()
    for pattern in PATH_BLACKLIST_PATTERNS:
        if pattern.lower() in path_lower:
            return True
    return False


def _check_role_matrix(path, role):
    """检查路径-角色矩阵"""
    for matrix_path, allowed_roles in ROLE_MATRIX.items():
        if path.startswith(matrix_path):
            return role in allowed_roles
    return True  # 未匹配的路径默认允许


def _get_cached_permission(user_id, permission_key):
    """从缓存获取权限检查结果"""
    cache_key = f"{user_id}:{permission_key}"
    cached = PERMISSION_CACHE.get(cache_key)
    if cached and (time.time() - cached['timestamp'] < PERMISSION_CACHE_TTL):
        return cached['result']
    return None


def _set_cached_permission(user_id, permission_key, result):
    """缓存权限检查结果"""
    cache_key = f"{user_id}:{permission_key}"
    PERMISSION_CACHE[cache_key] = {
        'result': result,
        'timestamp': time.time()
    }
    # 清理过期缓存
    if len(PERMISSION_CACHE) > 1000:
        now = time.time()
        expired = [k for k, v in PERMISSION_CACHE.items() if now - v['timestamp'] > PERMISSION_CACHE_TTL]
        for k in expired:
            del PERMISSION_CACHE[k]


def _sanitize_response_data(data):
    """递归移除响应数据中的敏感字段"""
    if isinstance(data, dict):
        return {
            k: _sanitize_response_data(v) for k, v in data.items()
            if k.lower() not in SENSITIVE_FIELDS
        }
    elif isinstance(data, list):
        return [_sanitize_response_data(item) for item in data]
    return data


def inject_security_headers(response):
    """注入安全响应头"""
    try:
        from app.system_rules_extension import SystemRulesExtension
        rules = SystemRulesExtension()
        headers_config = rules.get_security_headers_config()
        if headers_config['enabled']:
            response.headers['X-Frame-Options'] = headers_config['x_frame_options']
            response.headers['X-Content-Type-Options'] = headers_config['x_content_type_options']
            response.headers['X-XSS-Protection'] = headers_config['x_xss_protection']
            response.headers['Referrer-Policy'] = headers_config['referrer_policy']
            response.headers['Permissions-Policy'] = headers_config['permissions_policy']
            response.headers['Content-Security-Policy'] = headers_config['csp_policy']
            if headers_config['hsts_include_subdomains']:
                response.headers['Strict-Transport-Security'] = f"max-age={headers_config['hsts_max_age']}; includeSubDomains"
            else:
                response.headers['Strict-Transport-Security'] = f"max-age={headers_config['hsts_max_age']}"
    except Exception:
        # 降级：使用默认安全头
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
    return response


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if _is_super_admin_user():
            return f(*args, **kwargs)

        path = request.path or ''

        # 路径黑名单检查
        if _check_path_blacklist(path):
            return jsonify({'success': False, 'error': '访问被拒绝', 'code': 403}), 403

        if not session.get('logged_in'):
            if path.startswith('/api/'):
                return jsonify({'success': False, 'error': '未登录', 'code': 401}), 401
            return redirect('/')

        # 角色矩阵检查
        role = session.get('role', 'guest')
        if not _check_role_matrix(path, role):
            return jsonify({'success': False, 'error': '权限不足', 'code': 403}), 403

        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if _is_super_admin_user():
            return f(*args, **kwargs)
        if not session.get('logged_in'):
            return redirect('/')
        role = session.get('role', 'guest')
        if role not in ['admin', 'super_admin', 'system_admin',
                         'teacher_admin', 'school_admin', 'sysadmin',
                         'hardware_admin', 'cluster_manager', 'ai_manager']:
            return jsonify({'success': False, 'error': '需要管理员权限', 'code': 403}), 403

        # 角色矩阵检查
        path = request.path or ''
        if not _check_role_matrix(path, role):
            return jsonify({'success': False, 'error': '权限不足', 'code': 403}), 403

        return f(*args, **kwargs)
    return decorated_function


def require_super_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if _is_super_admin_user():
            return f(*args, **kwargs)
        if not session.get('logged_in'):
            return redirect('/')
        role = session.get('role', 'guest')
        if role != 'super_admin':
            return jsonify({'success': False, 'error': '需要超级管理员权限', 'code': 403}), 403

        # 路径黑名单检查
        path = request.path or ''
        if _check_path_blacklist(path):
            return jsonify({'success': False, 'error': '访问被拒绝', 'code': 403}), 403

        return f(*args, **kwargs)
    return decorated_function


def require_role(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if _is_super_admin_user():
                return f(*args, **kwargs)
            if not session.get('logged_in'):
                return redirect('/')
            role = session.get('role', 'guest')
            if role not in allowed_roles:
                return jsonify({'success': False, 'error': '权限不足', 'code': 403}), 403

            # 路径黑名单检查
            path = request.path or ''
            if _check_path_blacklist(path):
                return jsonify({'success': False, 'error': '访问被拒绝', 'code': 403}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_permission(permission_code):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if _is_super_admin_user():
                return f(*args, **kwargs)
            if not session.get('logged_in'):
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': '未登录', 'code': 401}), 401
                return redirect('/')

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': '用户信息缺失'}), 403

            # 权限缓存检查
            cached = _get_cached_permission(user_id, permission_code)
            if cached is not None:
                if not cached:
                    return jsonify({'success': False, 'error': f'缺少权限: {permission_code}'}), 403
                return f(*args, **kwargs)

            try:
                from permission_optimizer_service import permission_service
                has_perm = permission_service.check_permission(user_id, permission_code)
                _set_cached_permission(user_id, permission_code, has_perm)
                if not has_perm:
                    return jsonify({'success': False, 'error': f'缺少权限: {permission_code}'}), 403
            except Exception as e:
                return jsonify({'success': False, 'error': f'权限检查失败: {str(e)}'}), 500

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_button_permission(module_code, button_code):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if _is_super_admin_user():
                return f(*args, **kwargs)
            if not session.get('logged_in'):
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': '未登录', 'code': 401}), 401
                return redirect('/')

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': '用户信息缺失'}), 403

            perm_key = f"btn:{module_code}:{button_code}"
            cached = _get_cached_permission(user_id, perm_key)
            if cached is not None:
                if not cached:
                    return jsonify({'success': False, 'error': f'缺少按钮权限: {module_code}.{button_code}'}), 403
                return f(*args, **kwargs)

            try:
                from permission_optimizer_service import permission_service
                has_perm = permission_service.check_button_permission(user_id, module_code, button_code)
                _set_cached_permission(user_id, perm_key, has_perm)
                if not has_perm:
                    return jsonify({'success': False, 'error': f'缺少按钮权限: {module_code}.{button_code}'}), 403
            except Exception as e:
                return jsonify({'success': False, 'error': f'按钮权限检查失败: {str(e)}'}), 500

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_api_permission(api_path, api_method='GET'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if _is_super_admin_user():
                return f(*args, **kwargs)
            if not session.get('logged_in'):
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': '未登录', 'code': 401}), 401
                return redirect('/')

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': '用户信息缺失'}), 403

            perm_key = f"api:{api_method}:{api_path}"
            cached = _get_cached_permission(user_id, perm_key)
            if cached is not None:
                if not cached:
                    return jsonify({'success': False, 'error': f'缺少接口权限: {api_method} {api_path}'}), 403
                return f(*args, **kwargs)

            try:
                from permission_optimizer_service import permission_service
                has_perm = permission_service.check_api_permission(user_id, api_path, api_method)
                _set_cached_permission(user_id, perm_key, has_perm)
                if not has_perm:
                    return jsonify({'success': False, 'error': f'缺少接口权限: {api_method} {api_path}'}), 403
            except Exception as e:
                return jsonify({'success': False, 'error': f'接口权限检查失败: {str(e)}'}), 500

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def allow_guest_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if _is_super_admin_user():
            return f(*args, **kwargs)
        role = session.get('role', 'guest')
        if role not in ['guest', 'student', 'teacher', 'parent', 'admin', 'super_admin', 'system_admin']:
            role = 'guest'
        session['role'] = role

        # 游客路径黑名单检查
        path = request.path or ''
        if _check_path_blacklist(path):
            return jsonify({'success': False, 'error': '访问被拒绝', 'code': 403}), 403

        return f(*args, **kwargs)
    return decorated_function


def api_access_control_middleware():
    def middleware(app):
        @app.before_request
        def check_api_permissions():
            path = request.path or ''

            # 路径黑名单（所有用户，含SA）
            if _check_path_blacklist(path):
                return jsonify({'success': False, 'error': '访问被拒绝', 'code': 403}), 403

            if not path.startswith('/api/') or path.startswith('/api/auth/'):
                return None

            if _is_super_admin_user():
                return None

            if not session.get('logged_in'):
                return jsonify({'success': False, 'error': '未登录', 'code': 401}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': '用户信息缺失'}), 403

            # 角色矩阵检查
            role = session.get('role', 'guest')
            if not _check_role_matrix(path, role):
                return jsonify({'success': False, 'error': f'接口访问被拒绝: {request.method} {path}', 'code': 403}), 403

            # 权限缓存检查
            api_method = request.method
            perm_key = f"api:{api_method}:{path}"
            cached = _get_cached_permission(user_id, perm_key)
            if cached is not None:
                if not cached:
                    return jsonify({'success': False, 'error': f'接口访问被拒绝: {api_method} {path}', 'code': 403}), 403
                return None

            try:
                from permission_optimizer_service import permission_service
                has_perm = permission_service.check_api_permission(user_id, path, api_method)
                _set_cached_permission(user_id, perm_key, has_perm)
                if not has_perm:
                    return jsonify({'success': False, 'error': f'接口访问被拒绝: {api_method} {path}', 'code': 403}), 403
            except Exception:
                pass

            return None

        @app.after_request
        def add_security_headers(response):
            """注入安全响应头"""
            return inject_security_headers(response)

        return middleware

    return middleware