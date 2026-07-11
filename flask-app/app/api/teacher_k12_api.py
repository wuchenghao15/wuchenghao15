# -*- coding: utf-8 -*-
"""
K12教育教师端API
教师布置作业、批改作业、查看班级报告、管理学生等功能
"""

from flask import Blueprint, jsonify, request, session
from functools import wraps
import logging
import sqlite3
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

teacher_k12_api = Blueprint('teacher_k12_api', __name__, url_prefix='/api/teacher')

# 数据库路径
DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

# ==================== 权限装饰器 ====================

def require_teacher_role(f):
    """教师角色验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role', '')
        if role != 'teacher':
            logger.warning(f"[教师端] 用户 {session.get('username')} ({role}) 无教师权限")
            return jsonify({'success': False, 'error': '此功能仅限教师使用', 'code': 'TEACHER_ONLY'}), 403
        return f(*args, **kwargs)
    return decorated_function


def require_login(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '请先登录', 'code': 'NOT_LOGGED_IN'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== 初始化教师端数据库表 ====================

def _init_teacher_k12_tables():
    """初始化教师端K12相关数据库表"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 教师班级管理表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                grade TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 班级学生表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                join_date TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                UNIQUE(class_id, student_id)
            )
        ''')
        
        # 作业布置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_homeworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                homework_type TEXT DEFAULT 'practice',
                difficulty TEXT DEFAULT 'medium',
                deadline TEXT NOT NULL,
                total_score INTEGER DEFAULT 100,
                questions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # 学生作业提交表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_homework_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homework_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                answers TEXT,
                score REAL DEFAULT 0,
                teacher_comment TEXT,
                is_graded INTEGER DEFAULT 0,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                graded_at TEXT,
                UNIQUE(homework_id, student_id)
            )
        ''')
        
        # 班级考试记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                exam_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                exam_type TEXT DEFAULT 'unit',
                total_score INTEGER DEFAULT 100,
                duration INTEGER DEFAULT 60,
                exam_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 学生考试成绩表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_exam_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_record_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                score REAL DEFAULT 0,
                rank INTEGER,
                analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(exam_record_id, student_id)
            )
        ''')
        
        # 教师评价记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                evaluation_type TEXT NOT NULL,
                content TEXT NOT NULL,
                rating INTEGER DEFAULT 5,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()


# 初始化表
try:
    _init_teacher_k12_tables()
    logger.info("[教师端K12] 数据库表初始化完成")
except Exception as e:
    logger.warning(f"[教师端K12] 数据库表初始化失败: {e}")


# ==================== 班级管理API ====================

@teacher_k12_api.route('/class/create', methods=['POST'])
@require_login
@require_teacher_role
def create_class():
    """创建班级"""
    data = request.get_json() or {}
    
    teacher_id = session.get('user_id')
    class_name = data.get('class_name', '')
    grade = data.get('grade', '')
    subject = data.get('subject', '')
    description = data.get('description', '')
    
    if not class_name or not grade or not subject:
        return jsonify({'success': False, 'error': '请填写班级名称、年级和学科', 'code': 'MISSING_REQUIRED_FIELDS'})
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO teacher_classes
                (teacher_id, class_name, grade, subject, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (teacher_id, class_name, grade, subject, description))
            
            class_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"[教师端] 教师 {session.get('username')} 创建班级: {class_name}")
            
            return jsonify({
                'success': True,
                'message': '班级创建成功',
                'data': {
                    'class_id': class_id,
                    'class_name': class_name,
                    'grade': grade,
                    'subject': subject
                }
            })
    except Exception as e:
        logger.error(f"创建班级失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/classes')
@require_login
@require_teacher_role
def get_teacher_classes():
    """获取教师的班级列表"""
    teacher_id = session.get('user_id')
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, class_name, grade, subject, description, created_at
                FROM teacher_classes WHERE teacher_id = ? AND is_active = 1
                ORDER BY created_at DESC
            ''', (teacher_id,))
            
            classes = []
            for row in cursor.fetchall():
                # 获取班级学生数量
                cursor.execute('SELECT COUNT(*) FROM class_students WHERE class_id = ? AND is_active = 1', (row[0],))
                student_count = cursor.fetchone()[0]
                
                classes.append({
                    'class_id': row[0],
                    'class_name': row[1],
                    'grade': row[2],
                    'subject': row[3],
                    'description': row[4],
                    'student_count': student_count,
                    'created_at': row[5]
                })
            
            return jsonify({'success': True, 'data': classes})
    except Exception as e:
        logger.error(f"获取班级列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/class/<int:class_id>/students', methods=['GET', 'POST'])
@require_login
@require_teacher_role
def manage_class_students(class_id):
    """管理班级学生"""
    teacher_id = session.get('user_id')
    
    # 验证班级归属
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM teacher_classes WHERE id = ? AND teacher_id = ? AND is_active = 1', (class_id, teacher_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '无权限管理该班级', 'code': 'NO_PERMISSION'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    if request.method == 'GET':
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT cs.id, u.id, u.username, u.grade, cs.join_date
                    FROM class_students cs
                    JOIN users u ON cs.student_id = u.id
                    WHERE cs.class_id = ? AND cs.is_active = 1
                    ORDER BY cs.join_date
                ''', (class_id,))
                
                students = []
                for row in cursor.fetchall():
                    # 获取学生学习进度
                    cursor.execute('SELECT AVG(score) FROM k12_learning_progress WHERE user_id = ?', (row[1],))
                    avg_score = cursor.fetchone()[0] or 0
                    
                    students.append({
                        'binding_id': row[0],
                        'student_id': row[1],
                        'username': row[2],
                        'grade': row[3],
                        'join_date': row[4],
                        'avg_score': round(avg_score, 1)
                    })
                
                return jsonify({'success': True, 'data': students})
        except Exception as e:
            logger.error(f"获取班级学生失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        student_ids = data.get('student_ids', [])
        action = data.get('action', 'add')
        
        if not student_ids:
            return jsonify({'success': False, 'error': '请提供学生ID列表', 'code': 'MISSING_STUDENT_IDS'})
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                added_count = 0
                for student_id in student_ids:
                    # 验证学生角色
                    cursor.execute('SELECT role FROM users WHERE id = ?', (student_id,))
                    user = cursor.fetchone()
                    if not user or user[0] not in ['student', 'student_vip']:
                        continue
                    
                    if action == 'add':
                        cursor.execute('''
                            INSERT OR IGNORE INTO class_students (class_id, student_id, is_active)
                            VALUES (?, ?, 1)
                        ''', (class_id, student_id))
                        added_count += 1
                    elif action == 'remove':
                        cursor.execute('UPDATE class_students SET is_active = 0 WHERE class_id = ? AND student_id = ?', (class_id, student_id))
                        added_count += 1
                
                conn.commit()
                
                action_text = '添加' if action == 'add' else '移除'
                return jsonify({
                    'success': True,
                    'message': f'已{action_text}{added_count}名学生',
                    'data': {'count': added_count}
                })
        except Exception as e:
            logger.error(f"管理班级学生失败: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 作业管理API ====================

@teacher_k12_api.route('/homework/create', methods=['POST'])
@require_login
@require_teacher_role
def create_homework():
    """布置作业"""
    data = request.get_json() or {}
    
    teacher_id = session.get('user_id')
    class_id = data.get('class_id')
    subject = data.get('subject', '')
    title = data.get('title', '')
    description = data.get('description', '')
    homework_type = data.get('homework_type', 'practice')
    difficulty = data.get('difficulty', 'medium')
    deadline = data.get('deadline', '')
    total_score = data.get('total_score', 100)
    questions = data.get('questions', [])
    
    if not class_id or not title or not deadline:
        return jsonify({'success': False, 'error': '请填写班级、作业标题和截止日期', 'code': 'MISSING_REQUIRED_FIELDS'})
    
    # 验证班级归属
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM teacher_classes WHERE id = ? AND teacher_id = ? AND is_active = 1', (class_id, teacher_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '无权限在该班级布置作业', 'code': 'NO_PERMISSION'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO teacher_homeworks
                (teacher_id, class_id, subject, title, description, homework_type, difficulty, deadline, total_score, questions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (teacher_id, class_id, subject, title, description, homework_type, difficulty, deadline, total_score, json.dumps(questions)))
            
            homework_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"[教师端] 教师 {session.get('username')} 布置作业: {title}")
            
            return jsonify({
                'success': True,
                'message': '作业布置成功',
                'data': {
                    'homework_id': homework_id,
                    'title': title,
                    'deadline': deadline
                }
            })
    except Exception as e:
        logger.error(f"布置作业失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/homeworks')
@require_login
@require_teacher_role
def get_teacher_homeworks():
    """获取教师布置的作业列表"""
    teacher_id = session.get('user_id')
    status = request.args.get('status', 'all')
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            if status == 'all':
                cursor.execute('''
                    SELECT h.id, h.title, h.subject, h.homework_type, h.difficulty, h.deadline, h.total_score, h.status, h.created_at,
                           c.class_name, c.grade
                    FROM teacher_homeworks h
                    JOIN teacher_classes c ON h.class_id = c.id
                    WHERE h.teacher_id = ?
                    ORDER BY h.created_at DESC
                ''', (teacher_id,))
            else:
                cursor.execute('''
                    SELECT h.id, h.title, h.subject, h.homework_type, h.difficulty, h.deadline, h.total_score, h.status, h.created_at,
                           c.class_name, c.grade
                    FROM teacher_homeworks h
                    JOIN teacher_classes c ON h.class_id = c.id
                    WHERE h.teacher_id = ? AND h.status = ?
                    ORDER BY h.created_at DESC
                ''', (teacher_id, status))
            
            homeworks = []
            for row in cursor.fetchall():
                # 获取提交统计
                cursor.execute('SELECT COUNT(*) FROM student_homework_submissions WHERE homework_id = ?', (row[0],))
                submitted_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM class_students WHERE class_id = (SELECT class_id FROM teacher_homeworks WHERE id = ?) AND is_active = 1', (row[0],))
                total_count = cursor.fetchone()[0]
                
                homeworks.append({
                    'homework_id': row[0],
                    'title': row[1],
                    'subject': row[2],
                    'type': row[3],
                    'difficulty': row[4],
                    'deadline': row[5],
                    'total_score': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'class_name': row[9],
                    'grade': row[10],
                    'submitted_count': submitted_count,
                    'total_students': total_count,
                    'completion_rate': round(submitted_count / total_count * 100, 1) if total_count > 0 else 0
                })
            
            return jsonify({'success': True, 'data': homeworks})
    except Exception as e:
        logger.error(f"获取作业列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/homework/<int:homework_id>/submissions')
@require_login
@require_teacher_role
def get_homework_submissions(homework_id):
    """获取作业提交列表"""
    teacher_id = session.get('user_id')
    
    # 验证作业归属
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT teacher_id FROM teacher_homeworks WHERE id = ?', (homework_id,))
            hw = cursor.fetchone()
            if not hw or hw[0] != teacher_id:
                return jsonify({'success': False, 'error': '无权限查看该作业', 'code': 'NO_PERMISSION'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.id, s.student_id, u.username, s.answers, s.score, s.teacher_comment, s.is_graded, s.submitted_at
                FROM student_homework_submissions s
                JOIN users u ON s.student_id = u.id
                WHERE s.homework_id = ?
                ORDER BY s.submitted_at DESC
            ''', (homework_id,))
            
            submissions = []
            for row in cursor.fetchall():
                submissions.append({
                    'submission_id': row[0],
                    'student_id': row[1],
                    'student_name': row[2],
                    'answers': json.loads(row[3]) if row[3] else [],
                    'score': row[4],
                    'comment': row[5],
                    'is_graded': row[6],
                    'submitted_at': row[7]
                })
            
            return jsonify({'success': True, 'data': submissions})
    except Exception as e:
        logger.error(f"获取作业提交失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/homework/submission/<int:submission_id>/grade', methods=['POST'])
@require_login
@require_teacher_role
def grade_homework_submission(submission_id):
    """批改作业"""
    teacher_id = session.get('user_id')
    data = request.get_json() or {}
    
    score = data.get('score', 0)
    comment = data.get('comment', '')
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 验证作业归属
            cursor.execute('''
                SELECT h.teacher_id FROM student_homework_submissions s
                JOIN teacher_homeworks h ON s.homework_id = h.id
                WHERE s.id = ?
            ''', (submission_id,))
            result = cursor.fetchone()
            if not result or result[0] != teacher_id:
                return jsonify({'success': False, 'error': '无权限批改该作业', 'code': 'NO_PERMISSION'}), 403
            
            # 更新批改结果
            cursor.execute('''
                UPDATE student_homework_submissions
                SET score = ?, teacher_comment = ?, is_graded = 1, graded_at = datetime("now")
                WHERE id = ?
            ''', (score, comment, submission_id))
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '作业批改完成',
                'data': {
                    'submission_id': submission_id,
                    'score': score,
                    'comment': comment
                }
            })
    except Exception as e:
        logger.error(f"批改作业失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/homework/batch_grade', methods=['POST'])
@require_login
@require_teacher_role
def batch_grade_homework():
    """批量批改作业"""
    teacher_id = session.get('user_id')
    data = request.get_json() or {}
    
    grades = data.get('grades', [])  # [{'submission_id': 1, 'score': 85, 'comment': '...'}, ...]
    
    if not grades:
        return jsonify({'success': False, 'error': '请提供批改数据', 'code': 'MISSING_GRADES'})
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            graded_count = 0
            for grade_data in grades:
                submission_id = grade_data.get('submission_id')
                score = grade_data.get('score', 0)
                comment = grade_data.get('comment', '')
                
                # 验证归属
                cursor.execute('''
                    SELECT h.teacher_id FROM student_homework_submissions s
                    JOIN teacher_homeworks h ON s.homework_id = h.id
                    WHERE s.id = ?
                ''', (submission_id,))
                result = cursor.fetchone()
                if result and result[0] == teacher_id:
                    cursor.execute('''
                        UPDATE student_homework_submissions
                        SET score = ?, teacher_comment = ?, is_graded = 1, graded_at = datetime("now")
                        WHERE id = ?
                    ''', (score, comment, submission_id))
                    graded_count += 1
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'已批改{graded_count}份作业',
                'data': {'graded_count': graded_count}
            })
    except Exception as e:
        logger.error(f"批量批改失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 班级报告API ====================

@teacher_k12_api.route('/class/<int:class_id>/report')
@require_login
@require_teacher_role
def get_class_report(class_id):
    """获取班级学习报告"""
    teacher_id = session.get('user_id')
    
    # 验证班级归属
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, class_name, grade, subject FROM teacher_classes WHERE id = ? AND teacher_id = ? AND is_active = 1', (class_id, teacher_id))
            class_info = cursor.fetchone()
            if not class_info:
                return jsonify({'success': False, 'error': '无权限查看该班级报告', 'code': 'NO_PERMISSION'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取班级学生
            cursor.execute('SELECT student_id FROM class_students WHERE class_id = ? AND is_active = 1', (class_id,))
            student_ids = [row[0] for row in cursor.fetchall()]
            
            if not student_ids:
                return jsonify({'success': True, 'data': {'message': '班级暂无学生'}})
            
            # 统计学习进度
            total_avg_score = 0
            subject_scores = {}
            student_scores = []
            
            for student_id in student_ids:
                cursor.execute('SELECT AVG(score) FROM k12_learning_progress WHERE user_id = ?', (student_id,))
                avg = cursor.fetchone()[0] or 0
                total_avg_score += avg
                student_scores.append(avg)
            
            total_avg_score = round(total_avg_score / len(student_ids), 1) if student_ids else 0
            
            # 按学科统计
            cursor.execute('''
                SELECT subject, AVG(score) 
                FROM k12_learning_progress 
                WHERE user_id IN ({})
                GROUP BY subject
            '''.format(','.join(['?'] * len(student_ids))), student_ids)
            
            for row in cursor.fetchall():
                subject_scores[row[0]] = round(row[1], 1)
            
            # 计算分布
            excellent = sum(1 for s in student_scores if s >= 90)
            good = sum(1 for s in student_scores if s >= 80 and s < 90)
            average = sum(1 for s in student_scores if s >= 60 and s < 80)
            poor = sum(1 for s in student_scores if s < 60)
            
            return jsonify({
                'success': True,
                'data': {
                    'class_info': {
                        'class_id': class_id,
                        'class_name': class_info[1],
                        'grade': class_info[2],
                        'subject': class_info[3],
                        'student_count': len(student_ids)
                    },
                    'overall': {
                        'avg_score': total_avg_score,
                        'excellent_count': excellent,
                        'good_count': good,
                        'average_count': average,
                        'poor_count': poor
                    },
                    'subject_scores': subject_scores,
                    'distribution': {
                        'excellent': round(excellent / len(student_ids) * 100, 1) if student_ids else 0,
                        'good': round(good / len(student_ids) * 100, 1) if student_ids else 0,
                        'average': round(average / len(student_ids) * 100, 1) if student_ids else 0,
                        'poor': round(poor / len(student_ids) * 100, 1) if student_ids else 0
                    }
                }
            })
    except Exception as e:
        logger.error(f"获取班级报告失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/class/<int:class_id>/student_ranking')
@require_login
@require_teacher_role
def get_class_student_ranking(class_id):
    """获取班级学生排名"""
    teacher_id = session.get('user_id')
    
    # 验证班级归属
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM teacher_classes WHERE id = ? AND teacher_id = ? AND is_active = 1', (class_id, teacher_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '无权限查看该班级', 'code': 'NO_PERMISSION'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.grade, AVG(lp.score) as avg_score
                FROM class_students cs
                JOIN users u ON cs.student_id = u.id
                LEFT JOIN k12_learning_progress lp ON u.id = lp.user_id
                WHERE cs.class_id = ? AND cs.is_active = 1
                GROUP BY u.id
                ORDER BY avg_score DESC
            ''', (class_id,))
            
            rankings = []
            rank = 1
            for row in cursor.fetchall():
                rankings.append({
                    'rank': rank,
                    'student_id': row[0],
                    'username': row[1],
                    'grade': row[2],
                    'avg_score': round(row[3], 1) if row[3] else 0
                })
                rank += 1
            
            return jsonify({'success': True, 'data': rankings})
    except Exception as e:
        logger.error(f"获取学生排名失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/class/<int:class_id>/weak_points')
@require_login
@require_teacher_role
def get_class_weak_points(class_id):
    """获取班级整体薄弱知识点"""
    teacher_id = session.get('user_id')
    
    # 验证班级归属
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM teacher_classes WHERE id = ? AND teacher_id = ? AND is_active = 1', (class_id, teacher_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '无权限查看该班级', 'code': 'NO_PERMISSION'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取班级学生
            cursor.execute('SELECT student_id FROM class_students WHERE class_id = ? AND is_active = 1', (class_id,))
            student_ids = [row[0] for row in cursor.fetchall()]
            
            if not student_ids:
                return jsonify({'success': True, 'data': {'weak_points': []}})
            
            # 统计薄弱知识点
            cursor.execute('''
                SELECT subject, chapter, AVG(score) as avg_score, COUNT(*) as count
                FROM k12_learning_progress 
                WHERE user_id IN ({}) AND score < 80
                GROUP BY subject, chapter
                ORDER BY avg_score ASC
            '''.format(','.join(['?'] * len(student_ids))), student_ids)
            
            weak_points = []
            for row in cursor.fetchall():
                weak_points.append({
                    'subject': row[0],
                    'chapter': row[1],
                    'avg_score': round(row[2], 1),
                    'affected_students': row[3],
                    'severity': 'high' if row[2] < 60 else 'medium'
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'weak_points': weak_points,
                    'recommendations': [
                        {'subject': wp['subject'], 'chapter': wp['chapter'], 'action': '建议进行专题讲解和练习'}
                        for wp in weak_points[:5]
                    ]
                }
            })
    except Exception as e:
        logger.error(f"获取班级薄弱点失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 学生评价API ====================

@teacher_k12_api.route('/student/<int:student_id>/evaluate', methods=['POST'])
@require_login
@require_teacher_role
def evaluate_student(student_id):
    """评价学生"""
    data = request.get_json() or {}
    
    teacher_id = session.get('user_id')
    class_id = data.get('class_id')
    evaluation_type = data.get('evaluation_type', 'general')
    content = data.get('content', '')
    rating = data.get('rating', 5)
    
    if not content:
        return jsonify({'success': False, 'error': '请填写评价内容', 'code': 'MISSING_CONTENT'})
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO teacher_evaluations
                (teacher_id, student_id, class_id, evaluation_type, content, rating)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (teacher_id, student_id, class_id, evaluation_type, content, rating))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '学生评价已保存'
            })
    except Exception as e:
        logger.error(f"评价学生失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@teacher_k12_api.route('/student/<int:student_id>/evaluations')
@require_login
@require_teacher_role
def get_student_evaluations(student_id):
    """获取学生评价记录"""
    teacher_id = session.get('user_id')
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, class_id, evaluation_type, content, rating, created_at
                FROM teacher_evaluations WHERE teacher_id = ? AND student_id = ?
                ORDER BY created_at DESC
            ''', (teacher_id, student_id))
            
            evaluations = []
            for row in cursor.fetchall():
                evaluations.append({
                    'id': row[0],
                    'class_id': row[1],
                    'type': row[2],
                    'content': row[3],
                    'rating': row[4],
                    'created_at': row[5]
                })
            
            return jsonify({'success': True, 'data': evaluations})
    except Exception as e:
        logger.error(f"获取学生评价失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 教师工作概览API ====================

@teacher_k12_api.route('/overview')
@require_login
@require_teacher_role
def get_teacher_overview():
    """获取教师工作概览"""
    teacher_id = session.get('user_id')
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 统计班级数量
            cursor.execute('SELECT COUNT(*) FROM teacher_classes WHERE teacher_id = ? AND is_active = 1', (teacher_id,))
            class_count = cursor.fetchone()[0]
            
            # 统计学生数量
            cursor.execute('''
                SELECT COUNT(DISTINCT cs.student_id)
                FROM class_students cs
                JOIN teacher_classes tc ON cs.class_id = tc.id
                WHERE tc.teacher_id = ? AND cs.is_active = 1
            ''', (teacher_id,))
            student_count = cursor.fetchone()[0]
            
            # 统计作业数量
            cursor.execute('SELECT COUNT(*) FROM teacher_homeworks WHERE teacher_id = ? AND status = "active"', (teacher_id,))
            active_homework_count = cursor.fetchone()[0]
            
            # 统计待批改作业
            cursor.execute('''
                SELECT COUNT(*) 
                FROM student_homework_submissions s
                JOIN teacher_homeworks h ON s.homework_id = h.id
                WHERE h.teacher_id = ? AND s.is_graded = 0
            ''', (teacher_id,))
            pending_grade_count = cursor.fetchone()[0]
            
            # 最近活动
            cursor.execute('''
                SELECT h.title, h.deadline, c.class_name
                FROM teacher_homeworks h
                JOIN teacher_classes c ON h.class_id = c.id
                WHERE h.teacher_id = ? AND h.status = "active"
                ORDER BY h.deadline ASC
                LIMIT 5
            ''', (teacher_id,))
            
            upcoming_homeworks = []
            for row in cursor.fetchall():
                upcoming_homeworks.append({
                    'title': row[0],
                    'deadline': row[1],
                    'class_name': row[2]
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'class_count': class_count,
                    'student_count': student_count,
                    'active_homework_count': active_homework_count,
                    'pending_grade_count': pending_grade_count,
                    'upcoming_homeworks': upcoming_homeworks
                }
            })
    except Exception as e:
        logger.error(f"获取教师概览失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500