#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
9年制学生升级管理系统 - API服务
提供完整的RESTful API接口
版本: 1.1 - 从小学1年级开始的完整9年制体系
"""

from flask import Flask, request, jsonify, Blueprint
import sqlite3
from datetime import datetime
from functools import wraps
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nine_year_upgrade_system import NineYearUpgradeSystem, GradeLevel, Subject

app = Flask(__name__)
nine_year_bp = Blueprint('nine_year', __name__, url_prefix='/api/nine-year')

DB_PATH = 'mtcos_system.db'


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def require_permission(min_level):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_level = int(request.headers.get('X-User-Level', 20))
            if user_level < min_level:
                return jsonify({'success': False, 'error': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@nine_year_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': '9年制升级系统API运行正常 (v1.1)',
        'version': '1.1',
        'timestamp': datetime.now().isoformat()
    })


# ==================== 学生年级管理 ====================

@nine_year_bp.route('/register', methods=['POST'])
def register_student_grade():
    """注册学生年级"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        grade_code = data.get('grade')
        
        if not user_id or not grade_code:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 将字符串转换为GradeLevel枚举
        grade_map = {
            'grade1': GradeLevel.GRADE_1,
            'grade2': GradeLevel.GRADE_2,
            'grade3': GradeLevel.GRADE_3,
            'grade4': GradeLevel.GRADE_4,
            'grade5': GradeLevel.GRADE_5,
            'grade6': GradeLevel.GRADE_6,
            'grade7': GradeLevel.GRADE_7,
            'grade8': GradeLevel.GRADE_8,
            'grade9': GradeLevel.GRADE_9
        }
        
        grade = grade_map.get(grade_code)
        if not grade:
            return jsonify({'success': False, 'error': '无效的年级代码'}), 400
        
        system = NineYearUpgradeSystem()
        result = system.register_student_grade(user_id, grade)
        
        if result:
            return jsonify({
                'success': True,
                'message': '学生注册成功',
                'grade': grade_code
            })
        else:
            return jsonify({'success': False, 'error': '学生已注册'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/status/<user_id>', methods=['GET'])
def get_student_status(user_id):
    """获取学生状态"""
    try:
        system = NineYearUpgradeSystem()
        status = system.get_student_status(user_id)
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/confirm/<user_id>', methods=['POST'])
def confirm_grade(user_id):
    """确认年级"""
    try:
        system = NineYearUpgradeSystem()
        result = system.confirm_grade(user_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': '年级确认成功'
            })
        else:
            return jsonify({'success': False, 'error': '确认失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 考试管理 ====================

@nine_year_bp.route('/exam/create', methods=['POST'])
def create_exam():
    """创建考试"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        exam_type = data.get('exam_type')
        subject_code = data.get('subject')
        grade_code = data.get('grade')
        
        if not all([user_id, exam_type, subject_code, grade_code]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 映射为枚举
        subject_map = {
            '语文': Subject.CHINESE,
            '数学': Subject.MATH,
            '英语': Subject.ENGLISH,
            '物理': Subject.PHYSICS,
            '化学': Subject.CHEMISTRY,
            '生物': Subject.BIOLOGY,
            '历史': Subject.HISTORY,
            '地理': Subject.GEOGRAPHY,
            '政治': Subject.POLITICS
        }
        
        grade_map = {
            'grade1': GradeLevel.GRADE_1,
            'grade2': GradeLevel.GRADE_2,
            'grade3': GradeLevel.GRADE_3,
            'grade4': GradeLevel.GRADE_4,
            'grade5': GradeLevel.GRADE_5,
            'grade6': GradeLevel.GRADE_6,
            'grade7': GradeLevel.GRADE_7,
            'grade8': GradeLevel.GRADE_8,
            'grade9': GradeLevel.GRADE_9
        }
        
        subject = subject_map.get(subject_code)
        grade = grade_map.get(grade_code)
        
        if not subject or not grade:
            return jsonify({'success': False, 'error': '无效的科目或年级代码'}), 400
        
        system = NineYearUpgradeSystem()
        exam_id = system.create_exam_record(user_id, exam_type, subject, grade)
        
        if exam_id:
            return jsonify({
                'success': True,
                'message': '考试创建成功',
                'exam_id': exam_id
            })
        else:
            return jsonify({'success': False, 'error': '考试已存在'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/exam/start', methods=['POST'])
def start_exam():
    """开始考试"""
    try:
        data = request.get_json()
        exam_id = data.get('exam_id')
        
        if not exam_id:
            return jsonify({'success': False, 'error': '缺少考试ID'}), 400
        
        system = NineYearUpgradeSystem()
        result, message = system.start_exam(exam_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/exam/pause-request', methods=['POST'])
def pause_exam_request():
    """申请暂停考试"""
    try:
        data = request.get_json()
        exam_id = data.get('exam_id')
        user_id = data.get('user_id')
        reason = data.get('reason')
        
        if not all([exam_id, user_id, reason]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        system = NineYearUpgradeSystem()
        result, message, request_id = system.pause_exam_request(exam_id, user_id, reason)
        
        if result:
            return jsonify({
                'success': True,
                'message': message,
                'request_id': request_id
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/exam/pause-approve', methods=['POST'])
@require_permission(60)
def approve_pause():
    """审批暂停申请（教师权限）"""
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        approved = data.get('approved', False)
        teacher_id = data.get('teacher_id', 'system')
        comment = data.get('comment', '')
        
        if not request_id:
            return jsonify({'success': False, 'error': '缺少申请ID'}), 400
        
        system = NineYearUpgradeSystem()
        result, message = system.approve_pause_request(request_id, teacher_id, approved, comment)
        
        if result:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/exam/submit', methods=['POST'])
def submit_exam():
    """提交考试成绩"""
    try:
        data = request.get_json()
        exam_id = data.get('exam_id')
        score = data.get('score')
        
        if exam_id is None or score is None:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        system = NineYearUpgradeSystem()
        result, message = system.submit_exam(exam_id, score)
        
        if result:
            return jsonify({
                'success': True,
                'message': message,
                'status': 'passed' if '及格' in message else 'failed'
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 升级管理 ====================

@nine_year_bp.route('/upgrade-check/<user_id>', methods=['GET'])
def check_upgrade_eligibility(user_id):
    """检查升级资格"""
    try:
        system = NineYearUpgradeSystem()
        eligibility = system.check_upgrade_eligibility(user_id)
        
        return jsonify({
            'success': True,
            'data': eligibility
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/upgrade', methods=['POST'])
def perform_upgrade():
    """执行升级"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        upgrade_type = data.get('upgrade_type', 'normal')
        operator_id = data.get('operator_id', 'system')
        reason = data.get('reason', '')
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        system = NineYearUpgradeSystem()
        result, message = system.perform_upgrade(user_id, upgrade_type, operator_id, reason)
        
        if result:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/force-repeat', methods=['POST'])
@require_permission(80)
def force_repeat():
    """强制留级（管理员权限）"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        operator_id = data.get('operator_id', 'system')
        reason = data.get('reason', '')
        
        if not user_id:
            return jsonify({'success': False, 'error': '缺少用户ID'}), 400
        
        system = NineYearUpgradeSystem()
        result, message = system.force_repeat(user_id, operator_id, reason)
        
        if result:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 教师管理接口 ====================

@nine_year_bp.route('/teacher/pause-requests', methods=['GET'])
@require_permission(60)
def get_pending_pause_requests():
    """获取待审批的暂停申请（教师权限）"""
    try:
        teacher_id = request.args.get('teacher_id', 'system')
        system = NineYearUpgradeSystem()
        requests = system.get_pending_pause_requests(teacher_id)
        
        return jsonify({
            'success': True,
            'data': requests
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@nine_year_bp.route('/teacher/students', methods=['GET'])
@require_permission(60)
def get_teacher_students():
    """获取学生列表（教师权限）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT g.*, 
                   (SELECT COUNT(*) FROM nine_year_exams WHERE user_id = g.user_id AND status = 'passed') as passed_exams,
                   (SELECT COUNT(*) FROM nine_year_exams WHERE user_id = g.user_id AND status = 'failed') as failed_exams
            FROM nine_year_grades g
            ORDER BY g.current_grade, g.user_id
        ''')
        students = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': [dict(s) for s in students]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 统计报告 ====================

@nine_year_bp.route('/report', methods=['GET'])
@require_permission(80)
def get_upgrade_report():
    """获取升级报告（管理员权限）"""
    try:
        system = NineYearUpgradeSystem()
        report = system.get_upgrade_report()
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 年级信息 ====================

@nine_year_bp.route('/grades/info', methods=['GET'])
def get_grades_info():
    """获取所有年级信息"""
    grade_names = {
        'grade1': '小学1年级',
        'grade2': '小学2年级',
        'grade3': '小学3年级',
        'grade4': '小学4年级',
        'grade5': '小学5年级',
        'grade6': '小学6年级',
        'grade7': '初中1年级',
        'grade8': '初中2年级',
        'grade9': '初中3年级'
    }
    
    return jsonify({
        'success': True,
        'data': grade_names
    })


# ==================== 日志记录 ====================

@nine_year_bp.route('/log', methods=['POST'])
def log_operation():
    """记录操作日志"""
    try:
        data = request.get_json()
        
        # 这里可以扩展为写入专门的日志表
        print('Operation Log:', data)
        
        return jsonify({
            'success': True,
            'message': '日志已记录'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# 注册蓝图
app.register_blueprint(nine_year_bp)


# 添加首页路由
@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>MTSCOS 9年制升级系统 API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
                ul { line-height: 1.8; }
                code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>� MTSCOS 9年制学生升级管理系统 API</h1>
            <p>版本: 1.1 | 完整9年制体系: 小学1年级至初中3年级</p>
            
            <h2>📋 API 接口</h2>
            <ul>
                <li><code>GET /api/nine-year/health</code> - 健康检查</li>
                <li><code>POST /api/nine-year/register</code> - 注册学生年级</li>
                <li><code>GET /api/nine-year/status/&lt;user_id&gt;</code> - 获取学生状态</li>
                <li><code>POST /api/nine-year/confirm/&lt;user_id&gt;</code> - 确认年级</li>
                <li><code>POST /api/nine-year/exam/create</code> - 创建考试</li>
                <li><code>POST /api/nine-year/exam/start</code> - 开始考试</li>
                <li><code>POST /api/nine-year/exam/pause-request</code> - 申请暂停考试</li>
                <li><code>POST /api/nine-year/exam/pause-approve</code> - 审批暂停申请</li>
                <li><code>POST /api/nine-year/exam/submit</code> - 提交考试</li>
                <li><code>GET /api/nine-year/upgrade-check/&lt;user_id&gt;</code> - 检查升级资格</li>
                <li><code>POST /api/nine-year/upgrade</code> - 执行升级</li>
                <li><code>POST /api/nine-year/force-repeat</code> - 强制留级</li>
                <li><code>GET /api/nine-year/teacher/pause-requests</code> - 获取待审批申请</li>
                <li><code>GET /api/nine-year/teacher/students</code> - 获取学生列表</li>
                <li><code>GET /api/nine-year/report</code> - 获取升级报告</li>
                <li><code>GET /api/nine-year/grades/info</code> - 获取年级信息</li>
            </ul>
            
            <h2>📚 年级体系</h2>
            <ul>
                <li>小学阶段: 1-6年级</li>
                <li>初中阶段: 7-9年级</li>
                <li>入口: 小学1年级</li>
                <li>出口: 初中3年级</li>
            </ul>
        </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 80)
    print("MTSCOS 9年制学生升级管理系统 API (v1.1)")
    print("=" * 80)
    print("📚 完整9年制体系: 小学1年级至初中3年级")
    print("🚀 API服务地址: http://0.0.0.0:5002")
    print("=" * 80)
    
    # 初始化数据库
    try:
        system = NineYearUpgradeSystem()
        system.init_database()
    except Exception as e:
        print(f"⚠️  数据库初始化警告: {e}")
    
    app.run(host='0.0.0.0', port=5002, debug=True)

# END

