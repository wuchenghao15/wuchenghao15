# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, session, jsonify, flash
from app.utils.security import security_utils
from app.utils.logging import logger
from app.utils.session_manager import session_manager
import logging
import json

session_management_bp = Blueprint('session_management', __name__)

@session_management_bp.route('/sessions')
@security_utils.login_required
def manage_sessions():
    """管理会话页面"""
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        sessions = session_manager.get_user_sessions(user_id)
        current_session_id = session.get('session_id')
        device_limit = session_manager.get_device_limit(user_id)
        return render_template('session_management.html', 
                             sessions=sessions,
                             current_session_id=current_session_id,
                             device_limit=device_limit)
    except Exception as e:
        logger.error(f"管理会话页面失败: {str(e)}")
        return render_template('session_management.html')

@session_management_bp.route('/sessions/invalidate/<session_id>', methods=['POST'])
def invalidate_session(session_id):
    """使特定会话失效"""
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        sessions = session_manager.get_user_sessions(user_id)
        session_found = any(s['session_id'] == session_id for s in sessions)
        
        if not session_found:
            flash('会话不存在或无权操作', 'error')
            return redirect(url_for('session_management.manage_sessions'))
        
        session_manager.invalidate_session(session_id)
        flash('会话已失效', 'success')
        return redirect(url_for('session_management.manage_sessions'))
    except Exception as e:
        logger.error(f"使会话失效失败: {str(e)}")
        return redirect(url_for('session_management.manage_sessions'))

@session_management_bp.route('/sessions/invalidate-all', methods=['POST'])
def invalidate_all_sessions():
    """使所有会话失效"""
    try:
        username = session.get('username')
        logger.info(f"用户 {username} 使所有会话失效")
        flash('所有会话已失效,请重新登录', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"使所有会话失效失败: {str(e)}")
        return redirect(url_for('session_management.manage_sessions'))

@session_management_bp.route('/api/sessions')
def get_sessions_api():
    """获取会话列表的API端点"""
    try:
        user_id = session.get('user_id')
        sessions = session_manager.get_user_sessions(user_id)
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        logger.error(f"获取会话列表API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@session_management_bp.route('/api/sessions/invalidate/<session_id>', methods=['POST'])
def invalidate_session_api(session_id):
    """使特定会话失效的API端点"""
    try:
        user_id = session.get('user_id')
        sessions = session_manager.get_user_sessions(user_id)
        session_found = any(s['session_id'] == session_id for s in sessions)
        
        if not session_found:
            return jsonify({'success': False, 'error': '会话不存在或无权操作'})
        
        session_manager.invalidate_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"使会话失效API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@session_management_bp.route('/api/sessions/invalidate-all', methods=['POST'])
def invalidate_all_sessions_api():
    """使所有会话失效的API端点"""
    try:
        user_id = session.get('user_id')
        session_manager.invalidate_all_user_sessions(user_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"使所有会话失效API失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
