# -*- coding: utf-8 -*-
"""
测试系统视图模块
负责摸底测试、水平测试等功能
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import logging

logger = logging.getLogger(__name__)

test_system_bp = Blueprint('test_system', __name__)

ALLOWED_ROLES = ['student']


def require_login():
    if 'user_id' not in session:
        logger.warning("[测试系统] 未登录用户尝试访问")
        return redirect(url_for('auth.login'))
    return None


def require_allowed_role():
    result = require_login()
    if result:
        return result
    
    role = session.get('role')
    if role not in ALLOWED_ROLES:
        logger.warning(f"[测试系统] 用户 {session.get('username')} ({role}) 权限不足")
        return jsonify({'success': False, 'error': '没有权限访问测试系统'}), 403
    return None


def get_user_education_type(user_id):
    import sqlite3
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT education_level FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"获取用户教育类型失败: {e}")
        return None


def set_user_education_type(user_id, education_type):
    import sqlite3
    db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET education_level = ? WHERE id = ?', (education_type, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"设置用户教育类型失败: {e}")
        return False


@test_system_bp.route('/test_system')
def test_system_index():
    """测试系统首页"""
    result = require_allowed_role()
    if result:
        return result
    
    user = {
        'username': session.get('username', ''),
        'role': session.get('role', ''),
        'user_id': session.get('user_id', '')
    }
    
    logger.info(f"[测试系统] 用户 {user['username']} ({user['role']}) 访问测试系统")
    return render_template('test_system.html', user=user)


@test_system_bp.route('/test/select_education_type')
def select_education_type():
    """选择教育类型页面"""
    result = require_login()
    if result:
        return result
    
    user_id = session.get('user_id', 0)
    education_type = get_user_education_type(user_id)
    
    if education_type in ['compulsory', 'adult']:
        return redirect('/test/placement_test')
    
    return render_template('education_type_select.html')


@test_system_bp.route('/api/test/education/set-type', methods=['POST'])
def api_set_education_type():
    """设置教育类型API"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.get_json()
    education_type = data.get('type')
    
    if education_type not in ['compulsory', 'adult']:
        return jsonify({'success': False, 'error': '无效的教育类型'}), 400
    
    if set_user_education_type(user_id, education_type):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '设置失败'}), 500


@test_system_bp.route('/test/placement_test')
def placement_test_page():
    """摸底测试页面"""
    result = require_login()
    if result:
        return result
    
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        return redirect('/dashboard')
    
    education_type = get_user_education_type(user_id)
    if education_type not in ['compulsory', 'adult']:
        return redirect('/test/select_education_type')
    
    has_completed = False
    current_level = None
    try:
        from app.services.placement_test_service import get_placement_test_service
        placement_service = get_placement_test_service()
        reports = placement_service.get_user_reports(user_id, limit=1)
        if reports:
            has_completed = True
            current_level = reports[0].get('overall_level')
    except Exception as e:
        logger.error(f"检查摸底测试状态失败: {e}")
    
    grade_manager = None
    user_grade = None
    try:
        from app.services.grade_manager import get_grade_manager
        grade_manager = get_grade_manager()
        user_grade = grade_manager.get_user_grade(user_id)
    except Exception as e:
        logger.error(f"获取用户年级失败: {e}")
    
    if education_type == 'compulsory':
        compulsory_subjects = ['语文', '数学', '英语', '物理', '化学', '生物']
        
        if user_grade:
            grade_index = grade_manager.get_grade_index(user_grade) if grade_manager else 0
            
            if grade_index <= 5:
                compulsory_subjects = ['语文', '数学', '英语']
            elif grade_index <= 8:
                compulsory_subjects = ['语文', '数学', '英语', '物理', '化学', '生物']
            else:
                compulsory_subjects = ['语文', '数学', '英语', '物理', '化学', '生物']
        
        test_info = {
            'title': '义务教育摸底测试',
            'description': '根据九年制义务教育课程标准，评估您各学科的知识水平',
            'duration': '60分钟',
            'questions': '60道',
            'subjects': compulsory_subjects,
            'education_type': 'compulsory',
            'mode': 'all_subjects',
            'grade': user_grade
        }
    else:
        adult_subjects = [
            {'id': 'japanese', 'name': '日语', 'description': '日语能力测试', 'icon': '🇯🇵'},
            {'id': 'english', 'name': '英语', 'description': '英语水平测试', 'icon': '🇺🇸'},
            {'id': 'adult_college', 'name': '成人大学', 'description': '成人高等教育入学测试', 'icon': '🎓'},
            {'id': 'ielts', 'name': '雅思', 'description': 'IELTS模拟测试', 'icon': '📝'},
            {'id': 'toefl', 'name': '托福', 'description': 'TOEFL模拟测试', 'icon': '📚'}
        ]
        
        test_info = {
            'title': '成人教育摸底测试',
            'description': '请选择您想要参加的测试项目',
            'duration': '45分钟',
            'questions': '30道',
            'subjects': adult_subjects,
            'education_type': 'adult',
            'mode': 'select_subjects',
            'grade': user_grade
        }
    
    return render_template('placement_test.html', 
                           username=username, 
                           role=role,
                           user_id=user_id,
                           has_completed=has_completed,
                           current_level=current_level,
                           test_info=test_info)


@test_system_bp.route('/test/placement_test/take/<test_id>')
def take_placement_test(test_id):
    """摸底测试答题页面"""
    result = require_login()
    if result:
        return result
    
    username = session.get('username', '未知用户')
    role = session.get('role', 'guest')
    user_id = session.get('user_id', 0)
    
    student_roles = ['student', 'student_vip', 'exam_expert']
    if role not in student_roles:
        return redirect('/dashboard')
    
    try:
        from app.services.placement_test_service import get_placement_test_service
        placement_service = get_placement_test_service()
        test = placement_service.get_placement_test(test_id)
        if not test or test['user_id'] != user_id:
            return redirect('/test/placement_test')
    except Exception as e:
        logger.error(f"验证测试失败: {e}")
        return redirect('/test/placement_test')
    
    return render_template('placement_test_take.html', 
                           username=username,
                           test_id=test_id)