#!/usr/bin/env python3
"""
Role Router Manager for MTSCOS AI System
角色路由管理器 - 统一管理角色与页面的匹配关系
确保登录后根据角色正确跳转
"""

from flask import Blueprint, session, redirect, url_for, jsonify, request
from app.middlewares.system_constraints import get_user_education_system, get_user_education_info
import logging

logger = logging.getLogger(__name__)

role_router_bp = Blueprint('role_router', __name__)

ROLE_PAGE_MAPPING = {
    'student': {
        'default': '/exam_system',
        'pages': ['/exam_system', '/dashboard', '/profile', '/ai-chat', '/learning_system', '/math_training', '/k12'],
        'description': '学生用户',
        'icon': 'graduation-cap'
    },
    'student_vip': {
        'default': '/exam_system',
        'pages': ['/exam_system', '/dashboard', '/profile', '/ai-chat', '/learning_system', '/math_training', '/k12'],
        'description': 'VIP学生用户',
        'icon': 'crown'
    },
    'teacher': {
        'default': '/teacher',
        'pages': ['/teacher', '/dashboard', '/profile', '/ai-chat', '/k12'],
        'description': '教师用户',
        'icon': 'chalkboard-teacher'
    },
    'designer': {
        'default': '/arduino',
        'pages': ['/arduino', '/dashboard', '/profile', '/ai-chat'],
        'description': '设计师用户',
        'icon': 'palette'
    },
    'admin': {
        'default': '/admin_app/settings',
        'pages': ['/admin_app/settings', '/admin_center', '/dashboard', '/profile', '/ai-chat'],
        'description': '管理员用户',
        'icon': 'shield'
    },
    'super_admin': {
        'default': '/admin_app/settings',
        'pages': ['/admin_app/settings', '/admin_center', '/dashboard', '/profile', '/ai-chat'],
        'description': '超级管理员',
        'icon': 'shield-alt'
    },
    'hardware_admin': {
        'default': '/hardware/dashboard',
        'pages': ['/hardware/dashboard', '/super_admin_dashboard', '/admin_center', '/settings', '/dashboard', '/profile', '/ai-chat'],
        'description': '硬件管理员',
        'icon': 'key'
    },
    'hardware_vikey_admin': {
        'default': '/hardware/dashboard',
        'pages': ['/hardware/dashboard', '/super_admin_dashboard', '/admin_center', '/settings', '/dashboard', '/profile', '/ai-chat'],
        'description': '硬件维凯管理员',
        'icon': 'key'
    },
    'user': {
        'default': '/',
        'pages': ['/', '/dashboard', '/profile', '/ai-chat'],
        'description': '普通用户',
        'icon': 'user'
    },
    'guest': {
        'default': '/',
        'pages': ['/', '/login', '/register'],
        'description': '访客',
        'icon': 'user-circle'
    },
}

