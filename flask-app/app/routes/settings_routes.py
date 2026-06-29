# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Settings Routes with Permission Control
设置页面路由(带权限控制)
"""

import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime
from functools import wraps
from app.utils.permission_manager import get_permission_manager, check_permission, check_role
from app.utils.session_manager import get_session_manager, login_required
from app.middlewares.access_control import require_admin, require_super_admin
import sys

app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(app_root, 'app.db')

settings_bp = Blueprint('settings', __name__)


def log_unauthorized_access(request, resource):
    """记录未授权访问尝试到数据库"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO system_logs (level, module, message, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', ('WARNING', 'security', f'未授权访问尝试: {resource}', request.remote_addr, datetime.now()))
            
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to log unauthorized access: {e}")


def log_error(error_type, message, details=''):
    """记录错误到数据库供AI学习"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_learning_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved INTEGER DEFAULT 0,
            ai_analyzed INTEGER DEFAULT 0
            )
            ''')
            
            cursor.execute('''
            INSERT INTO ai_learning_errors (error_type, message, details)
            VALUES (?, ?, ?)
            ''', (error_type, message, details))
            
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to log error: {e}")
        return False


@settings_bp.route('/settings', methods=['GET'])
@require_admin
def settings_page():
    """设置页面 - 需要管理员权限"""
    try:
        user_info = {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role')
        }
        return render_template('settings.html', user=user_info)
    except Exception as e:
        log_error('settings_page_error', str(e), '设置页面渲染失败')
        return render_template('error.html', error=f'设置页面加载失败: {str(e)}'), 500


@settings_bp.route('/api/settings/general', methods=['GET'])
@require_admin
def get_general_settings():
    """获取通用设置 - 需要管理员权限"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value FROM system_settings WHERE category = "general"')
            settings = {row[0]: json.loads(row[1]) if row[1].startswith('{') or row[1].startswith('[') else row[1] for row in cursor.fetchall()}
            
        
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        log_error('settings_api_error', str(e), '获取通用设置失败')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/general', methods=['POST'])
@require_admin
def update_general_settings():
    """更新通用设置 - 需要管理员权限"""
    try:
        data = request.get_json()
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            category TEXT DEFAULT "general",
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            for key, value in data.items():
                value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                
                cursor.execute('''
                INSERT OR REPLACE INTO system_settings (key, value, category, updated_at)
                VALUES (?, ?, "general", ?)
                ''', (key, value_str, datetime.now()))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '设置更新成功'
        })
    except Exception as e:
        log_error('settings_update_error', str(e), '更新通用设置失败')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/language', methods=['GET'])
def get_language_settings():
    """获取语言设置 - 所有用户都可以访问"""
    try:
        current_lang = session.get('language', 'zh-CN')
        
        languages = [
            {"code": "zh-CN", "name": "简体中文", "native_name": "简体中文"},
            {"code": "zh-TW", "name": "繁体中文", "native_name": "繁體中文"},
            {"code": "ja", "name": "日语", "native_name": "日本語"},
            {"code": "ko", "name": "韩语", "native_name": "한국어"},
            {"code": "en", "name": "英语", "native_name": "English"}
        ]
        
        return jsonify({
            'success': True,
            'current_language': current_lang,
            'available_languages': languages
        })
    except Exception as e:
        log_error('language_settings_error', str(e), '获取语言设置失败')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/language', methods=['POST'])
def set_language():
    """设置语言 - 所有用户都可以设置"""
    try:
        data = request.get_json()
        lang_code = data.get('lang', 'zh-CN')
        
        session['language'] = lang_code
        
        return jsonify({
            'success': True,
            'message': '语言设置成功',
            'language': lang_code
        })
    except Exception as e:
        log_error('language_set_error', str(e), '设置语言失败')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/permissions', methods=['GET'])
