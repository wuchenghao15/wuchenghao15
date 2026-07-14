# -*- coding: utf-8 -*-
"""
数据分析系统API - 数据可视化、智能报表、趋势分析、预测模型
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

data_analysis_api = Blueprint('data_analysis_api', __name__)

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


def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                data_source TEXT,
                chart_type TEXT DEFAULT 'line',
                filters TEXT DEFAULT '{}',
                columns TEXT DEFAULT '[]',
                layout TEXT DEFAULT '{}',
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                schedule_type TEXT DEFAULT 'daily',
                schedule_time TEXT,
                last_run TEXT,
                next_run TEXT,
                status TEXT DEFAULT 'active',
                recipients TEXT DEFAULT '[]',
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES report_templates(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                execution_time TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'running',
                data TEXT,
                error_message TEXT,
                duration INTEGER DEFAULT 0,
                FOREIGN KEY (report_id) REFERENCES scheduled_reports(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                widgets TEXT DEFAULT '[]',
                layout TEXT DEFAULT '{}',
                refresh_interval INTEGER DEFAULT 300,
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dashboard_widgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dashboard_id INTEGER NOT NULL,
                widget_type TEXT NOT NULL,
                title TEXT,
                data_source TEXT,
                x_axis TEXT,
                y_axis TEXT,
                filters TEXT DEFAULT '{}',
                position TEXT DEFAULT '{}',
                refresh_interval INTEGER DEFAULT 300,
                FOREIGN KEY (dashboard_id) REFERENCES dashboards(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_name TEXT NOT NULL,
                query_type TEXT DEFAULT 'sql',
                query_text TEXT NOT NULL,
                parameters TEXT DEFAULT '{}',
                data_source TEXT DEFAULT 'app',
                description TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                data_source TEXT,
                time_range TEXT DEFAULT '7d',
                metrics TEXT DEFAULT '[]',
                results TEXT DEFAULT '{}',
                generated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT UNIQUE NOT NULL,
                model_type TEXT DEFAULT 'regression',
                description TEXT,
                features TEXT DEFAULT '[]',
                target TEXT,
                accuracy REAL DEFAULT 0,
                status TEXT DEFAULT 'trained',
                trained_at TEXT,
                last_used TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 数据分析系统表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建数据分析系统表失败: {e}")


create_tables()


@data_analysis_api.route('/api/analysis/dashboard', methods=['GET'])
@require_admin
def get_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM users WHERE role IN ("student", "student_vip")')
        student_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM users WHERE role IN ("teacher")')
        teacher_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM exams')
        exam_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM course_enrollments')
        enrollment_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE status = "graded"')
        graded_homework_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM wrong_answers')
        wrong_answer_count = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM exam_results
            WHERE created_at > ?
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        ''', [(datetime.now() - timedelta(days=7)).isoformat()])
        exam_trend = []
        for row in cursor.fetchall():
            exam_trend.append({'date': row['date'], 'count': row['count']})

        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM learning_records
            WHERE created_at > ?
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        ''', [(datetime.now() - timedelta(days=7)).isoformat()])
        learning_trend = []
        for row in cursor.fetchall():
            learning_trend.append({'date': row['date'], 'count': row['count']})

        cursor.execute('''
            SELECT e.subject, COUNT(*) as exam_count, AVG(er.total_score) as avg_score
            FROM exams e
            LEFT JOIN exam_results er ON e.id = er.exam_id
            GROUP BY e.subject
            ORDER BY exam_count DESC
            LIMIT 5
        ''')
        subject_stats = []
        for row in cursor.fetchall():
            subject_stats.append({
                'subject': row['subject'],
                'exam_count': row['exam_count'],
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        cursor.execute('''
            SELECT u.username, COUNT(er.id) as exam_count, AVG(er.total_score) as avg_score
            FROM users u
            JOIN exam_results er ON u.id = er.user_id
            WHERE u.role IN ("student", "student_vip")
            GROUP BY u.id
            ORDER BY avg_score DESC
            LIMIT 5
        ''')
        top_students = []
        for row in cursor.fetchall():
            top_students.append({
                'username': row['username'],
                'exam_count': row['exam_count'],
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        conn.close()

        return create_response(200, 'success', {
            'overview': {
                'total_users': total_users,
                'student_count': student_count,
                'teacher_count': teacher_count,
                'exam_count': exam_count,
                'enrollment_count': enrollment_count,
                'graded_homework_count': graded_homework_count,
                'wrong_answer_count': wrong_answer_count
            },
            'exam_trend': exam_trend,
            'learning_trend': learning_trend,
            'subject_stats': subject_stats,
            'top_students': top_students
        })

    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        return create_response(500, '获取仪表盘数据失败')


@data_analysis_api.route('/api/analysis/exam_stats', methods=['GET'])
@require_login
def get_exam_stats():
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        subject = request.args.get('subject', '')
        time_range = request.args.get('time_range', '30d')

        conn = get_db_connection()
        cursor = conn.cursor()

        days_map = {'7d': 7, '14d': 14, '30d': 30, '90d': 90}
        days = days_map.get(time_range, 30)
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()

        where_clauses = ['er.created_at > ?']
        params = [date_threshold]

        if subject:
            where_clauses.append('e.subject = ?')
            params.append(subject)

        if role not in ['admin', 'super_admin']:
            where_clauses.append('er.user_id = ?')
            params.append(user_id)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

        cursor.execute(f'''
            SELECT COUNT(*) as total_exams,
                   AVG(er.total_score) as avg_score,
                   MAX(er.total_score) as highest_score,
                   MIN(er.total_score) as lowest_score
            FROM exam_results er
            JOIN exams e ON er.exam_id = e.id
            {where_sql}
        ''', params)
        stats_row = cursor.fetchone()

        cursor.execute(f'''
            SELECT DATE(er.created_at) as date, COUNT(*) as exam_count, AVG(er.total_score) as avg_score
            FROM exam_results er
            JOIN exams e ON er.exam_id = e.id
            {where_sql}
            GROUP BY DATE(er.created_at)
            ORDER BY date DESC
        ''', params)
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row['date'],
                'exam_count': row['exam_count'],
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        cursor.execute(f'''
            SELECT e.subject, COUNT(*) as exam_count, AVG(er.total_score) as avg_score
            FROM exam_results er
            JOIN exams e ON er.exam_id = e.id
            {where_sql}
            GROUP BY e.subject
            ORDER BY exam_count DESC
        ''', params)
        subject_stats = []
        for row in cursor.fetchall():
            subject_stats.append({
                'subject': row['subject'],
                'exam_count': row['exam_count'],
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        cursor.execute(f'''
            SELECT e.difficulty, COUNT(*) as exam_count, AVG(er.total_score) as avg_score
            FROM exam_results er
            JOIN exams e ON er.exam_id = e.id
            {where_sql}
            GROUP BY e.difficulty
            ORDER BY exam_count DESC
        ''', params)
        difficulty_stats = []
        for row in cursor.fetchall():
            difficulty_stats.append({
                'difficulty': row['difficulty'],
                'exam_count': row['exam_count'],
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        conn.close()

        return create_response(200, 'success', {
            'stats': {
                'total_exams': stats_row['total_exams'] or 0,
                'avg_score': round(stats_row['avg_score'] or 0, 2),
                'highest_score': stats_row['highest_score'] or 0,
                'lowest_score': stats_row['lowest_score'] or 0
            },
            'daily_stats': daily_stats,
            'subject_stats': subject_stats,
            'difficulty_stats': difficulty_stats
        })

    except Exception as e:
        logger.error(f"获取考试统计失败: {e}")
        return create_response(500, '获取考试统计失败')


@data_analysis_api.route('/api/analysis/learning_stats', methods=['GET'])
@require_login
def get_learning_stats():
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        time_range = request.args.get('time_range', '30d')

        conn = get_db_connection()
        cursor = conn.cursor()

        days_map = {'7d': 7, '14d': 14, '30d': 30, '90d': 90}
        days = days_map.get(time_range, 30)
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()

        where_clauses = ['lr.created_at > ?']
        params = [date_threshold]

        if role not in ['admin', 'super_admin']:
            where_clauses.append('lr.user_id = ?')
            params.append(user_id)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

        cursor.execute(f'''
            SELECT COUNT(*) as total_activities,
                   SUM(lr.duration) as total_duration,
                   AVG(lr.progress) as avg_progress,
                   AVG(lr.score) as avg_score
            FROM learning_records lr
            {where_sql}
        ''', params)
        stats_row = cursor.fetchone()

        cursor.execute(f'''
            SELECT DATE(lr.created_at) as date, COUNT(*) as activity_count, SUM(lr.duration) as total_duration
            FROM learning_records lr
            {where_sql}
            GROUP BY DATE(lr.created_at)
            ORDER BY date DESC
        ''', params)
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row['date'],
                'activity_count': row['activity_count'],
                'total_duration': row['total_duration'] or 0
            })

        cursor.execute(f'''
            SELECT lr.activity_type, COUNT(*) as count, AVG(lr.progress) as avg_progress
            FROM learning_records lr
            {where_sql}
            GROUP BY lr.activity_type
            ORDER BY count DESC
        ''', params)
        activity_stats = []
        for row in cursor.fetchall():
            activity_stats.append({
                'activity_type': row['activity_type'],
                'count': row['count'],
                'avg_progress': round(row['avg_progress'] or 0, 2)
            })

        cursor.execute(f'''
            SELECT ls.current_streak, ls.longest_streak, ls.total_days
            FROM learning_streaks ls
            {where_sql.replace('lr.created_at', 'ls.user_id')}
        ''', params[:1] + ([user_id] if role not in ['admin', 'super_admin'] else []))
        streak_row = cursor.fetchone()
        streak_stats = {
            'current_streak': streak_row['current_streak'] or 0 if streak_row else 0,
            'longest_streak': streak_row['longest_streak'] or 0 if streak_row else 0,
            'total_days': streak_row['total_days'] or 0 if streak_row else 0
        }

        conn.close()

        return create_response(200, 'success', {
            'stats': {
                'total_activities': stats_row['total_activities'] or 0,
                'total_duration': stats_row['total_duration'] or 0,
                'avg_progress': round(stats_row['avg_progress'] or 0, 2),
                'avg_score': round(stats_row['avg_score'] or 0, 2)
            },
            'daily_stats': daily_stats,
            'activity_stats': activity_stats,
            'streak_stats': streak_stats
        })

    except Exception as e:
        logger.error(f"获取学习统计失败: {e}")
        return create_response(500, '获取学习统计失败')


@data_analysis_api.route('/api/analysis/student_progress/<int:user_id>', methods=['GET'])
@require_login
def get_student_progress(user_id):
    try:
        current_user_id = session.get('user_id')
        role = session.get('role')

        if role not in ['admin', 'super_admin', 'teacher'] and current_user_id != user_id:
            return create_response(403, '无权查看')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT username, role FROM users WHERE id = ?', (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return create_response(404, '用户不存在')

        cursor.execute('''
            SELECT COUNT(*) as total_exams, AVG(total_score) as avg_score
            FROM exam_results
            WHERE user_id = ? AND total_score IS NOT NULL
        ''', (user_id,))
        exam_stats = cursor.fetchone()

        cursor.execute('''
            SELECT DATE(created_at) as date, total_score
            FROM exam_results
            WHERE user_id = ? AND total_score IS NOT NULL
            ORDER BY date DESC
            LIMIT 10
        ''', (user_id,))
        exam_history = []
        for row in cursor.fetchall():
            exam_history.append({'date': row['date'], 'score': row['total_score']})

        cursor.execute('''
            SELECT subject, COUNT(*) as wrong_count
            FROM wrong_answers
            WHERE user_id = ?
            GROUP BY subject
            ORDER BY wrong_count DESC
        ''', (user_id,))
        weak_subjects = []
        for row in cursor.fetchall():
            weak_subjects.append({'subject': row['subject'], 'wrong_count': row['wrong_count']})

        cursor.execute('''
            SELECT chapter, COUNT(*) as wrong_count
            FROM wrong_answers
            WHERE user_id = ? AND chapter IS NOT NULL
            GROUP BY chapter
            ORDER BY wrong_count DESC
            LIMIT 5
        ''', (user_id,))
        weak_chapters = []
        for row in cursor.fetchall():
            weak_chapters.append({'chapter': row['chapter'], 'wrong_count': row['wrong_count']})

        cursor.execute('''
            SELECT c.title, ce.progress, ce.completed
            FROM course_enrollments ce
            JOIN courses c ON ce.course_id = c.id
            WHERE ce.user_id = ?
        ''', (user_id,))
        course_progress = []
        for row in cursor.fetchall():
            course_progress.append({
                'course_title': row['title'],
                'progress': round(row['progress'] or 0, 2),
                'completed': row['completed'] == 1
            })

        cursor.execute('''
            SELECT COUNT(*) as completed_count, AVG(score) as avg_score
            FROM homework_submissions
            WHERE user_id = ? AND status = "graded"
        ''', (user_id,))
        homework_stats = cursor.fetchone()

        cursor.execute('''
            SELECT COUNT(*) as unlocked_count, SUM(points) as total_points
            FROM user_achievements ua
            JOIN achievements a ON ua.achievement_id = a.id
            WHERE ua.user_id = ?
        ''', (user_id,))
        achievement_stats = cursor.fetchone()

        conn.close()

        return create_response(200, 'success', {
            'user': {
                'user_id': user_id,
                'username': user_row['username'],
                'role': user_row['role']
            },
            'exam_stats': {
                'total_exams': exam_stats['total_exams'] or 0,
                'avg_score': round(exam_stats['avg_score'] or 0, 2)
            },
            'exam_history': exam_history,
            'weak_subjects': weak_subjects,
            'weak_chapters': weak_chapters,
            'course_progress': course_progress,
            'homework_stats': {
                'completed_count': homework_stats['completed_count'] or 0,
                'avg_score': round(homework_stats['avg_score'] or 0, 2)
            },
            'achievement_stats': {
                'unlocked_count': achievement_stats['unlocked_count'] or 0,
                'total_points': achievement_stats['total_points'] or 0
            }
        })

    except Exception as e:
        logger.error(f"获取学生进度失败: {e}")
        return create_response(500, '获取学生进度失败')


@data_analysis_api.route('/api/analysis/course_stats', methods=['GET'])
@require_admin
def get_course_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM courses')
        total_courses = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM course_enrollments')
        total_enrollments = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM course_enrollments WHERE completed = 1')
        completed_courses = cursor.fetchone()[0] or 0

        cursor.execute('SELECT AVG(progress) FROM course_enrollments')
        avg_progress = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT c.title, c.subject, COUNT(ce.id) as enrollment_count, AVG(ce.progress) as avg_progress
            FROM courses c
            LEFT JOIN course_enrollments ce ON c.id = ce.course_id
            GROUP BY c.id
            ORDER BY enrollment_count DESC
            LIMIT 10
        ''')
        course_popularity = []
        for row in cursor.fetchall():
            course_popularity.append({
                'title': row['title'],
                'subject': row['subject'],
                'enrollment_count': row['enrollment_count'],
                'avg_progress': round(row['avg_progress'] or 0, 2)
            })

        cursor.execute('''
            SELECT c.subject, COUNT(c.id) as course_count, COUNT(ce.id) as enrollment_count
            FROM courses c
            LEFT JOIN course_enrollments ce ON c.id = ce.course_id
            GROUP BY c.subject
            ORDER BY course_count DESC
        ''')
        subject_distribution = []
        for row in cursor.fetchall():
            subject_distribution.append({
                'subject': row['subject'],
                'course_count': row['course_count'],
                'enrollment_count': row['enrollment_count']
            })

        cursor.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
            FROM course_reviews
        ''')
        review_stats = cursor.fetchone()

        conn.close()

        return create_response(200, 'success', {
            'overview': {
                'total_courses': total_courses,
                'total_enrollments': total_enrollments,
                'completed_courses': completed_courses,
                'avg_progress': round(avg_progress, 2),
                'avg_rating': round(review_stats['avg_rating'] or 0, 2),
                'review_count': review_stats['review_count'] or 0
            },
            'course_popularity': course_popularity,
            'subject_distribution': subject_distribution
        })

    except Exception as e:
        logger.error(f"获取课程统计失败: {e}")
        return create_response(500, '获取课程统计失败')


@data_analysis_api.route('/api/analysis/homework_stats', methods=['GET'])
@require_admin
def get_homework_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM homework_assignments')
        total_assignments = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM homework_submissions')
        total_submissions = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE status = "graded"')
        graded_count = cursor.fetchone()[0] or 0

        cursor.execute('SELECT AVG(score) FROM homework_submissions WHERE status = "graded"')
        avg_score = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT hs.status, COUNT(*) as count
            FROM homework_submissions hs
            GROUP BY hs.status
        ''')
        status_distribution = []
        for row in cursor.fetchall():
            status_distribution.append({'status': row['status'], 'count': row['count']})

        cursor.execute('''
            SELECT ha.title, ha.subject, COUNT(hs.id) as submission_count, AVG(hs.score) as avg_score
            FROM homework_assignments ha
            LEFT JOIN homework_submissions hs ON ha.id = hs.homework_id AND hs.status = "graded"
            GROUP BY ha.id
            ORDER BY submission_count DESC
            LIMIT 10
        ''')
        assignment_stats = []
        for row in cursor.fetchall():
            assignment_stats.append({
                'title': row['title'],
                'subject': row['subject'],
                'submission_count': row['submission_count'] or 0,
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        cursor.execute('''
            SELECT ha.subject, COUNT(ha.id) as assignment_count, COUNT(hs.id) as submission_count, AVG(hs.score) as avg_score
            FROM homework_assignments ha
            LEFT JOIN homework_submissions hs ON ha.id = hs.homework_id AND hs.status = "graded"
            GROUP BY ha.subject
            ORDER BY assignment_count DESC
        ''')
        subject_stats = []
        for row in cursor.fetchall():
            subject_stats.append({
                'subject': row['subject'],
                'assignment_count': row['assignment_count'],
                'submission_count': row['submission_count'] or 0,
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        conn.close()

        return create_response(200, 'success', {
            'overview': {
                'total_assignments': total_assignments,
                'total_submissions': total_submissions,
                'graded_count': graded_count,
                'avg_score': round(avg_score, 2),
                'submission_rate': round((total_submissions / (total_assignments * 10)) * 100, 2) if total_assignments > 0 else 0
            },
            'status_distribution': status_distribution,
            'assignment_stats': assignment_stats,
            'subject_stats': subject_stats
        })

    except Exception as e:
        logger.error(f"获取作业统计失败: {e}")
        return create_response(500, '获取作业统计失败')


@data_analysis_api.route('/api/analysis/trend', methods=['POST'])
@require_admin
def analyze_trend():
    try:
        data = request.get_json() or {}
        analysis_type = data.get('analysis_type', 'exam')
        time_range = data.get('time_range', '30d')

        conn = get_db_connection()
        cursor = conn.cursor()

        days_map = {'7d': 7, '14d': 14, '30d': 30, '90d': 90}
        days = days_map.get(time_range, 30)
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()

        if analysis_type == 'exam':
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count, AVG(total_score) as avg_score
                FROM exam_results
                WHERE created_at > ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (date_threshold,))
            trend_data = []
            for row in cursor.fetchall():
                trend_data.append({
                    'date': row['date'],
                    'count': row['count'],
                    'avg_score': round(row['avg_score'] or 0, 2)
                })

            if trend_data:
                first_score = trend_data[0]['avg_score']
                last_score = trend_data[-1]['avg_score']
                trend_direction = 'up' if last_score > first_score else 'down' if last_score < first_score else 'stable'
                trend_change = round(((last_score - first_score) / first_score) * 100, 2) if first_score > 0 else 0
            else:
                trend_direction = 'stable'
                trend_change = 0

        elif analysis_type == 'learning':
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as activity_count, SUM(duration) as total_duration
                FROM learning_records
                WHERE created_at > ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (date_threshold,))
            trend_data = []
            for row in cursor.fetchall():
                trend_data.append({
                    'date': row['date'],
                    'activity_count': row['activity_count'],
                    'total_duration': row['total_duration'] or 0
                })

            if trend_data:
                first_count = trend_data[0]['activity_count']
                last_count = trend_data[-1]['activity_count']
                trend_direction = 'up' if last_count > first_count else 'down' if last_count < first_count else 'stable'
                trend_change = round(((last_count - first_count) / first_count) * 100, 2) if first_count > 0 else 0
            else:
                trend_direction = 'stable'
                trend_change = 0

        else:
            conn.close()
            return create_response(400, '不支持的分析类型')

        conn.close()

        return create_response(200, 'success', {
            'analysis_type': analysis_type,
            'time_range': time_range,
            'trend_data': trend_data,
            'trend_direction': trend_direction,
            'trend_change': trend_change,
            'trend_summary': f"近{days}天{analysis_type}趋势{'上升' if trend_direction == 'up' else '下降' if trend_direction == 'down' else '稳定'}{abs(trend_change)}%" if trend_change != 0 else f"近{days}天{analysis_type}趋势稳定"
        })

    except Exception as e:
        logger.error(f"趋势分析失败: {e}")
        return create_response(500, '趋势分析失败')


@data_analysis_api.route('/api/analysis/reports', methods=['GET'])
@require_admin
def get_reports():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT rt.id, rt.template_code, rt.name, rt.description, rt.chart_type,
                   u.username as created_name, rt.created_at
            FROM report_templates rt
            JOIN users u ON rt.created_by = u.id
            ORDER BY rt.created_at DESC
        ''')
        templates = []
        for row in cursor.fetchall():
            templates.append({
                'id': row['id'],
                'template_code': row['template_code'],
                'name': row['name'],
                'description': row['description'] or '',
                'chart_type': row['chart_type'],
                'created_name': row['created_name'],
                'created_at': row['created_at']
            })

        conn.close()
        return create_response(200, 'success', {'templates': templates})

    except Exception as e:
        logger.error(f"获取报表模板失败: {e}")
        return create_response(500, '获取报表模板失败')