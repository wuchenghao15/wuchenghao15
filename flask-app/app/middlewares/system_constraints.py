#!/usr/bin/env python3
"""
System Constraints Middleware for MTSCOS AI System
系统约束中间件 - 处理特殊访问规则和业务约束
"""

from flask import request, session, redirect, jsonify, render_template
from functools import wraps
import logging

logger = logging.getLogger(__name__)

EDUCATION_SYSTEMS = {
    'adult': '成人教育',
    'k12': 'K12教育',
    'vocational': '职业教育',
    'higher': '高等教育'
}

SPECIAL_CONSTRAINTS = {
    '/math_training': {
        'name': '数学训练系统',
        'required_role': ['student', 'student_vip'],
        'required_education': ['adult'],
        'description': '仅成人制教育学生可访问'
    },
    '/exam_system': {
        'name': '考试系统',
        'required_role': ['student', 'student_vip'],
        'description': '仅学生角色可访问，教师、管理员等角色均被禁止'
    },
    '/learning_system': {
        'name': '学习系统',
        'required_role': ['student', 'student_vip'],
        'description': '仅学生角色可访问'
    },
    '/exam_center': {
        'name': '考试中心',
        'required_role': ['student', 'student_vip'],
        'description': '仅学生角色可访问'
    },
    '/exam_page/': {
        'name': '考试页面',
        'required_role': ['student', 'student_vip'],
        'description': '仅学生角色可访问'
    },
    '/exam_results': {
        'name': '考试结果',
        'required_role': ['student', 'student_vip'],
        'description': '仅学生角色可访问'
    },
    '/exam_history': {
        'name': '考试历史',
        'required_role': ['student', 'student_vip'],
        'description': '仅学生角色可访问'
    },
    '/physics-engine': {
        'name': '物理引擎',
        'required_role': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin', 'teacher', 'designer'],
        'description': '学生角色无权访问物理引擎'
    },
    '/settings': {
        'name': '系统设置',
        'required_role': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '仅管理员可访问设置页面'
    },
    '/super_admin_dashboard': {
        'name': '超级管理员控制台',
        'required_role': ['super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '仅超级管理员可访问'
    },
    '/hardware/dashboard': {
        'name': '硬件管理控制台',
        'required_role': ['hardware_admin', 'hardware_vikey_admin'],
        'description': '仅硬件管理员可访问'
    },
    '/admin_center': {
        'name': '管理中心',
        'required_role': ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '仅管理员可访问'
    },
    '/admin_app': {
        'name': '管理员专用App',
        'required_role': ['admin', 'super_admin', 'hardware_admin'],
        'description': '仅管理员可访问'
    },
    '/arduino': {
        'name': '设计师平台',
        'required_role': ['designer', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '仅设计师和管理员可访问'
    },
    '/teacher': {
        'name': '教师平台',
        'required_role': ['teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin'],
        'description': '仅教师和管理员可访问'
    },
    '/k12': {
        'name': 'K12教育系统',
        'required_role': ['student', 'student_vip', 'teacher'],
        'required_education': ['k12'],
        'description': '仅K12教育学生和教师可访问'
    },
    '/k12/subject/': {
        'name': 'K12学科学习',
        'required_role': ['student', 'student_vip', 'teacher'],
        'required_education': ['k12'],
        'require_grade': True,
        'description': '仅K12教育学生和教师可访问'
    },
    '/k12/exam': {
        'name': 'K12考试中心',
        'required_role': ['student', 'student_vip'],
        'required_education': ['k12'],
        'require_grade': True,
        'description': '仅K12教育学生可访问'
    },
    '/k12/report': {
        'name': 'K12学习报告',
        'required_role': ['student', 'student_vip'],
        'required_education': ['k12'],
        'require_grade': True,
        'description': '仅K12教育学生可访问'
    },
    '/k12/practice': {
        'name': 'K12智能练习',
        'required_role': ['student', 'student_vip', 'teacher'],
        'required_education': ['k12'],
        'description': '仅K12教育学生和教师可访问'
    },
}

ROLE_LEVELS = {
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

def get_user_education_system(user_id=None):
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

def get_user_grade(user_id=None):
    """获取用户年级"""
    if not user_id:
        user_id = session.get('user_id')
    
    if not user_id:
        return None
    
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT grade FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
    except Exception as e:
        logger.error(f"获取用户年级失败: {e}")
    
    return session.get('grade')

def check_special_constraint(path: str) -> tuple:
    """检查特殊约束"""
    for constraint_path, rules in SPECIAL_CONSTRAINTS.items():
        if path.startswith(constraint_path):
            return constraint_path, rules
    return None, None

def validate_constraint_rules(rules: dict) -> tuple:
    """验证约束规则"""
    user_id = session.get('user_id')
    role = session.get('role', '')
    grade = session.get('grade', '') or get_user_grade(user_id)
    
    if not user_id:
        return False, 'NOT_LOGGED_IN', '请先登录'
    
    if 'required_role' in rules:
        if role not in rules['required_role']:
            allowed_roles_str = ', '.join(rules['required_role'])
            return False, 'ROLE_NOT_ALLOWED', f"{rules['name']}仅允许以下角色访问: {allowed_roles_str}"
    
    if 'required_education' in rules:
        education = get_user_education_system(user_id)
        if education not in rules['required_education']:
            allowed_educations = ', '.join([EDUCATION_SYSTEMS.get(e, e) for e in rules['required_education']])
            return False, 'EDUCATION_NOT_ALLOWED', f"{rules['name']}仅{allowed_educations}学生可访问"
    
    if rules.get('require_grade', False):
        if not grade:
            return False, 'GRADE_NOT_SET', f"{rules['name']}需要先设置年级"
    
    return True, 'ALLOWED', '访问允许'

def system_constraints_middleware(app):
    """系统约束中间件"""
    
    @app.before_request
    def check_system_constraints():
        path = request.path
        
        if path.startswith('/static/') or path.startswith('/assets/'):
            return None
        
        if request.method == 'OPTIONS':
            return None
        
        constraint_path, rules = check_special_constraint(path)
        if constraint_path:
            allowed, code, message = validate_constraint_rules(rules)
            if not allowed:
                logger.warning(f"[系统约束] 访问受限 - 路径: {path}, 原因: {code}, 用户: {session.get('username')}")
                
                if request.is_json or path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': code,
                        'message': message,
                        'constraint': rules['name']
                    }), 403
                
                return render_template('403.html', 
                                      message=message,
                                      path=path,
                                      constraint=rules['name']), 403
        
        return None
    
    return app

def require_adult_education(f):
    """装饰器:要求成人教育学生"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')
        
        if not user_id:
            return redirect('/login?next=' + request.path)
        
        if role not in ['student', 'student_vip']:
            return jsonify({'success': False, 'error': 'ROLE_NOT_ALLOWED', 'message': '仅限学生访问'}), 403
        
        education = get_user_education_system(user_id)
        if education != 'adult':
            return jsonify({'success': False, 'error': 'EDUCATION_NOT_ALLOWED', 'message': '仅限成人制教育学生访问'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def require_k12_education(f):
    """装饰器:要求K12教育学生"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        role = session.get('role', '')
        
        if not user_id:
            return redirect('/login?next=' + request.path)
        
        if role not in ['student', 'student_vip', 'teacher']:
            return jsonify({'success': False, 'error': 'ROLE_NOT_ALLOWED', 'message': '仅限学生和教师访问'}), 403
        
        education = get_user_education_system(user_id)
        if education != 'k12':
            return jsonify({'success': False, 'error': 'EDUCATION_NOT_ALLOWED', 'message': '仅限K12教育学生访问'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def check_education_access(user_id=None) -> dict:
    """检查用户教育体系访问权限"""
    if not user_id:
        user_id = session.get('user_id')
    
    if not user_id:
        return {
            'has_access': False,
            'education_system': None,
            'allowed_features': [],
            'message': '用户未登录'
        }
    
    education = get_user_education_system(user_id)
    role = session.get('role', '')
    
    if education == 'adult':
        return {
            'has_access': True,
            'education_system': 'adult',
            'education_name': '成人教育',
            'allowed_features': ['exam_system', 'learning_system', 'math_training'],
            'message': '成人教育学生'
        }
    elif education == 'k12':
        features = ['k12', 'exam_system', 'learning_system']
        if role == 'teacher':
            features.append('teacher')
        return {
            'has_access': True,
            'education_system': 'k12',
            'education_name': 'K12教育',
            'allowed_features': features,
            'message': 'K12教育学生'
        }
    elif education == 'vocational':
        return {
            'has_access': True,
            'education_system': 'vocational',
            'education_name': '职业教育',
            'allowed_features': ['exam_system', 'learning_system'],
            'message': '职业教育学生'
        }
    elif education == 'higher':
        return {
            'has_access': True,
            'education_system': 'higher',
            'education_name': '高等教育',
            'allowed_features': ['exam_system', 'learning_system'],
            'message': '高等教育学生'
        }
    else:
        return {
            'has_access': False,
            'education_system': education,
            'allowed_features': [],
            'message': f'未知教育体系: {education}'
        }

def get_user_education_info() -> dict:
    """获取用户教育信息"""
    user_id = session.get('user_id')
    education = get_user_education_system(user_id)
    grade = get_user_grade(user_id)
    
    return {
        'user_id': user_id,
        'education_system': education,
        'education_name': EDUCATION_SYSTEMS.get(education, education),
        'grade': grade,
        'is_adult': education == 'adult',
        'is_k12': education == 'k12',
        'is_vocational': education == 'vocational',
        'is_higher': education == 'higher',
        'has_grade': bool(grade),
        'education_access': check_education_access(user_id)
    }

def validate_student_only_access(path: str) -> tuple:
    """验证学生专属访问"""
    role = session.get('role', '')
    
    student_only_paths = ['/exam_system', '/learning_system', '/math_training']
    
    if path in student_only_paths or any(path.startswith(p) for p in student_only_paths):
        if role not in ['student', 'student_vip']:
            return False, 'STUDENT_ONLY', '此功能仅限学生使用'
    
    return True, 'ALLOWED', '访问允许'

def validate_admin_only_access(path: str) -> tuple:
    """验证管理员专属访问"""
    role = session.get('role', '')
    
    admin_only_paths = ['/settings', '/admin_center', '/super_admin_dashboard', '/hardware/dashboard', '/admin_app']
    
    if path in admin_only_paths or any(path.startswith(p) for p in admin_only_paths):
        if role not in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            return False, 'ADMIN_ONLY', '此功能仅限管理员使用'
    
    return True, 'ALLOWED', '访问允许'