SPECIAL_ROUTE_RULES = {
    '/exam_system': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'adult_only': True,
        'redirect_if_denied': '/'
    },
    '/learning_system': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'adult_only': True,
        'redirect_if_denied': '/'
    },
    '/math_training': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'adult_only': True,
        'redirect_if_denied': '/'
    },
    '/exam_center': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'redirect_if_denied': '/'
    },
    '/exam_page/': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'redirect_if_denied': '/'
    },
    '/exam_results': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'redirect_if_denied': '/'
    },
    '/exam_history': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'redirect_if_denied': '/'
    },
    '/learning/': {
        'allowed_roles': ['student', 'student_vip', 'teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/settings': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/super_admin_dashboard': {
        'allowed_roles': ['super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/hardware/dashboard': {
        'allowed_roles': ['hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/admin_center': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/admin_app': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/ai-chat': {
        'allowed_roles': ['student', 'student_vip', 'designer', 'teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/physics-engine/': {
        'allowed_roles': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin', 'teacher', 'designer'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/arduino': {
        'allowed_roles': ['designer', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/teacher': {
        'allowed_roles': ['teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'student_only': False,
        'redirect_if_denied': '/'
    },
    '/k12': {
        'allowed_roles': ['student', 'student_vip', 'teacher'],
        'student_only': False,
        'k12_only': True,
        'redirect_if_denied': '/'
    },
    '/k12/subject/': {
        'allowed_roles': ['student', 'student_vip', 'teacher'],
        'student_only': False,
        'k12_only': True,
        'require_grade': True,
        'redirect_if_denied': '/'
    },
    '/k12/exam': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'k12_only': True,
        'require_grade': True,
        'redirect_if_denied': '/'
    },
    '/k12/report': {
        'allowed_roles': ['student', 'student_vip'],
        'student_only': True,
        'k12_only': True,
        'require_grade': True,
        'redirect_if_denied': '/'
    },
    '/k12/practice': {
        'allowed_roles': ['student', 'student_vip', 'teacher'],
        'student_only': False,
        'k12_only': True,
        'redirect_if_denied': '/'
    },
}

def get_role_info(role: str) -> dict:
    """获取角色详细信息"""
    return ROLE_PAGE_MAPPING.get(role, {
        'default': '/',
        'pages': ['/', '/login', '/register'],
        'description': '未知角色',
        'icon': 'question-circle'
    })

def get_default_redirect(role: str) -> str:
    """获取角色默认重定向URL"""
    return get_role_info(role)['default']

def is_page_allowed(path: str, role: str) -> bool:
    """检查角色是否允许访问页面"""
    if role in ['hardware_admin', 'hardware_vikey_admin']:
        return True
    
    if role == 'super_admin':
        if path.startswith('/hardware/dashboard') or path.startswith('/api/hardware/'):
            return False
        return True
    
    if path in SPECIAL_ROUTE_RULES:
        return role in SPECIAL_ROUTE_RULES[path]['allowed_roles']
    
    for rule_path, rules in SPECIAL_ROUTE_RULES.items():
        if path.startswith(rule_path):
            return role in rules['allowed_roles']
    
    role_info = get_role_info(role)
    for allowed_path in role_info['pages']:
        if path.startswith(allowed_path):
            return True
    
    return False

def get_redirect_for_denied(path: str) -> str:
    """获取被拒绝访问时的重定向URL"""
    if path in SPECIAL_ROUTE_RULES:
        return SPECIAL_ROUTE_RULES[path]['redirect_if_denied']
    
    for rule_path, rules in SPECIAL_ROUTE_RULES.items():
        if path.startswith(rule_path):
            return rules['redirect_if_denied']
    
    return '/'

def validate_and_redirect(path: str) -> tuple:
    """验证访问权限并返回重定向结果"""
    user_id = session.get('user_id')
    role = session.get('role', 'guest')
    
    if not user_id:
        return False, '/login?next=' + path, 'NOT_LOGGED_IN'
    
    if role == 'guest':
        return False, '/login?next=' + path, 'ROLE_IS_GUEST'
    
    if not is_page_allowed(path, role):
        default_redirect = get_default_redirect(role)
        return False, default_redirect, 'INSUFFICIENT_PERMISSIONS'
    
    return True, path, 'ALLOWED'

def get_redirect_url_by_education(role: str, education: str) -> str:
    """根据教育体系获取重定向URL"""
    if education == 'k12':
        if role in ['student', 'student_vip']:
            return '/k12'
        elif role == 'teacher':
            return '/teacher'
    
    return get_default_redirect(role)

def get_smart_redirect_url(role: str) -> str:
    """智能获取重定向URL，考虑教育体系"""
    user_id = session.get('user_id')
    
    if not user_id:
        return get_default_redirect(role)
    
    try:
        education = get_user_education_system(user_id)
        if education:
            return get_redirect_url_by_education(role, education)
    except Exception as e:
        logger.warning(f"获取教育体系失败: {e}")
    
    return get_default_redirect(role)

@role_router_bp.route('/api/role/info')
def api_role_info():
    """获取当前用户角色信息"""
    role = session.get('role', 'guest')
    role_info = get_role_info(role)
    education_info = get_user_education_info()
    
    return jsonify({
        'success': True,
        'role': role,
        'default_redirect': role_info['default'],
        'smart_redirect': get_smart_redirect_url(role),
        'allowed_pages': role_info['pages'],
        'description': role_info['description'],
        'icon': role_info['icon'],
        'is_logged_in': 'user_id' in session,
        'education_info': education_info
    })

@role_router_bp.route('/api/role/check_access')
def api_check_access():
    """检查当前用户对指定路径的访问权限"""
    path = request.args.get('path', '')
    
    if not path:
        return jsonify({'success': False, 'error': '未指定路径'}), 400
    
    allowed, redirect_url, reason = validate_and_redirect(path)
    
    return jsonify({
        'success': True,
        'path': path,
        'allowed': allowed,
        'redirect_url': redirect_url,
        'reason': reason,
        'role': session.get('role', 'guest'),
        'education_info': get_user_education_info()
    })

@role_router_bp.route('/api/role/list')
def api_list_roles():
    """获取所有角色列表"""
    roles = []
    for role_code, role_info in ROLE_PAGE_MAPPING.items():
        roles.append({
            'role': role_code,
            'description': role_info['description'],
            'icon': role_info['icon'],
            'default_page': role_info['default'],
            'page_count': len(role_info['pages'])
        })
    
    return jsonify({
        'success': True,
        'roles': roles
    })

@role_router_bp.route('/api/role/validate')
def api_validate_role():
    """验证角色有效性"""
    role = request.args.get('role', '')
    
    if role in ROLE_PAGE_MAPPING:
        role_info = get_role_info(role)
        return jsonify({
            'success': True,
            'valid': True,
            'role': role,
            'description': role_info['description']
        })
    else:
        return jsonify({
            'success': True,
            'valid': False,
            'role': role,
            'error': '角色不存在'
        })

@role_router_bp.route('/api/role/route_rules')
def api_get_route_rules():
    """获取所有路由规则"""
    return jsonify({
        'success': True,
        'role_page_mapping': ROLE_PAGE_MAPPING,
        'special_route_rules': SPECIAL_ROUTE_RULES
    })

def create_role_routes(app):
    """创建角色路由"""
    @app.route('/role/redirect')
    def role_redirect():
        """根据角色重定向到默认页面"""
        role = session.get('role', 'guest')
        redirect_url = get_smart_redirect_url(role)
        logger.info(f"[角色路由] 用户角色: {role}, 智能重定向到: {redirect_url}")
        return redirect(redirect_url)
    
    @app.route('/role/switch/<new_role>')
    def role_switch(new_role):
        """切换角色（仅开发测试用）"""
        if new_role in ROLE_PAGE_MAPPING:
            session['role'] = new_role
            logger.info(f"[角色切换] 角色切换为: {new_role}")
            return redirect(get_smart_redirect_url(new_role))
        else:
            return jsonify({'success': False, 'error': '无效的角色'}), 400
    
    @app.route('/role/validate_and_redirect')
    def role_validate_and_redirect():
        """验证权限并重定向"""
        target_path = request.args.get('path', '/')
        allowed, redirect_url, reason = validate_and_redirect(target_path)
        
        if allowed:
            return redirect(target_path)
        else:
            logger.info(f"[角色路由] 权限验证失败 - 目标: {target_path}, 重定向: {redirect_url}, 原因: {reason}")
            return redirect(redirect_url)
    
    return app

def validate_login_redirect(role: str) -> str:
    """验证登录后的重定向URL"""
    return get_smart_redirect_url(role)