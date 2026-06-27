# -*- coding: utf-8 -*-
"""
考试系统视图模块
负责正式考试、考试中心、考试结果等功能
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import logging

logger = logging.getLogger(__name__)

exam_system_bp = Blueprint('exam_system', __name__)

ALLOWED_ROLES = ['student']


def require_login():
    if 'user_id' not in session:
        logger.warning("[考试系统] 未登录用户尝试访问")
        return redirect(url_for('auth.login'))
    return None


def require_allowed_role():
    result = require_login()
    if result:
        return result
    
    role = session.get('role')
    if role not in ALLOWED_ROLES:
        logger.warning(f"[考试系统] 用户 {session.get('username')} ({role}) 权限不足")
        return jsonify({'success': False, 'error': '没有权限访问考试系统'}), 403
    return None


@exam_system_bp.route('/exam_center')
def exam_center():
    """考试中心 - 展示可用考试列表"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('exam_center.html', user=user)


@exam_system_bp.route('/exam_page/<exam_id>')
def exam_page(exam_id):
    """考试页面 - 学生答题界面"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    logger.info(f"[考试系统] 用户 {user['username']} 进入考试: {exam_id}")
    return render_template('exam_page.html', user=user, exam_id=exam_id)


@exam_system_bp.route('/exam_results')
def exam_results():
    """考试结果页面"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('exam_results.html', user=user)


@exam_system_bp.route('/exam_history')
def exam_history():
    """考试历史记录页面"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    return render_template('exam_history.html', user=user)


@exam_system_bp.route('/exam')
def exam_redirect():
    """考试入口重定向"""
    result = require_allowed_role()
    if result:
        return result
    
    exam_id = request.args.get('exam_id')
    if exam_id:
        return redirect(url_for('exam_system.exam_page', exam_id=exam_id))
    else:
        return redirect(url_for('exam_system.exam_center'))