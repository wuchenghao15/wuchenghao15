# -*- coding: utf-8 -*-
"""
K12教育家长端API
家长监控孩子学习进度、查看学习报告、设置学习提醒等功能
"""

from flask import Blueprint, jsonify, request, session
from functools import wraps
import logging
import sqlite3
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

parent_api = Blueprint('parent_api', __name__, url_prefix='/api/parent')

# 数据库路径
DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

# ==================== 权限装饰器 ====================

def require_parent_role(f):
    """家长角色验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role', '')
        if role != 'parent':
            logger.warning(f"[家长端] 用户 {session.get('username')} ({role}) 无家长权限")
            return jsonify({'success': False, 'error': '此功能仅限家长使用', 'code': 'PARENT_ONLY'}), 403
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


# ==================== 家长-学生绑定管理 ====================

def _init_parent_tables():
    """初始化家长端相关数据库表"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 家长-学生绑定表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parent_student_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                relation_type TEXT DEFAULT 'parent',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                approved_at TEXT,
                UNIQUE(parent_id, student_id)
            )
        ''')
        
        # 家长监控设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parent_monitor_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                daily_report_enabled INTEGER DEFAULT 1,
                weekly_report_enabled INTEGER DEFAULT 1,
                exam_reminder_enabled INTEGER DEFAULT 1,
                homework_reminder_enabled INTEGER DEFAULT 1,
                study_time_limit INTEGER DEFAULT 120,
                rest_reminder_interval INTEGER DEFAULT 45,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(parent_id, student_id)
            )
        ''')
        
        # 家长通知记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()


# 初始化表
try:
    _init_parent_tables()
    logger.info("[家长端] 数据库表初始化完成")
except Exception as e:
    logger.warning(f"[家长端] 数据库表初始化失败: {e}")


# ==================== 家长-学生绑定API ====================

