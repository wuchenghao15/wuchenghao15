# -*- coding: utf-8 -*-
"""
课程管理系统API - 课程创建、课程管理、课程学习、课程评价
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

course_management_api = Blueprint('course_management_api', __name__)

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
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT,
                level TEXT DEFAULT 'beginner',
                duration INTEGER DEFAULT 0,
                lesson_count INTEGER DEFAULT 0,
                cover_image TEXT,
                status TEXT DEFAULT 'draft',
                creator_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                content TEXT,
                video_url TEXT,
                duration INTEGER DEFAULT 0,
                order_num INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                enrollment_date TEXT NOT NULL,
                progress REAL DEFAULT 0,
                completed INTEGER DEFAULT 0,
                completed_at TEXT,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(course_id, user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lesson_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                completed INTEGER DEFAULT 0,
                completed_at TEXT,
                watch_progress REAL DEFAULT 0,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (lesson_id) REFERENCES course_lessons(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(course_id, lesson_id, user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER DEFAULT 5,
                comment TEXT,
                helpful_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(course_id, user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                icon TEXT DEFAULT '📚',
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_category_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (category_id) REFERENCES course_categories(id),
                UNIQUE(course_id, category_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                lesson_id INTEGER,
                name TEXT NOT NULL,
                file_path TEXT,
                file_type TEXT,
                size INTEGER DEFAULT 0,
                uploaded_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (lesson_id) REFERENCES course_lessons(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                lesson_id INTEGER,
                title TEXT NOT NULL,
                question_count INTEGER DEFAULT 0,
                passing_score REAL DEFAULT 60,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (lesson_id) REFERENCES course_lessons(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                score REAL DEFAULT 0,
                total_score REAL DEFAULT 0,
                passed INTEGER DEFAULT 0,
                attempt_count INTEGER DEFAULT 1,
                completed_at TEXT,
                FOREIGN KEY (quiz_id) REFERENCES course_quizzes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 课程管理系统表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建课程管理系统表失败: {e}")


create_tables()


@course_management_api.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        subject = request.args.get('subject', '')
        level = request.args.get('level', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = ['c.is_active = 1']
        params = []

        if subject:
            where_clauses.append('c.subject = ?')
            params.append(subject)
        if level:
            where_clauses.append('c.grade_level = ?')
            params.append(level)

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

        cursor.execute(f'''
            SELECT COUNT(DISTINCT c.id) FROM courses c {where_sql}
        ''', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT c.id, c.course_name, c.description, c.subject, c.grade_level, 
                   c.duration_hours, c.difficulty, c.created_at
            FROM courses c
            {where_sql}
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        courses = []
        for row in cursor.fetchall():
            courses.append({
                'id': row['id'],
                'title': row['course_name'],
                'description': row['description'] or '',
                'subject': row['subject'] or '',
                'level': row['grade_level'] or '',
                'duration': int((row['duration_hours'] or 0) * 60),
                'lesson_count': 0,
                'enrollment_count': 0,
                'avg_rating': 0.0,
                'review_count': 0,
                'created_at': row['created_at']
            })
        conn.close()
        return create_response(200, 'success', {
            'courses': courses,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取课程列表失败: {e}")
        return create_response(500, '获取课程列表失败')


@course_management_api.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course_detail(course_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT c.id, c.title, c.description, c.subject, c.level, c.duration, 
                   c.lesson_count, c.cover_image, c.status, c.creator_id, 
                   u.username as creator_name, c.created_at, c.updated_at,
                   COUNT(DISTINCT ce.id) as enrollment_count,
                   AVG(cr.rating) as avg_rating,
                   COUNT(DISTINCT cr.id) as review_count
            FROM courses c
            JOIN users u ON c.creator_id = u.id
            LEFT JOIN course_enrollments ce ON c.id = ce.course_id
            LEFT JOIN course_reviews cr ON c.id = cr.course_id
            WHERE c.id = ?
            GROUP BY c.id
        ''', (course_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '课程不存在')

        cursor.execute('''
            SELECT id, title, description, duration, order_num, status, video_url
            FROM course_lessons
            WHERE course_id = ?
            ORDER BY order_num
        ''', (course_id,))
        lessons = []
        for lesson_row in cursor.fetchall():
            lessons.append({
                'id': lesson_row['id'],
                'title': lesson_row['title'],
                'description': lesson_row['description'] or '',
                'duration': lesson_row['duration'] or 0,
                'order_num': lesson_row['order_num'],
                'status': lesson_row['status'],
                'video_url': lesson_row['video_url'] or ''
            })

        cursor.execute('''
            SELECT cc.id, cc.name, cc.icon
            FROM course_category_associations cca
            JOIN course_categories cc ON cca.category_id = cc.id
            WHERE cca.course_id = ?
        ''', (course_id,))
        categories = []
        for cat_row in cursor.fetchall():
            categories.append({
                'id': cat_row['id'],
                'name': cat_row['name'],
                'icon': cat_row['icon']
            })

        user_id = session.get('user_id')
        is_enrolled = False
        progress = 0
        completed = False
        if user_id:
            cursor.execute('SELECT progress, completed FROM course_enrollments WHERE course_id = ? AND user_id = ?', (course_id, user_id))
            enrollment = cursor.fetchone()
            if enrollment:
                is_enrolled = True
                progress = enrollment['progress'] or 0
                completed = enrollment['completed'] == 1

        conn.close()
        return create_response(200, 'success', {
            'id': row['id'],
            'title': row['title'],
            'description': row['description'] or '',
            'subject': row['subject'] or '',
            'level': row['level'],
            'duration': row['duration'] or 0,
            'lesson_count': row['lesson_count'] or 0,
            'cover_image': row['cover_image'] or '',
            'status': row['status'],
            'creator_id': row['creator_id'],
            'creator_name': row['creator_name'],
            'enrollment_count': row['enrollment_count'] or 0,
            'avg_rating': round(row['avg_rating'] or 0, 1),
            'review_count': row['review_count'] or 0,
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'lessons': lessons,
            'categories': categories,
            'is_enrolled': is_enrolled,
            'progress': round(progress, 2),
            'completed': completed
        })

    except Exception as e:
        logger.error(f"获取课程详情失败: {e}")
        return create_response(500, '获取课程详情失败')


@course_management_api.route('/api/courses', methods=['POST'])
@require_admin
def create_course():
    try:
        data = request.get_json() or {}
        title = data.get('title', '')
        description = data.get('description', '')
        subject = data.get('subject', '')
        level = data.get('level', 'beginner')
        duration = data.get('duration', 0)

        if not title:
            return create_response(400, '课程标题不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO courses (course_name, subject, grade_level, description, duration_hours, difficulty, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (title, subject, level, description, duration / 60, 'medium', 1, time.time(), time.time()))
        course_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '课程创建成功', {'course_id': course_id, 'title': title})

    except Exception as e:
        logger.error(f"创建课程失败: {e}")
        return create_response(500, '创建课程失败')


@course_management_api.route('/api/courses/<int:course_id>', methods=['PUT', 'DELETE'])
@require_admin
def manage_course(course_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'PUT':
            data = request.get_json() or {}
            updates = []
            params = []

            if 'title' in data:
                updates.append('title = ?')
                params.append(data['title'])
            if 'description' in data:
                updates.append('description = ?')
                params.append(data['description'])
            if 'subject' in data:
                updates.append('subject = ?')
                params.append(data['subject'])
            if 'level' in data:
                updates.append('level = ?')
                params.append(data['level'])
            if 'duration' in data:
                updates.append('duration = ?')
                params.append(data['duration'])
            if 'cover_image' in data:
                updates.append('cover_image = ?')
                params.append(data['cover_image'])
            if 'status' in data:
                updates.append('status = ?')
                params.append(data['status'])

            if not updates:
                conn.close()
                return create_response(400, '没有可更新的字段')

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(course_id)

            cursor.execute(f'UPDATE courses SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return create_response(200, '课程更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM course_category_associations WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM course_resources WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM course_quizzes WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM lesson_progress WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM course_enrollments WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM course_reviews WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM course_lessons WHERE course_id = ?', (course_id,))
            cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
            conn.commit()
            conn.close()
            return create_response(200, '课程已删除')

    except Exception as e:
        logger.error(f"课程管理操作失败: {e}")
        return create_response(500, '课程管理操作失败')


@course_management_api.route('/api/courses/<int:course_id>/lessons', methods=['GET', 'POST'])
@require_login
def course_lessons(course_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute('''
                SELECT cl.id, cl.title, cl.description, cl.content, cl.video_url, 
                       cl.duration, cl.order_num, cl.status, cl.created_at
                FROM course_lessons cl
                WHERE cl.course_id = ?
                ORDER BY cl.order_num
            ''', (course_id,))

            lessons = []
            for row in cursor.fetchall():
                cursor.execute('SELECT completed, watch_progress FROM lesson_progress WHERE course_id = ? AND lesson_id = ? AND user_id = ?', (course_id, row['id'], user_id))
                progress = cursor.fetchone()

                lessons.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'] or '',
                    'content': row['content'] or '',
                    'video_url': row['video_url'] or '',
                    'duration': row['duration'] or 0,
                    'order_num': row['order_num'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'completed': progress['completed'] == 1 if progress else False,
                    'watch_progress': progress['watch_progress'] or 0 if progress else 0
                })
            conn.close()
            return create_response(200, 'success', {'lessons': lessons})

        elif request.method == 'POST':
            if role not in ['admin', 'super_admin', 'teacher']:
                conn.close()
                return create_response(403, '无权添加课程章节')

            data = request.get_json() or {}
            title = data.get('title', '')
            description = data.get('description', '')
            content = data.get('content', '')
            video_url = data.get('video_url', '')
            duration = data.get('duration', 0)
            order_num = data.get('order_num', 0)

            if not title:
                conn.close()
                return create_response(400, '章节标题不能为空')

            cursor.execute('INSERT INTO course_lessons (course_id, title, description, content, video_url, duration, order_num) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (course_id, title, description, content, video_url, duration, order_num))

            cursor.execute('UPDATE courses SET lesson_count = lesson_count + 1 WHERE id = ?', (course_id,))

            conn.commit()
            conn.close()
            return create_response(201, '课程章节添加成功')

    except Exception as e:
        logger.error(f"课程章节操作失败: {e}")
        return create_response(500, '课程章节操作失败')


@course_management_api.route('/api/courses/<int:course_id>/lessons/<int:lesson_id>', methods=['GET', 'PUT', 'DELETE'])
@require_login
def lesson_detail(course_id, lesson_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute('''
                SELECT cl.id, cl.title, cl.description, cl.content, cl.video_url, 
                       cl.duration, cl.order_num, cl.status, cl.created_at
                FROM course_lessons cl
                WHERE cl.id = ? AND cl.course_id = ?
            ''', (lesson_id, course_id))

            row = cursor.fetchone()
            if not row:
                conn.close()
                return create_response(404, '章节不存在')

            cursor.execute('SELECT completed, watch_progress FROM lesson_progress WHERE course_id = ? AND lesson_id = ? AND user_id = ?', (course_id, lesson_id, user_id))
            progress = cursor.fetchone()

            conn.close()
            return create_response(200, 'success', {
                'id': row['id'],
                'title': row['title'],
                'description': row['description'] or '',
                'content': row['content'] or '',
                'video_url': row['video_url'] or '',
                'duration': row['duration'] or 0,
                'order_num': row['order_num'],
                'status': row['status'],
                'created_at': row['created_at'],
                'completed': progress['completed'] == 1 if progress else False,
                'watch_progress': progress['watch_progress'] or 0 if progress else 0
            })

        elif request.method == 'PUT':
            if role not in ['admin', 'super_admin', 'teacher']:
                conn.close()
                return create_response(403, '无权修改章节')

            data = request.get_json() or {}
            updates = []
            params = []

            if 'title' in data:
                updates.append('title = ?')
                params.append(data['title'])
            if 'description' in data:
                updates.append('description = ?')
                params.append(data['description'])
            if 'content' in data:
                updates.append('content = ?')
                params.append(data['content'])
            if 'video_url' in data:
                updates.append('video_url = ?')
                params.append(data['video_url'])
            if 'duration' in data:
                updates.append('duration = ?')
                params.append(data['duration'])
            if 'order_num' in data:
                updates.append('order_num = ?')
                params.append(data['order_num'])
            if 'status' in data:
                updates.append('status = ?')
                params.append(data['status'])

            if not updates:
                conn.close()
                return create_response(400, '没有可更新的字段')

            params.append(lesson_id)
            params.append(course_id)

            cursor.execute(f'UPDATE course_lessons SET {", ".join(updates)} WHERE id = ? AND course_id = ?', params)
            conn.commit()
            conn.close()
            return create_response(200, '章节更新成功')

        elif request.method == 'DELETE':
            if role not in ['admin', 'super_admin', 'teacher']:
                conn.close()
                return create_response(403, '无权删除章节')

            cursor.execute('DELETE FROM lesson_progress WHERE course_id = ? AND lesson_id = ?', (course_id, lesson_id))
            cursor.execute('DELETE FROM course_lessons WHERE id = ? AND course_id = ?', (lesson_id, course_id))
            cursor.execute('UPDATE courses SET lesson_count = lesson_count - 1 WHERE id = ?', (course_id,))

            conn.commit()
            conn.close()
            return create_response(200, '章节已删除')

    except Exception as e:
        logger.error(f"章节操作失败: {e}")
        return create_response(500, '章节操作失败')


@course_management_api.route('/api/courses/<int:course_id>/enroll', methods=['POST'])
@require_login
def enroll_course(course_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, status FROM courses WHERE id = ?', (course_id,))
        course = cursor.fetchone()
        if not course:
            conn.close()
            return create_response(404, '课程不存在')

        if course['status'] != 'published':
            conn.close()
            return create_response(400, '课程未发布')

        cursor.execute('SELECT id FROM course_enrollments WHERE course_id = ? AND user_id = ?', (course_id, user_id))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '已报名该课程')

        cursor.execute('INSERT INTO course_enrollments (course_id, user_id, enrollment_date) VALUES (?, ?, ?)',
                     (course_id, user_id, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        return create_response(200, '报名课程成功')

    except Exception as e:
        logger.error(f"报名课程失败: {e}")
        return create_response(500, '报名课程失败')


@course_management_api.route('/api/courses/<int:course_id>/lessons/<int:lesson_id>/progress', methods=['POST'])
@require_login
def update_lesson_progress(course_id, lesson_id):
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        completed = data.get('completed', False)
        watch_progress = data.get('watch_progress', 0)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM course_enrollments WHERE course_id = ? AND user_id = ?', (course_id, user_id))
        if not cursor.fetchone():
            conn.close()
            return create_response(403, '请先报名课程')

        cursor.execute('''
            INSERT OR REPLACE INTO lesson_progress (course_id, lesson_id, user_id, completed, completed_at, watch_progress)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (course_id, lesson_id, user_id, 1 if completed else 0, datetime.now().isoformat() if completed else None, watch_progress))

        cursor.execute('SELECT COUNT(*) FROM course_lessons WHERE course_id = ?', (course_id,))
        total_lessons = cursor.fetchone()[0] or 0

        cursor.execute('SELECT COUNT(*) FROM lesson_progress WHERE course_id = ? AND user_id = ? AND completed = 1', (course_id, user_id))
        completed_lessons = cursor.fetchone()[0] or 0

        progress = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
        is_completed = completed_lessons == total_lessons

        cursor.execute('''
            UPDATE course_enrollments 
            SET progress = ?, completed = ?, completed_at = ? 
            WHERE course_id = ? AND user_id = ?
        ''', (progress, 1 if is_completed else 0, datetime.now().isoformat() if is_completed else None, course_id, user_id))

        conn.commit()
        conn.close()

        return create_response(200, '学习进度更新成功', {
            'progress': round(progress, 2),
            'completed': is_completed,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons
        })

    except Exception as e:
        logger.error(f"更新学习进度失败: {e}")
        return create_response(500, '更新学习进度失败')


@course_management_api.route('/api/courses/<int:course_id>/reviews', methods=['GET'])
def get_course_reviews(course_id):
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM course_reviews WHERE course_id = ?', (course_id,))
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT cr.id, cr.user_id, u.username, cr.rating, cr.comment, 
                   cr.helpful_count, cr.created_at
            FROM course_reviews cr
            JOIN users u ON cr.user_id = u.id
            WHERE cr.course_id = ?
            ORDER BY cr.created_at DESC
            LIMIT ? OFFSET ?
        ''', (course_id, per_page, offset))

        reviews = []
        for row in cursor.fetchall():
            reviews.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'],
                'rating': row['rating'],
                'comment': row['comment'] or '',
                'helpful_count': row['helpful_count'] or 0,
                'created_at': row['created_at']
            })
        conn.close()

        return create_response(200, 'success', {
            'reviews': reviews,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取课程评价失败: {e}")
        return create_response(500, '获取课程评价失败')


@course_management_api.route('/api/courses/<int:course_id>/reviews', methods=['POST'])
@require_login
def create_course_review(course_id):
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        rating = data.get('rating', 5)
        comment = data.get('comment', '')

        if rating < 1 or rating > 5:
            return create_response(400, '评分必须在1-5之间')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM course_enrollments WHERE course_id = ? AND user_id = ?', (course_id, user_id))
        if not cursor.fetchone():
            conn.close()
            return create_response(403, '请先报名并完成课程')

        cursor.execute('INSERT OR REPLACE INTO course_reviews (course_id, user_id, rating, comment) VALUES (?, ?, ?, ?)',
                     (course_id, user_id, rating, comment))
        conn.commit()
        conn.close()

        return create_response(200, '课程评价提交成功')

    except Exception as e:
        logger.error(f"创建课程评价失败: {e}")
        return create_response(500, '创建课程评价失败')


@course_management_api.route('/api/course_categories', methods=['GET'])
def get_course_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, description, icon, sort_order FROM course_categories ORDER BY sort_order')
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'] or '',
                'icon': row['icon'],
                'sort_order': row['sort_order']
            })
        conn.close()
        return create_response(200, 'success', {'categories': categories})

    except Exception as e:
        logger.error(f"获取课程分类失败: {e}")
        return create_response(500, '获取课程分类失败')


@course_management_api.route('/api/course_categories', methods=['POST'])
@require_admin
def create_course_category():
    try:
        data = request.get_json() or {}
        name = data.get('name', '')
        description = data.get('description', '')
        icon = data.get('icon', '📚')
        sort_order = data.get('sort_order', 0)

        if not name:
            return create_response(400, '分类名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM course_categories WHERE name = ?', (name,))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '分类名称已存在')

        cursor.execute('INSERT INTO course_categories (name, description, icon, sort_order) VALUES (?, ?, ?, ?)',
                     (name, description, icon, sort_order))
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '课程分类创建成功', {'category_id': category_id})

    except Exception as e:
        logger.error(f"创建课程分类失败: {e}")
        return create_response(500, '创建课程分类失败')