# -*- coding: utf-8 -*-
"""
学生分析API - 成绩分析、学习行为分析、薄弱知识点分析
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login
import sqlite3
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

student_analytics_api = Blueprint('student_analytics_api', __name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_response(code=200, message='success', data=None):
    return jsonify({
        'code': code,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })


def get_time_range_dates(time_range):
    now = datetime.now()
    if time_range == 'week':
        start_date = (now - timedelta(days=7)).date().isoformat()
    elif time_range == 'month':
        start_date = (now - timedelta(days=30)).date().isoformat()
    elif time_range == 'quarter':
        start_date = (now - timedelta(days=90)).date().isoformat()
    elif time_range == 'year':
        start_date = (now - timedelta(days=365)).date().isoformat()
    else:
        start_date = (now - timedelta(days=30)).date().isoformat()
    end_date = now.date().isoformat()
    return start_date, end_date


def has_access():
    role = session.get('role')
    return role in ['admin', 'super_admin', 'teacher']


def fetch_analytics_stats(subject='', cls='', time_range='month'):
    """获取分析统计数据 - 返回原始字典"""
    stats = {
        'total_students': 0,
        'active_students': 0,
        'avg_score': 0,
        'total_exams': 0,
        'pass_rate': 0,
        'fail_rate': 0,
        'avg_study_time': 0,
        'recent_activities': 0
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('student',))
        row = cursor.fetchone()
        if row:
            stats['total_students'] = row[0] or 0

        cursor.execute('SELECT COUNT(*) FROM users WHERE role = ? AND is_active = 1', ('student',))
        row = cursor.fetchone()
        if row:
            stats['active_students'] = row[0] or 0

        query = '''
            SELECT AVG(er.score) as avg_score,
                   COUNT(*) as total_exams,
                   SUM(CASE WHEN er.score >= 60 THEN 1 ELSE 0 END) as passed_count,
                   SUM(CASE WHEN er.score < 60 THEN 1 ELSE 0 END) as failed_count
            FROM exam_results er
            WHERE er.status = 'completed'
        '''
        params = []
        if subject:
            query += ' AND er.subject = ?'
            params.append(subject)

        cursor.execute(query, params)
        row = cursor.fetchone()
        if row and row['total_exams'] and row['total_exams'] > 0:
            stats['avg_score'] = round(row['avg_score'] or 0, 1)
            stats['total_exams'] = row['total_exams']
            stats['pass_rate'] = round((row['passed_count'] / row['total_exams']) * 100, 1)
            stats['fail_rate'] = round((row['failed_count'] / row['total_exams']) * 100, 1)

        cursor.execute('SELECT AVG(duration) as avg_duration FROM learning_records WHERE activity_type = ?', ('study',))
        row = cursor.fetchone()
        if row:
            stats['avg_study_time'] = round(row['avg_duration'] or 0, 0)

        start_date, end_date = get_time_range_dates(time_range)
        cursor.execute('SELECT COUNT(*) FROM learning_records WHERE created_at >= ? AND created_at <= ?',
                       (start_date, end_date))
        row = cursor.fetchone()
        if row:
            stats['recent_activities'] = row[0] or 0

        conn.close()
    except Exception as e:
        logger.error(f"获取分析统计数据失败: {e}")

    return stats


def fetch_score_distribution(subject=''):
    """获取成绩分布数据 - 返回原始字典"""
    distribution = {
        'labels': ['0-59', '60-69', '70-79', '80-89', '90-100'],
        'data': [0, 0, 0, 0, 0]
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = '''
            SELECT
                SUM(CASE WHEN score < 60 THEN 1 ELSE 0 END) as range_0_59,
                SUM(CASE WHEN score >= 60 AND score < 70 THEN 1 ELSE 0 END) as range_60_69,
                SUM(CASE WHEN score >= 70 AND score < 80 THEN 1 ELSE 0 END) as range_70_79,
                SUM(CASE WHEN score >= 80 AND score < 90 THEN 1 ELSE 0 END) as range_80_89,
                SUM(CASE WHEN score >= 90 THEN 1 ELSE 0 END) as range_90_100
            FROM exam_results
            WHERE status = 'completed'
        '''
        params = []
        if subject:
            query += ' AND subject = ?'
            params.append(subject)

        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            distribution['data'] = [
                row['range_0_59'] or 0,
                row['range_60_69'] or 0,
                row['range_70_79'] or 0,
                row['range_80_89'] or 0,
                row['range_90_100'] or 0
            ]

        conn.close()
    except Exception as e:
        logger.error(f"获取成绩分布数据失败: {e}")

    return distribution


def fetch_subject_scores():
    """获取科目成绩数据 - 返回原始字典"""
    subjects = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT subject, AVG(score) as avg_score, COUNT(*) as exam_count
            FROM exam_results
            WHERE status = 'completed' AND subject IS NOT NULL
            GROUP BY subject
            ORDER BY avg_score DESC
        ''')

        for row in cursor.fetchall():
            subjects.append({
                'subject': row['subject'],
                'avg_score': round(row['avg_score'] or 0, 1),
                'exam_count': row['exam_count'] or 0
            })

        conn.close()
    except Exception as e:
        logger.error(f"获取科目成绩数据失败: {e}")

    return {
        'labels': [s['subject'] for s in subjects],
        'data': [s['avg_score'] for s in subjects],
        'subjects': subjects
    }


def fetch_study_time_trend(time_range='week'):
    """获取学习时间趋势数据 - 返回原始字典"""
    if time_range == 'week':
        labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        trend_data = [0] * 7
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%w', created_at) as day_of_week, SUM(duration) as total_duration
                FROM learning_records
                WHERE activity_type = 'study' AND created_at >= date('now', '-7 days')
                GROUP BY day_of_week
                ORDER BY day_of_week
            ''')
            for row in cursor.fetchall():
                index = int(row[0])
                if index < len(labels):
                    trend_data[index] = round(row[1] or 0, 0)
            conn.close()
        except Exception as e:
            logger.error(f"获取学习时间趋势(周)失败: {e}")
    elif time_range == 'month':
        labels = [f'{i}日' for i in range(1, 32)]
        trend_data = [0] * 31
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%d', created_at) as day_of_month, SUM(duration) as total_duration
                FROM learning_records
                WHERE activity_type = 'study' AND created_at >= date('now', '-30 days')
                GROUP BY day_of_month
                ORDER BY day_of_month
            ''')
            for row in cursor.fetchall():
                index = int(row[0]) - 1
                if index >= 0 and index < len(labels):
                    trend_data[index] = round(row[1] or 0, 0)
            conn.close()
        except Exception as e:
            logger.error(f"获取学习时间趋势(月)失败: {e}")
    else:
        labels = ['第1周', '第2周', '第3周', '第4周']
        trend_data = [0] * 4
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%W', created_at) as week_num, SUM(duration) as total_duration
                FROM learning_records
                WHERE activity_type = 'study' AND created_at >= date('now', '-30 days')
                GROUP BY week_num
                ORDER BY week_num
                LIMIT 4
            ''')
            idx = 0
            for row in cursor.fetchall():
                if idx < len(trend_data):
                    trend_data[idx] = round(row[1] or 0, 0)
                    idx += 1
            conn.close()
        except Exception as e:
            logger.error(f"获取学习时间趋势(季度)失败: {e}")

    return {
        'labels': labels,
        'data': trend_data
    }


def fetch_wrong_rate():
    """获取错题率数据 - 返回原始字典"""
    wrong_rate_data = {
        'labels': ['掌握良好(<30%)', '需要加强(30-50%)', '薄弱(50-70%)', '严重薄弱(>70%)'],
        'data': [0, 0, 0, 0]
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                SUM(CASE WHEN wrong_rate < 30 THEN 1 ELSE 0 END) as good,
                SUM(CASE WHEN wrong_rate >= 30 AND wrong_rate < 50 THEN 1 ELSE 0 END) as need_improve,
                SUM(CASE WHEN wrong_rate >= 50 AND wrong_rate < 70 THEN 1 ELSE 0 END) as weak,
                SUM(CASE WHEN wrong_rate >= 70 THEN 1 ELSE 0 END) as severe_weak
            FROM (
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN is_wrong = 1 THEN 1 ELSE 0 END) as wrong_count,
                       (SUM(CASE WHEN is_wrong = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as wrong_rate
                FROM user_answers
                GROUP BY question_id
            ) as question_stats
        ''')

        row = cursor.fetchone()
        if row:
            wrong_rate_data['data'] = [
                row['good'] or 0,
                row['need_improve'] or 0,
                row['weak'] or 0,
                row['severe_weak'] or 0
            ]

        conn.close()
    except Exception as e:
        logger.error(f"获取错题率数据失败: {e}")

    return wrong_rate_data


def fetch_top_students(subject='', limit=10):
    """获取成绩排名数据 - 返回原始字典"""
    top_students = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = '''
            SELECT u.id, u.username, 
                   AVG(er.score) as avg_score,
                   COUNT(er.id) as exam_count,
                   MAX(er.score) as max_score,
                   MIN(er.score) as min_score
            FROM users u
            LEFT JOIN exam_results er ON u.id = er.user_id AND er.status = 'completed'
            WHERE u.role = 'student'
        '''
        params = []

        if subject:
            query += ' AND er.subject = ?'
            params.append(subject)

        query += ' GROUP BY u.id ORDER BY avg_score DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)

        rank = 1
        for row in cursor.fetchall():
            avg_score = round(row['avg_score'] or 0, 1)
            max_score = row['max_score'] or 0
            min_score = row['min_score'] or 0
            progress = round((avg_score - min_score), 1) if min_score > 0 else round(avg_score * 0.1, 1)

            top_students.append({
                'rank': rank,
                'user_id': row['id'],
                'name': row['username'],
                'avg_score': avg_score,
                'exam_count': row['exam_count'] or 0,
                'progress': progress
            })
            rank += 1

        conn.close()
    except Exception as e:
        logger.error(f"获取成绩排名数据失败: {e}")

    return top_students


def fetch_weak_points(subject=''):
    """获取薄弱知识点数据 - 返回原始字典"""
    weak_points = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if subject:
            cursor.execute('''
                SELECT q.subject, q.knowledge_point,
                       COUNT(*) as total_questions,
                       SUM(CASE WHEN ua.is_wrong = 1 THEN 1 ELSE 0 END) as wrong_count,
                       (SUM(CASE WHEN ua.is_wrong = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as wrong_rate
                FROM questions q
                LEFT JOIN user_answers ua ON q.id = ua.question_id
                WHERE q.knowledge_point IS NOT NULL AND q.subject = ?
                GROUP BY q.knowledge_point
                ORDER BY wrong_rate DESC
                LIMIT 10
            ''', (subject,))
        else:
            cursor.execute('''
                SELECT q.subject, q.knowledge_point,
                       COUNT(*) as total_questions,
                       SUM(CASE WHEN ua.is_wrong = 1 THEN 1 ELSE 0 END) as wrong_count,
                       (SUM(CASE WHEN ua.is_wrong = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as wrong_rate
                FROM questions q
                LEFT JOIN user_answers ua ON q.id = ua.question_id
                WHERE q.knowledge_point IS NOT NULL
                GROUP BY q.knowledge_point
                ORDER BY wrong_rate DESC
                LIMIT 10
            ''')

        for row in cursor.fetchall():
            wrong_rate = round(row['wrong_rate'] or 0, 0)
            if wrong_rate > 0:
                if wrong_rate > 70:
                    level = '严重薄弱'
                elif wrong_rate > 50:
                    level = '薄弱'
                elif wrong_rate > 30:
                    level = '需要加强'
                else:
                    level = '掌握良好'

                weak_points.append({
                    'point': row['knowledge_point'],
                    'subject': row['subject'],
                    'wrong_rate': wrong_rate,
                    'level': level,
                    'total_questions': row['total_questions'] or 0,
                    'wrong_count': row['wrong_count'] or 0
                })

        conn.close()
    except Exception as e:
        logger.error(f"获取薄弱知识点数据失败: {e}")

    return weak_points


def fetch_student_detail(user_id):
    """获取学生详情数据 - 返回原始字典或None"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, username, email, created_at FROM users WHERE id = ?', (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return None

        student = {
            'id': user_row['id'],
            'username': user_row['username'],
            'email': user_row['email'],
            'created_at': user_row['created_at']
        }

        cursor.execute('''
            SELECT AVG(score) as avg_score, COUNT(*) as exam_count, 
                   MAX(score) as max_score, MIN(score) as min_score
            FROM exam_results
            WHERE user_id = ? AND status = 'completed'
        ''', (user_id,))
        exam_row = cursor.fetchone()
        student['exam_stats'] = {
            'avg_score': round(exam_row['avg_score'] or 0, 1),
            'exam_count': exam_row['exam_count'] or 0,
            'max_score': exam_row['max_score'] or 0,
            'min_score': exam_row['min_score'] or 0
        }

        cursor.execute('''
            SELECT SUM(duration) as total_duration, COUNT(*) as activity_count
            FROM learning_records
            WHERE user_id = ?
        ''', (user_id,))
        study_row = cursor.fetchone()
        student['study_stats'] = {
            'total_duration': study_row['total_duration'] or 0,
            'activity_count': study_row['activity_count'] or 0
        }

        cursor.execute('''
            SELECT subject, AVG(score) as avg_score
            FROM exam_results
            WHERE user_id = ? AND status = 'completed' AND subject IS NOT NULL
            GROUP BY subject
        ''', (user_id,))
        subject_scores = []
        for row in cursor.fetchall():
            subject_scores.append({
                'subject': row['subject'],
                'avg_score': round(row['avg_score'] or 0, 1)
            })
        student['subject_scores'] = subject_scores

        conn.close()
        return student

    except Exception as e:
        logger.error(f"获取学生详情数据失败: {e}")
        return None


