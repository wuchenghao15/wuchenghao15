# -*- coding: utf-8 -*-
"""
用户信息管理系统视图模块
负责用户个人资料、密码修改、设置等功能
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import logging
import hashlib
import base64

logger = logging.getLogger(__name__)

user_system_bp = Blueprint('user_system', __name__)


def require_login():
    if 'user_id' not in session:
        logger.warning("[用户系统] 未登录用户尝试访问")
        return redirect(url_for('auth.login'))
    return None


def hash_password(password):
    return base64.b64encode(hashlib.sha256(password.encode()).digest()).decode()


@user_system_bp.route('/user_system')
def user_system_index():
    """用户信息管理系统首页"""
    result = require_login()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    logger.info(f"[用户系统] 用户 {user['username']} ({user['role']}) 访问用户信息管理系统")
    return render_template('user_system.html', user=user)


@user_system_bp.route('/user/profile')
def user_profile():
    """用户个人资料页面"""
    result = require_login()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('profile.html', user=user)


@user_system_bp.route('/user/settings')
def user_settings():
    """用户设置页面"""
    result = require_login()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('settings.html', user=user)


@user_system_bp.route('/api/user/info')
def get_user_info():
    """获取当前用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': session.get('user_id'),
            'username': session.get('username', ''),
            'role': session.get('role', ''),
            'email': session.get('email', '')
        }
    })


@user_system_bp.route('/api/user/update_profile', methods=['POST'])
def update_profile():
    """更新用户个人资料"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json()
    email = data.get('email')
    
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET email = ? WHERE id = ?', (email, user_id))
            conn.commit()
        
        session['email'] = email
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@user_system_bp.route('/api/user/change_password', methods=['POST'])
def change_password():
    """修改用户密码"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'success': False, 'error': '用户不存在'}), 404
            
            stored_password = row['password']
            
            if stored_password != hash_password(old_password):
                return jsonify({'success': False, 'error': '原密码错误'}), 400
            
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hash_password(new_password), user_id))
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500