@require_admin
def get_permission_settings():
    """获取权限设置 - 需要管理员权限"""
    try:
        pm = get_permission_manager()
        roles = pm.get_all_roles()
        permissions = pm.get_all_permissions()
        
        return jsonify({
            'success': True,
            'roles': roles,
            'permissions': permissions
        })
    except Exception as e:
        log_error('permission_settings_error', str(e), '获取权限设置失败')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/permissions/user/<int:user_id>', methods=['GET'])
@require_admin
def get_user_permissions(user_id):
    """获取用户权限 - 需要管理员权限"""
    try:
        pm = get_permission_manager()
        role = pm.get_user_role(user_id)
        permissions = pm.get_role_permissions(role)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'role': role,
            'permissions': permissions
        })
    except Exception as e:
        log_error('user_permissions_error', str(e), '获取用户权限失败')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/permissions/user/<int:user_id>/role', methods=['PUT'])
@require_admin
def update_user_role(user_id):
    """更新用户角色 - 需要管理员权限"""
    try:
        data = request.get_json()
        role_name = data.get('role')
        
        pm = get_permission_manager()
        success = pm.set_user_role(user_id, role_name)
        
        if success:
            # 更新session中的角色
            session['role'] = role_name
            return jsonify({
                'success': True,
                'message': '用户角色更新成功',
                'role': role_name
            })
        else:
            return jsonify({
                'success': False,
                'error': '无效的角色名称'
            }), 400
    except Exception as e:
        log_error('update_user_role_error', str(e), '更新用户角色失败')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/errors', methods=['GET'])
@require_admin
def get_errors_for_ai():
    """获取错误列表供AI学习 - 需要管理员权限"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, error_type, message, details, created_at, resolved, ai_analyzed 
            FROM ai_learning_errors 
            ORDER BY created_at DESC 
            LIMIT 100
            ''')
            
            errors = []
            for row in cursor.fetchall():
                errors.append({
                    'id': row[0],
                    'error_type': row[1],
                    'message': row[2],
                    'details': row[3],
                    'created_at': row[4],
                    'resolved': bool(row[5]),
                    'ai_analyzed': bool(row[6])
                })
            
        
        return jsonify({
            'success': True,
            'errors': errors,
            'count': len(errors)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/errors/<int:error_id>', methods=['PUT'])
@require_admin
def update_error_status(error_id):
    """更新错误状态 - 需要管理员权限"""
    try:
        data = request.get_json()
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn_cursor = conn.cursor()
            cursor = conn.cursor()
            
            if 'resolved' in data:
                cursor.execute('UPDATE ai_learning_errors SET resolved = ?, updated_at = ? WHERE id = ?',
                    (1 if data['resolved'] else 0, datetime.now(), error_id))
            if 'ai_analyzed' in data:
                cursor.execute('UPDATE ai_learning_errors SET ai_analyzed = ?, updated_at = ? WHERE id = ?',
                    (1 if data['ai_analyzed'] else 0, datetime.now(), error_id))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': '错误状态更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/session', methods=['GET'])
@login_required
def get_session_info():
    """获取当前会话信息 - 需要登录"""
    try:
        session_id = session.get('session_id')
        sm = get_session_manager()
        session_data = sm.get_session_info(session_id)
        
        if session_data:
            return jsonify({
                'success': True,
                'session': {
                    'user_id': session_data['user_id'],
                    'username': session_data['username'],
                    'role': session_data['role'],
                    'created_at': session_data['created_at'],
                    'last_access': session_data['last_access'],
                    'expires_at': session_data['expires_at']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/api/settings/session/logout', methods=['POST'])
def logout():
    """退出登录"""
    try:
        session_id = session.get('session_id')
        if session_id:
            sm = get_session_manager()
            sm.invalidate_session(session_id)
        
        session.clear()
        
        return jsonify({
            'success': True,
            'message': '退出登录成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.errorhandler(403)
def forbidden(e):
    """处理未授权访问"""
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': '您没有权限访问此资源'
    }), 403


@settings_bp.errorhandler(401)
def unauthorized(e):
    """处理未登录访问"""
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': '请先登录'
    }), 401