@parent_api.route('/bind_student', methods=['POST'])
@require_login
@require_parent_role
def bind_student():
    """绑定学生账号"""
    data = request.get_json() or {}
    
    parent_id = session.get('user_id')
    student_username = data.get('student_username', '')
    relation_type = data.get('relation_type', 'parent')
    
    if not student_username:
        return jsonify({'success': False, 'error': '请提供学生用户名', 'code': 'MISSING_STUDENT_USERNAME'})
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 查找学生用户
            cursor.execute('SELECT id, username, role, grade FROM users WHERE username = ?', (student_username,))
            student = cursor.fetchone()
            
            if not student:
                return jsonify({'success': False, 'error': '学生账号不存在', 'code': 'STUDENT_NOT_FOUND'})
            
            student_id = student[0]
            student_role = student[2]
            
            # 验证学生角色
            if student_role not in ['student', 'student_vip']:
                return jsonify({'success': False, 'error': '该用户不是学生角色', 'code': 'NOT_STUDENT_ROLE'})
            
            # 检查是否已绑定
            cursor.execute('SELECT id, is_active FROM parent_student_bindings WHERE parent_id = ? AND student_id = ?', (parent_id, student_id))
            existing = cursor.fetchone()
            
            if existing:
                if existing[1] == 1:
                    return jsonify({'success': False, 'error': '已绑定该学生', 'code': 'ALREADY_BOUND'})
                else:
                    # 重新激活绑定
                    cursor.execute('UPDATE parent_student_bindings SET is_active = 1, approved_at = datetime("now") WHERE id = ?', (existing[0],))
                    conn.commit()
                    return jsonify({'success': True, 'message': '绑定已重新激活'})
            
            # 创建新绑定
            cursor.execute('''
                INSERT INTO parent_student_bindings 
                (parent_id, student_id, relation_type, is_active, approved_at)
                VALUES (?, ?, ?, 1, datetime("now"))
            ''', (parent_id, student_id, relation_type))
            
            # 创建默认监控设置
            cursor.execute('''
                INSERT INTO parent_monitor_settings 
                (parent_id, student_id)
                VALUES (?, ?)
            ''', (parent_id, student_id))
            
            conn.commit()
            
            logger.info(f"[家长端] 家长 {session.get('username')} 绑定学生 {student_username}")
            
            return jsonify({
                'success': True,
                'message': '绑定成功',
                'data': {
                    'student_id': student_id,
                    'student_username': student_username,
                    'student_grade': student[3],
                    'relation_type': relation_type
                }
            })
    except Exception as e:
        logger.error(f"绑定学生失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@parent_api.route('/unbind_student', methods=['POST'])
@require_login
@require_parent_role
def unbind_student():
    """解除绑定学生账号"""
    data = request.get_json() or {}
    
    parent_id = session.get('user_id')
    student_id = data.get('student_id')
    
    if not student_id:
        return jsonify({'success': False, 'error': '请提供学生ID', 'code': 'MISSING_STUDENT_ID'})
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('UPDATE parent_student_bindings SET is_active = 0 WHERE parent_id = ? AND student_id = ?', (parent_id, student_id))
            conn.commit()
            
            return jsonify({'success': True, 'message': '已解除绑定'})
    except Exception as e:
        logger.error(f"解除绑定失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@parent_api.route('/bound_students')
@require_login
@require_parent_role
def get_bound_students():
    """获取已绑定的学生列表"""
    parent_id = session.get('user_id')
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT b.student_id, u.username, u.grade, b.relation_type, b.created_at,
                       m.daily_report_enabled, m.weekly_report_enabled
                FROM parent_student_bindings b
                JOIN users u ON b.student_id = u.id
                JOIN parent_monitor_settings m ON b.parent_id = m.parent_id AND b.student_id = m.student_id
                WHERE b.parent_id = ? AND b.is_active = 1
            ''', (parent_id,))
            
            students = []
            for row in cursor.fetchall():
                students.append({
                    'student_id': row[0],
                    'username': row[1],
                    'grade': row[2],
                    'relation_type': row[3],
                    'bound_at': row[4],
                    'monitor_settings': {
                        'daily_report': row[5],
                        'weekly_report': row[6]
                    }
                })
            
            return jsonify({'success': True, 'data': students})
    except Exception as e:
        logger.error(f"获取绑定学生失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 学习进度监控API ====================

@parent_api.route('/student/<int:student_id>/progress')
@require_login
@require_parent_role
def get_student_progress(student_id):
    """获取学生学习进度"""
    parent_id = session.get('user_id')
    
    # 验证绑定关系
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM parent_student_bindings WHERE parent_id = ? AND student_id = ? AND is_active = 1', (parent_id, student_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '未绑定该学生', 'code': 'NOT_BOUND'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取学生基本信息
            cursor.execute('SELECT username, grade FROM users WHERE id = ?', (student_id,))
            student_info = cursor.fetchone()
            
            # 获取学习进度
            cursor.execute('''
                SELECT subject, chapter, progress, score, updated_at
                FROM k12_learning_progress WHERE user_id = ?
            ''', (student_id,))
            
            progress_data = []
            for row in cursor.fetchall():
                progress_data.append({
                    'subject': row[0],
                    'chapter': row[1],
                    'progress': row[2],
                    'score': row[3],
                    'updated_at': row[4]
                })
            
            # 获取考试记录
            cursor.execute('''
                SELECT exam_name, subject, score, total_score, completed_at
                FROM k12_exam_records WHERE student_id = ?
                ORDER BY completed_at DESC LIMIT 10
            ''', (student_id,))
            
            exam_records = []
            for row in cursor.fetchall():
                exam_records.append({
                    'exam_name': row[0],
                    'subject': row[1],
                    'score': row[2],
                    'total_score': row[3],
                    'completed_at': row[4],
                    'percentage': round(row[2] / row[3] * 100, 1) if row[3] > 0 else 0
                })
            
            # 计算总体数据
            avg_score = 0
            if progress_data:
                avg_score = round(sum(p['score'] for p in progress_data) / len(progress_data), 1)
            
            return jsonify({
                'success': True,
                'data': {
                    'student_info': {
                        'id': student_id,
                        'username': student_info[0] if student_info else '',
                        'grade': student_info[1] if student_info else ''
                    },
                    'progress': progress_data,
                    'exam_records': exam_records,
                    'summary': {
                        'total_subjects': len(progress_data),
                        'avg_score': avg_score,
                        'recent_exams': len(exam_records)
                    }
                }
            })
    except Exception as e:
        logger.error(f"获取学生学习进度失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@parent_api.route('/student/<int:student_id>/daily_report')
@require_login
@require_parent_role
def get_student_daily_report(student_id):
    """获取学生每日学习报告"""
    parent_id = session.get('user_id')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # 验证绑定关系
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM parent_student_bindings WHERE parent_id = ? AND student_id = ? AND is_active = 1', (parent_id, student_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '未绑定该学生', 'code': 'NOT_BOUND'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取当日学习记录
            cursor.execute('''
                SELECT subject, chapter, study_duration, questions_done, correct_count, wrong_count
                FROM k12_daily_study_records
                WHERE student_id = ? AND date = ?
            ''', (student_id, date))
            
            daily_records = []
            total_study_time = 0
            total_questions = 0
            total_correct = 0
            
            for row in cursor.fetchall():
                daily_records.append({
                    'subject': row[0],
                    'chapter': row[1],
                    'study_duration': row[2],
                    'questions_done': row[3],
                    'correct_count': row[4],
                    'wrong_count': row[5],
                    'accuracy': round(row[4] / row[3] * 100, 1) if row[3] > 0 else 0
                })
                total_study_time += row[2] or 0
                total_questions += row[3] or 0
                total_correct += row[4] or 0
            
            return jsonify({
                'success': True,
                'data': {
                    'date': date,
                    'student_id': student_id,
                    'daily_records': daily_records,
                    'summary': {
                        'total_study_time_minutes': total_study_time,
                        'total_questions': total_questions,
                        'total_correct': total_correct,
                        'overall_accuracy': round(total_correct / total_questions * 100, 1) if total_questions > 0 else 0
                    }
                }
            })
    except Exception as e:
        logger.error(f"获取每日学习报告失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@parent_api.route('/student/<int:student_id>/weekly_report')
@require_login
@require_parent_role
def get_student_weekly_report(student_id):
    """获取学生每周学习报告"""
    parent_id = session.get('user_id')
    
    # 验证绑定关系
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM parent_student_bindings WHERE parent_id = ? AND student_id = ? AND is_active = 1', (parent_id, student_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '未绑定该学生', 'code': 'NOT_BOUND'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 获取最近7天的学习数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            cursor.execute('''
                SELECT date, SUM(study_duration), SUM(questions_done), SUM(correct_count)
                FROM k12_daily_study_records
                WHERE student_id = ? AND date >= ? AND date <= ?
                GROUP BY date
                ORDER BY date
            ''', (student_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            daily_summary = []
            total_time = 0
            total_questions = 0
            total_correct = 0
            
            for row in cursor.fetchall():
                daily_summary.append({
                    'date': row[0],
                    'study_time': row[1],
                    'questions': row[2],
                    'correct': row[3]
                })
                total_time += row[1] or 0
                total_questions += row[2] or 0
                total_correct += row[3] or 0
            
            # 获取学科分布
            cursor.execute('''
                SELECT subject, SUM(study_duration), SUM(questions_done)
                FROM k12_daily_study_records
                WHERE student_id = ? AND date >= ? AND date <= ?
                GROUP BY subject
            ''', (student_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            
            subject_distribution = []
            for row in cursor.fetchall():
                subject_distribution.append({
                    'subject': row[0],
                    'study_time': row[1],
                    'questions': row[2],
                    'percentage': round(row[1] / total_time * 100, 1) if total_time > 0 else 0
                })
            
            return jsonify({
                'success': True,
                'data': {
                    'student_id': student_id,
                    'week_range': {
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d')
                    },
                    'daily_summary': daily_summary,
                    'subject_distribution': subject_distribution,
                    'weekly_summary': {
                        'total_study_time_minutes': total_time,
                        'total_questions': total_questions,
                        'total_correct': total_correct,
                        'overall_accuracy': round(total_correct / total_questions * 100, 1) if total_questions > 0 else 0,
                        'avg_daily_time': round(total_time / 7, 1),
                        'study_days': len(daily_summary)
                    }
                }
            })
    except Exception as e:
        logger.error(f"获取每周学习报告失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 监控设置API ====================

@parent_api.route('/monitor_settings/<int:student_id>', methods=['GET', 'POST'])
@require_login
@require_parent_role
def monitor_settings(student_id):
    """获取或设置监控配置"""
    parent_id = session.get('user_id')
    
    # 验证绑定关系
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM parent_student_bindings WHERE parent_id = ? AND student_id = ? AND is_active = 1', (parent_id, student_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '未绑定该学生', 'code': 'NOT_BOUND'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    if request.method == 'GET':
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT daily_report_enabled, weekly_report_enabled, exam_reminder_enabled,
                           homework_reminder_enabled, study_time_limit, rest_reminder_interval
                    FROM parent_monitor_settings WHERE parent_id = ? AND student_id = ?
                ''', (parent_id, student_id))
                
                settings = cursor.fetchone()
                
                if settings:
                    return jsonify({
                        'success': True,
                        'data': {
                            'daily_report_enabled': settings[0],
                            'weekly_report_enabled': settings[1],
                            'exam_reminder_enabled': settings[2],
                            'homework_reminder_enabled': settings[3],
                            'study_time_limit': settings[4],
                            'rest_reminder_interval': settings[5]
                        }
                    })
                else:
                    return jsonify({'success': True, 'data': {
                        'daily_report_enabled': 1,
                        'weekly_report_enabled': 1,
                        'exam_reminder_enabled': 1,
                        'homework_reminder_enabled': 1,
                        'study_time_limit': 120,
                        'rest_reminder_interval': 45
                    }})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO parent_monitor_settings
                    (parent_id, student_id, daily_report_enabled, weekly_report_enabled,
                     exam_reminder_enabled, homework_reminder_enabled, study_time_limit,
                     rest_reminder_interval, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime("now"))
                ''', (
                    parent_id, student_id,
                    data.get('daily_report_enabled', 1),
                    data.get('weekly_report_enabled', 1),
                    data.get('exam_reminder_enabled', 1),
                    data.get('homework_reminder_enabled', 1),
                    data.get('study_time_limit', 120),
                    data.get('rest_reminder_interval', 45)
                ))
                conn.commit()
                
                return jsonify({'success': True, 'message': '监控设置已更新'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 通知管理API ====================

@parent_api.route('/notifications')
@require_login
@require_parent_role
def get_notifications():
    """获取家长通知列表"""
    parent_id = session.get('user_id')
    unread_only = request.args.get('unread_only', 'false') == 'true'
    limit = int(request.args.get('limit', 20))
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            if unread_only:
                cursor.execute('''
                    SELECT id, student_id, notification_type, title, content, is_read, created_at
                    FROM parent_notifications WHERE parent_id = ? AND is_read = 0
                    ORDER BY created_at DESC LIMIT ?
                ''', (parent_id, limit))
            else:
                cursor.execute('''
                    SELECT id, student_id, notification_type, title, content, is_read, created_at
                    FROM parent_notifications WHERE parent_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (parent_id, limit))
            
            notifications = []
            for row in cursor.fetchall():
                # 获取学生用户名
                cursor.execute('SELECT username FROM users WHERE id = ?', (row[1],))
                student_name = cursor.fetchone()
                
                notifications.append({
                    'id': row[0],
                    'student_id': row[1],
                    'student_name': student_name[0] if student_name else '',
                    'type': row[2],
                    'title': row[3],
                    'content': row[4],
                    'is_read': row[5],
                    'created_at': row[6]
                })
            
            return jsonify({'success': True, 'data': notifications})
    except Exception as e:
        logger.error(f"获取通知失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@parent_api.route('/notification/<int:notification_id>/read', methods=['POST'])
@require_login
@require_parent_role
def mark_notification_read(notification_id):
    """标记通知为已读"""
    parent_id = session.get('user_id')
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE parent_notifications SET is_read = 1 WHERE id = ? AND parent_id = ?', (notification_id, parent_id))
            conn.commit()
            
            return jsonify({'success': True, 'message': '通知已标记为已读'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 学习建议API ====================

@parent_api.route('/student/<int:student_id>/suggestions')
@require_login
@require_parent_role
def get_study_suggestions(student_id):
    """获取学生学习建议"""
    parent_id = session.get('user_id')
    
    # 验证绑定关系
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM parent_student_bindings WHERE parent_id = ? AND student_id = ? AND is_active = 1', (parent_id, student_id))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': '未绑定该学生', 'code': 'NOT_BOUND'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 分析薄弱点
            cursor.execute('''
                SELECT subject, chapter, score
                FROM k12_learning_progress WHERE user_id = ? AND score < 80
                ORDER BY score ASC
            ''', (student_id,))
            
            weak_points = []
            for row in cursor.fetchall():
                weak_points.append({
                    'subject': row[0],
                    'chapter': row[1],
                    'score': row[2]
                })
            
            suggestions = []
            
            # 生成建议
            for wp in weak_points[:5]:
                suggestions.append({
                    'type': 'weak_point',
                    'priority': 'high' if wp['score'] < 60 else 'medium',
                    'subject': wp['subject'],
                    'chapter': wp['chapter'],
                    'suggestion': f"建议加强{wp['subject']}学科{wp['chapter']}的学习，当前得分{wp['score']}分"
                })
            
            # 添加一般性建议
            suggestions.append({
                'type': 'general',
                'priority': 'low',
                'suggestion': '建议保持每日规律的学习节奏，劳逸结合'
            })
            
            suggestions.append({
                'type': 'general',
                'priority': 'low',
                'suggestion': '建议每周进行一次知识总结复习'
            })
            
            return jsonify({
                'success': True,
                'data': {
                    'student_id': student_id,
                    'weak_points_count': len(weak_points),
                    'suggestions': suggestions
                }
            })
    except Exception as e:
        logger.error(f"获取学习建议失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500