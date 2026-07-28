#!/usr/bin/env python3
from functools import wraps
from flask import session, redirect, jsonify, request

def _is_super_admin_user():
    """判断当前用户是否为超级管理员（wuchenghao15）"""
    username = session.get('username', '')
    return username == 'wuchenghao15'

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if _is_super_admin_user():
            return f(*args, **kwargs)
        if not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': '未登录', 'code': 401}), 401
            return redirect('/')
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
        if role not in ['admin', 'super_admin', 'system_admin']:
            return jsonify({'success': False, 'error': '权限不足'}), 403
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
            return jsonify({'success': False, 'error': '权限不足'}), 403
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
                return jsonify({'success': False, 'error': '权限不足'}), 403
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
            
            try:
                from permission_optimizer_service import permission_service
                has_perm = permission_service.check_permission(user_id, permission_code)
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
            
            try:
                from permission_optimizer_service import permission_service
                has_perm = permission_service.check_button_permission(user_id, module_code, button_code)
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
            
            try:
                from permission_optimizer_service import permission_service
                has_perm = permission_service.check_api_permission(user_id, api_path, api_method)
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
        return f(*args, **kwargs)
    return decorated_function


def api_access_control_middleware():
    def middleware(app):
        @app.before_request
        def check_api_permissions():
            if request.path.startswith('/api/') and not request.path.startswith('/api/auth/'):
                if _is_super_admin_user():
                    return None
                
                if not session.get('logged_in'):
                    return jsonify({'success': False, 'error': '未登录', 'code': 401}), 401
                
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({'success': False, 'error': '用户信息缺失'}), 403
                
                try:
                    from permission_optimizer_service import permission_service
                    api_path = request.path
                    api_method = request.method
                    
                    has_perm = permission_service.check_api_permission(user_id, api_path, api_method)
                    if not has_perm:
                        return jsonify({'success': False, 'error': f'接口访问被拒绝: {api_method} {api_path}', 'code': 403}),
                        403
                except Exception as e:
                    pass
            
            return None
        
        return middleware
    
    return middleware