@student_analytics_api.route('/api/student/analytics/stats', methods=['GET'])
@require_login
def get_analytics_stats():
    if not has_access():
        return create_response(403, '无权访问')

    subject = request.args.get('subject', '')
    cls = request.args.get('class', '')
    time_range = request.args.get('timeRange', 'month')

    stats = fetch_analytics_stats(subject, cls, time_range)
    return create_response(200, 'success', stats)


@student_analytics_api.route('/api/student/analytics/score_distribution', methods=['GET'])
@require_login
def get_score_distribution():
    if not has_access():
        return create_response(403, '无权访问')

    subject = request.args.get('subject', '')
    distribution = fetch_score_distribution(subject)
    return create_response(200, 'success', distribution)


@student_analytics_api.route('/api/student/analytics/subject_scores', methods=['GET'])
@require_login
def get_subject_scores():
    if not has_access():
        return create_response(403, '无权访问')

    subject_scores = fetch_subject_scores()
    return create_response(200, 'success', subject_scores)


@student_analytics_api.route('/api/student/analytics/study_time_trend', methods=['GET'])
@require_login
def get_study_time_trend():
    if not has_access():
        return create_response(403, '无权访问')

    time_range = request.args.get('timeRange', 'week')
    trend = fetch_study_time_trend(time_range)
    return create_response(200, 'success', trend)


