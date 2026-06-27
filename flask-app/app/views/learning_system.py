# -*- coding: utf-8 -*-
"""
学习系统视图模块
负责学习记录、错题本、学习分析等功能
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import logging

logger = logging.getLogger(__name__)

learning_system_bp = Blueprint('learning_system', __name__)

ALLOWED_ROLES = ['student']


def require_login():
    if 'user_id' not in session:
        logger.warning("[学习系统] 未登录用户尝试访问")
        return redirect(url_for('auth.login'))
    return None


def require_allowed_role():
    result = require_login()
    if result:
        return result
    
    role = session.get('role')
    if role not in ALLOWED_ROLES:
        logger.warning(f"[学习系统] 用户 {session.get('username')} ({role}) 权限不足")
        return jsonify({'success': False, 'error': '没有权限访问学习系统'}), 403
    return None


@learning_system_bp.route('/learning_system')
def learning_system_index():
    """学习系统首页"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    logger.info(f"[学习系统] 用户 {user['username']} ({user['role']}) 访问学习系统")
    return render_template('learning_system.html', user=user)


@learning_system_bp.route('/learning/history')
def learning_history():
    """学习历史记录页面"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('learning_history.html', user=user)


@learning_system_bp.route('/learning/wrong_questions')
def wrong_questions():
    """错题本页面"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('wrong_questions.html', user=user)


@learning_system_bp.route('/learning/analysis')
def learning_analysis():
    """学习分析页面"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('learning_analysis.html', user=user)


@learning_system_bp.route('/api/learning/user_info')
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


@learning_system_bp.route('/api/learning/history', methods=['GET'])
def get_learning_history():
    """获取学习历史记录"""
    result = require_allowed_role()
    if result:
        return result
    
    user_id = session.get('user_id')
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM learning_records 
                WHERE user_id = ? 
                ORDER BY created_at DESC LIMIT 20
            ''', (user_id,))
            records = cursor.fetchall()
            
            history = []
            for record in records:
                history.append({
                    'id': record['id'],
                    'subject': record.get('subject', ''),
                    'content': record.get('content', ''),
                    'duration': record.get('duration', 0),
                    'created_at': record.get('created_at', '')
                })
        
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        logger.error(f"获取学习历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@learning_system_bp.route('/api/learning/wrong_questions', methods=['GET'])
def get_wrong_questions():
    """获取错题列表"""
    result = require_allowed_role()
    if result:
        return result
    
    user_id = session.get('user_id')
    try:
        import sqlite3
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM wrong_questions 
                WHERE user_id = ? 
                ORDER BY wrong_count DESC LIMIT 30
            ''', (user_id,))
            questions = cursor.fetchall()
            
            wrong_list = []
            for q in questions:
                wrong_list.append({
                    'id': q['id'],
                    'question_id': q.get('question_id', ''),
                    'content': q.get('content', ''),
                    'wrong_count': q.get('wrong_count', 0),
                    'last_wrong_at': q.get('last_wrong_at', '')
                })
        
        return jsonify({'success': True, 'data': wrong_list})
    except Exception as e:
        logger.error(f"获取错题列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500