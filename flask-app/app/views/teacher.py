# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask import session
import os

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

teacher_bp = Blueprint('teacher', __name__, template_folder=os.path.join(APP_ROOT, '../templates/teacher'))


def requires_teacher(func):
    """教师权限装饰器"""
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login?next=' + request.path)
        
        role = session.get('role', 'guest')
        if role not in ['teacher', 'admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']:
            return render_template('error.html',
                                   error_code=403,
                                   error_title='权限不足',
                                   error_message='您没有权限访问此资源',
                                   error_suggestion='请使用教师账户登录'), 403
        return func(*args, **kwargs)
    decorated.__name__ = func.__name__
    return decorated


def get_teacher_user_info():
    """获取教师用户信息"""
    return {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', ''),
        'is_teacher': session.get('role') == 'teacher',
        'is_admin': session.get('role') in ['admin', 'super_admin', 'hardware_admin', 'hardware_vikey_admin']
    }


@teacher_bp.route('/teacher')
@requires_teacher
def teacher_index():
    """教师首页 - 重定向到仪表板"""
    return redirect('/teacher/dashboard')


@teacher_bp.route('/teacher/dashboard')
@requires_teacher
def teacher_dashboard():
    """教师仪表板"""
    return render_template('dashboard.html')


@teacher_bp.route('/teacher/students')
@requires_teacher
def teacher_students():
    """学生管理页面"""
    return render_template('dashboard.html')


@teacher_bp.route('/teacher/homework')
@requires_teacher
def teacher_homework():
    """作业管理页面"""
    return render_template('dashboard.html')


@teacher_bp.route('/teacher/exams')
@requires_teacher
def teacher_exams():
    """考试管理页面"""
    return render_template('dashboard.html')


@teacher_bp.route('/teacher/grades')
@requires_teacher
def teacher_grades():
    """成绩分析页面"""
    return render_template('dashboard.html')


@teacher_bp.route('/teacher/questions')
@requires_teacher
def teacher_questions():
    """题库管理页面"""
    return render_template('dashboard.html')


@teacher_bp.route('/teacher/reports')
@requires_teacher
def teacher_reports():
    """报告页面"""
    return render_template('dashboard.html')


@teacher_bp.route('/teacher/papers')
@requires_teacher
def teacher_papers():
    """论文文献参考页面"""
    return render_template('dashboard.html')