@student_analytics_api.route('/api/student/analytics/wrong_rate', methods=['GET'])
@require_login
def get_wrong_rate():
    if not has_access():
        return create_response(403, '无权访问')

    wrong_rate = fetch_wrong_rate()
    return create_response(200, 'success', wrong_rate)


@student_analytics_api.route('/api/student/analytics/top_students', methods=['GET'])
@require_login
def get_top_students():
    if not has_access():
        return create_response(403, '无权访问')

    subject = request.args.get('subject', '')
    limit = int(request.args.get('limit', 10))

    top_students = fetch_top_students(subject, limit)
    return create_response(200, 'success', {'students': top_students})


@student_analytics_api.route('/api/student/analytics/weak_points', methods=['GET'])
@require_login
def get_weak_points():
    if not has_access():
        return create_response(403, '无权访问')

    subject = request.args.get('subject', '')
    weak_points = fetch_weak_points(subject)
    return create_response(200, 'success', {'weak_points': weak_points})


@student_analytics_api.route('/api/student/analytics/student_detail/<int:user_id>', methods=['GET'])
@require_login
def get_student_detail(user_id):
    if not has_access():
        return create_response(403, '无权访问')

    student = fetch_student_detail(user_id)
    if student is None:
        return create_response(404, '学生不存在')

    return create_response(200, 'success', student)


@student_analytics_api.route('/api/student/analytics/all', methods=['GET'])
@require_login
def get_all_analytics():
    if not has_access():
        return create_response(403, '无权访问')

    subject = request.args.get('subject', '')
    cls = request.args.get('class', '')
    time_range = request.args.get('timeRange', 'month')

    return create_response(200, 'success', {
        'stats': fetch_analytics_stats(subject, cls, time_range),
        'score_distribution': fetch_score_distribution(subject),
        'subject_scores': fetch_subject_scores(),
        'study_time_trend': fetch_study_time_trend(time_range),
        'wrong_rate': fetch_wrong_rate(),
        'top_students': fetch_top_students(subject, 10),
        'weak_points': fetch_weak_points(subject)
    })
