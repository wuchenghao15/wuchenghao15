# -*- coding: utf-8 -*-
"""
系统维护路由
提供维护AI员工、系统说明书、使用说明书和初次登录引导功能
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from app.ai.maintenance_ai import maintenance_ai
from app.version import VERSION, VERSION_INFO, CHANGELOG
from datetime import datetime

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')
docs_bp = Blueprint('docs', __name__, url_prefix='/docs')


def get_db_connection():
    """获取数据库连接"""
    import sqlite3
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def is_admin():
    """检查当前用户是否为管理员"""
    return session.get('role') == 'admin'


def login_required(func):
    """登录装饰器"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def admin_required(func):
    """管理员装饰器"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'error': '需要管理员权限'}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@maintenance_bp.route('/run', methods=['POST'])
@admin_required
def run_maintenance():
    """运行例行维护"""
    try:
        results = maintenance_ai.run_routine_maintenance()
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        results = maintenance_ai.run_health_check()
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/backup', methods=['POST'])
@admin_required
def create_backup():
    """创建备份"""
    try:
        result = maintenance_ai.backup_manager.create_backup()
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/cleanup', methods=['POST'])
@admin_required
def run_cleanup():
    """运行清理"""
    try:
        result = maintenance_ai.db_cleaner.clean_all()
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/status', methods=['GET'])
@login_required
def get_maintenance_status():
    """获取维护状态"""
    try:
        status = maintenance_ai.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@maintenance_bp.route('/log-cleanup', methods=['POST'])
@admin_required
def clean_logs():
    """清理日志"""
    try:
        days = request.json.get('days', 30)
        result = maintenance_ai.log_cleaner.clean_old_log_files(days)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@docs_bp.route('/system-manual')
@login_required
def system_manual():
    """系统说明书页面"""
    return render_template('system_manual.html', version=VERSION)


@docs_bp.route('/user-manual')
@login_required
def user_manual():
    """使用说明书页面"""
    return render_template('user_manual.html', version=VERSION)


@docs_bp.route('/changelog')
@login_required
def changelog():
    """更新日志页面"""
    return render_template('changelog.html', changelog=CHANGELOG, version=VERSION)


@docs_bp.route('/onboarding')
@login_required
def onboarding():
    """初次登录引导页面"""
    if is_admin():
        return redirect('/')
    
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT has_completed_onboarding FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['has_completed_onboarding']:
            return redirect('/')
    except Exception:
        pass
    
    role_name = {
        'admin': '管理员',
        'teacher': '教师',
        'student': '学生',
        'user': '普通用户'
    }.get(session.get('role'), '用户')
    
    return render_template(
        'onboarding.html',
        username=session.get('username'),
        role=session.get('role'),
        role_name=role_name
    )


@docs_bp.route('/api/onboarding/complete', methods=['POST'])
@login_required
def complete_onboarding():
    """完成引导"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET has_completed_onboarding = 1, last_onboarding_at = ? 
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'redirect_url': '/'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@docs_bp.route('/api/check-onboarding', methods=['GET'])
@login_required
def check_onboarding():
    """检查是否需要引导"""
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        
        if role == 'admin':
            return jsonify({
                'success': True,
                'data': {
                    'needs_onboarding': False,
                    'has_completed': True,
                    'is_admin': True
                }
            })
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT has_completed_onboarding FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        has_completed = user['has_completed_onboarding'] if user else False
        
        return jsonify({
            'success': True,
            'data': {
                'needs_onboarding': not has_completed,
                'has_completed': has_completed,
                'is_admin': False
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


__all__ = ['maintenance_bp', 'docs_bp']