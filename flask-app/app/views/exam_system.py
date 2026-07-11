# -*- coding: utf-8 -*-
"""
考试系统视图模块
负责正式考试、考试中心、考试结果等功能
使用统一权限装饰器进行权限控制
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from app.middlewares.permission_decorators import require_student, require_student_or_vip, get_permission_info
import logging

logger = logging.getLogger(__name__)

exam_system_bp = Blueprint('exam_system', __name__)


def get_user_info():
    """获取当前用户信息"""
    return get_permission_info()


@exam_system_bp.route('/exam_center')
@require_student
def exam_center():
    """考试中心 - 展示可用考试列表"""
    user_info = get_user_info()
    logger.info(f"[考试系统] 用户 {user_info['username']} ({user_info['role']}) 访问考试中心")
    
    return render_template('exam_center.html', user=user_info)


@exam_system_bp.route('/exam_page/<exam_id>')
@require_student
def exam_page(exam_id):
    """考试页面 - 学生答题界面"""
    user_info = get_user_info()
    logger.info(f"[考试系统] 用户 {user_info['username']} ({user_info['role']}) 进入考试: {exam_id}")
    
    return render_template('exam_page.html', user=user_info, exam_id=exam_id)


@exam_system_bp.route('/exam_results')
@require_student
def exam_results():
    """考试结果页面"""
    user_info = get_user_info()
    logger.info(f"[考试系统] 用户 {user_info['username']} ({user_info['role']}) 访问考试结果")
    
    return render_template('exam_results.html', user=user_info)


@exam_system_bp.route('/exam_history')
@require_student
def exam_history():
    """考试历史记录页面"""
    user_info = get_user_info()
    logger.info(f"[考试系统] 用户 {user_info['username']} ({user_info['role']}) 访问考试历史")
    
    return render_template('exam_history.html', user=user_info)


@exam_system_bp.route('/exam')
@require_student
def exam_redirect():
    """考试入口重定向"""
    exam_id = request.args.get('exam_id')
    if exam_id:
        return redirect(url_for('exam_system.exam_page', exam_id=exam_id))
    else:
        return redirect(url_for('exam_system.exam_center'))


@exam_system_bp.route('/exam_system')
@require_student_or_vip
def exam_system_index():
    """考试系统首页"""
    user_info = get_user_info()
    logger.info(f"[考试系统] 用户 {user_info['username']} ({user_info['role']}) 访问考试系统首页")
    
    return render_template('exam_system.html', user=user_info)