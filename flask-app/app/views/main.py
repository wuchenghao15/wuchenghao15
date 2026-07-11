# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for
from flask import session
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

main_bp = Blueprint('main', __name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(APP_ROOT)), 'templates'))

def get_user_context():
    """获取用户上下文信息"""
    return {
        'user': {
            'username': session.get('username', ''),
            'role': session.get('role', 'guest'),
            'user_id': session.get('user_id', 0),
            'email': session.get('email', '')
        }
    }

@main_bp.route('/')
def index():
    """首页"""
    return render_template('index.html')

@main_bp.route('/home')
def home():
    """主页"""
    return render_template('home.html')

@main_bp.route('/dashboard')
def dashboard():
    """仪表板 - 根据角色重定向到对应页面"""
    role = session.get('role', 'guest')
    
    role_redirect_map = {
        'student': '/exam_system',
        'student_vip': '/exam_system',
        'designer': '/arduino',
        'teacher': '/teacher',
        'researcher': '/researcher',
        'admin': '/settings',
        'super_admin': '/super_admin_dashboard',
        'hardware_admin': '/hardware/dashboard',
        'hardware_vikey_admin': '/hardware/dashboard',
        'guest': '/'
    }
    
    redirect_path = role_redirect_map.get(role, '/')
    return redirect(redirect_path)

@main_bp.route('/permissions')
def permissions():
    """权限管理页面"""
    return render_template('permissions.html', **get_user_context())

@main_bp.route('/ai_rules')
def ai_rules():
    """AI规则管理页面"""
    return render_template('dashboard.html', **get_user_context())

@main_bp.route('/approval')
def approval():
    """审批管理页面"""
    return render_template('approval.html', **get_user_context())

@main_bp.route('/cleanup')
def cleanup():
    """系统清理页面"""
    return render_template('cleanup.html', **get_user_context())

@main_bp.route('/projects')
def projects():
    """项目管理页面"""
    return render_template('projects.html', **get_user_context())

@main_bp.route('/tasks')
def tasks():
    """任务管理页面"""
    return render_template('tasks.html', **get_user_context())

@main_bp.route('/reports')
def reports():
    """报告中心页面"""
    return render_template('reports.html', **get_user_context())

@main_bp.route('/system_config')
def system_config():
    """系统配置页面"""
    return render_template('system_config.html', **get_user_context())

@main_bp.route('/hardware')
def hardware():
    """硬件管理页面"""
    return render_template('hardware.html', **get_user_context())

@main_bp.route('/hardware_keys')
def hardware_keys():
    """硬件密钥管理页面"""
    return render_template('hardware_keys.html', **get_user_context())

@main_bp.route('/system_monitoring')
def system_monitoring():
    """系统监控页面"""
    return render_template('system_monitoring.html', **get_user_context())

@main_bp.route('/language_test')
def language_test():
    """语言测试页面"""
    return render_template('language_test.html', **get_user_context())

@main_bp.route('/admin_app/learning_paths')
def admin_learning_paths():
    """学习路径管理页面"""
    return render_template('admin_app/learning_paths.html', **get_user_context())

@main_bp.route('/admin_app/exam_analysis')
def admin_exam_analysis():
    """考试数据分析页面"""
    return render_template('admin_app/exam_analysis.html', **get_user_context())