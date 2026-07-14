# -*- coding: utf-8 -*-
"""
考试增强API - 考试预约、成绩分析、错题重做、考试收藏、考试标签
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin, require_student
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

exam_enhancement_api = Blueprint('exam_enhancement_api', __name__)

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
            CREATE TABLE IF NOT EXISTS exam_appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                appointment_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_id) REFERENCES exams(id),
                UNIQUE(user_id, exam_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_id) REFERENCES exams(id),
                UNIQUE(user_id, exam_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#409eff',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_tag_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES exams(id),
                FOREIGN KEY (tag_id) REFERENCES exam_tags(id),
                UNIQUE(exam_id, tag_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrong_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                subject TEXT,
                chapter TEXT,
                difficulty TEXT,
                review_count INTEGER DEFAULT 0,
                last_review_at TEXT,
                mastered INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_id) REFERENCES exams(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                question_id INTEGER,
                note_text TEXT NOT NULL,
                note_type TEXT DEFAULT 'general',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_id) REFERENCES exams(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id_1 INTEGER NOT NULL,
                exam_id_2 INTEGER NOT NULL,
                score_diff REAL,
                question_diff TEXT,
                analysis TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exam_id_1) REFERENCES exams(id),
                FOREIGN KEY (exam_id_2) REFERENCES exams(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS score_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                exam_date TEXT NOT NULL,
                score REAL NOT NULL,
                total_score INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 考试增强表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建考试增强表失败: {e}")


create_tables()


@exam_enhancement_api.route('/api/exam/appointments', methods=['GET'])
@require_login
def get_appointments():
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if role in ['admin', 'super_admin', 'teacher']:
            cursor.execute('''
                SELECT ea.id, ea.user_id, u.username, ea.exam_id, e.title, e.subject, 
                       ea.appointment_time, ea.status, ea.created_at
                FROM exam_appointments ea
                JOIN users u ON ea.user_id = u.id
                JOIN exams e ON ea.exam_id = e.id
                ORDER BY ea.appointment_time DESC
            ''')
        else:
            cursor.execute('''
                SELECT ea.id, ea.user_id, ea.exam_id, e.title, e.subject, 
                       ea.appointment_time, ea.status, ea.created_at
                FROM exam_appointments ea
                JOIN exams e ON ea.exam_id = e.id
                WHERE ea.user_id = ?
                ORDER BY ea.appointment_time DESC
            ''', (user_id,))

        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'] if role in ['admin', 'super_admin', 'teacher'] else '',
                'exam_id': row['exam_id'],
                'exam_title': row['title'],
                'exam_subject': row['subject'],
                'appointment_time': row['appointment_time'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        conn.close()
        return create_response(200, 'success', {'appointments': appointments})

    except Exception as e:
        logger.error(f"获取考试预约失败: {e}")
        return create_response(500, '获取考试预约失败')


@exam_enhancement_api.route('/api/exam/appointments', methods=['POST'])
@require_student
def create_appointment():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        exam_id = data.get('exam_id')
        appointment_time = data.get('appointment_time')

        if not exam_id or not appointment_time:
            return create_response(400, '缺少必要参数')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM exams WHERE id = ?', (exam_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '考试不存在')

        cursor.execute('SELECT id FROM exam_appointments WHERE user_id = ? AND exam_id = ?', (user_id, exam_id))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '已预约该考试')

        cursor.execute('INSERT INTO exam_appointments (user_id, exam_id, appointment_time, status) VALUES (?, ?, ?, ?)',
                     (user_id, exam_id, appointment_time, 'pending'))
        conn.commit()
        conn.close()

        return create_response(201, '考试预约成功')

    except Exception as e:
        logger.error(f"创建考试预约失败: {e}")
        return create_response(500, '创建考试预约失败')


@exam_enhancement_api.route('/api/exam/appointments/<int:appointment_id>', methods=['PUT', 'DELETE'])
@require_login
def manage_appointment(appointment_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'PUT':
            data = request.get_json() or {}
            status = data.get('status')

            if role not in ['admin', 'super_admin', 'teacher']:
                cursor.execute('SELECT id FROM exam_appointments WHERE id = ? AND user_id = ?', (appointment_id, user_id))
                if not cursor.fetchone():
                    conn.close()
                    return create_response(403, '无权操作')
            else:
                cursor.execute('SELECT id FROM exam_appointments WHERE id = ?', (appointment_id,))
                if not cursor.fetchone():
                    conn.close()
                    return create_response(404, '预约不存在')

            if status not in ['pending', 'approved', 'rejected', 'completed']:
                conn.close()
                return create_response(400, '无效的状态值')

            cursor.execute('UPDATE exam_appointments SET status = ? WHERE id = ?', (status, appointment_id))
            conn.commit()
            conn.close()
            return create_response(200, '预约状态更新成功')

        elif request.method == 'DELETE':
            if role not in ['admin', 'super_admin', 'teacher']:
                cursor.execute('DELETE FROM exam_appointments WHERE id = ? AND user_id = ?', (appointment_id, user_id))
            else:
                cursor.execute('DELETE FROM exam_appointments WHERE id = ?', (appointment_id,))

            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected == 0:
                return create_response(404, '预约不存在')
            return create_response(200, '预约已取消')

    except Exception as e:
        logger.error(f"管理考试预约失败: {e}")
        return create_response(500, '管理考试预约失败')


@exam_enhancement_api.route('/api/exam/favorites', methods=['GET'])
@require_login
def get_favorites():
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ef.id, ef.exam_id, e.title, e.subject, e.duration, e.question_count, e.status, ef.created_at
            FROM exam_favorites ef
            JOIN exams e ON ef.exam_id = e.id
            WHERE ef.user_id = ?
            ORDER BY ef.created_at DESC
        ''', (user_id,))

        favorites = []
        for row in cursor.fetchall():
            favorites.append({
                'id': row['id'],
                'exam_id': row['exam_id'],
                'title': row['title'],
                'subject': row['subject'],
                'duration': row['duration'],
                'question_count': row['question_count'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        conn.close()
        return create_response(200, 'success', {'favorites': favorites})

    except Exception as e:
        logger.error(f"获取收藏考试失败: {e}")
        return create_response(500, '获取收藏考试失败')


@exam_enhancement_api.route('/api/exam/favorites', methods=['POST'])
@require_login
def toggle_favorite():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        exam_id = data.get('exam_id')
        action = data.get('action', 'add')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM exams WHERE id = ?', (exam_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '考试不存在')

        if action == 'add':
            cursor.execute('INSERT OR IGNORE INTO exam_favorites (user_id, exam_id) VALUES (?, ?)', (user_id, exam_id))
            conn.commit()
            conn.close()
            return create_response(200, '考试已收藏')
        else:
            cursor.execute('DELETE FROM exam_favorites WHERE user_id = ? AND exam_id = ?', (user_id, exam_id))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            if affected == 0:
                return create_response(404, '未收藏该考试')
            return create_response(200, '考试已取消收藏')

    except Exception as e:
        logger.error(f"收藏考试失败: {e}")
        return create_response(500, '收藏考试失败')


@exam_enhancement_api.route('/api/exam/tags', methods=['GET'])
def get_tags():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, tag_name, description, color FROM exam_tags ORDER BY tag_name')
        tags = []
        for row in cursor.fetchall():
            tags.append({
                'id': row['id'],
                'tag_name': row['tag_name'],
                'description': row['description'] or '',
                'color': row['color'] or '#409eff'
            })
        conn.close()
        return create_response(200, 'success', {'tags': tags})

    except Exception as e:
        logger.error(f"获取考试标签失败: {e}")
        return create_response(500, '获取考试标签失败')


@exam_enhancement_api.route('/api/exam/tags', methods=['POST'])
@require_admin
def create_tag():
    try:
        data = request.get_json() or {}
        tag_name = data.get('tag_name', '').strip()
        description = data.get('description', '')
        color = data.get('color', '#409eff')

        if not tag_name:
            return create_response(400, '标签名称不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM exam_tags WHERE tag_name = ?', (tag_name,))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '标签已存在')

        cursor.execute('INSERT INTO exam_tags (tag_name, description, color) VALUES (?, ?, ?)',
                     (tag_name, description, color))
        tag_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '标签创建成功', {'tag_id': tag_id, 'tag_name': tag_name})

    except Exception as e:
        logger.error(f"创建考试标签失败: {e}")
        return create_response(500, '创建考试标签失败')


@exam_enhancement_api.route('/api/exam/tags/<int:tag_id>/associate', methods=['POST'])
@require_admin
def associate_tag(tag_id):
    try:
        data = request.get_json() or {}
        exam_id = data.get('exam_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM exam_tags WHERE id = ?', (tag_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '标签不存在')

        cursor.execute('SELECT id FROM exams WHERE id = ?', (exam_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '考试不存在')

        cursor.execute('INSERT OR IGNORE INTO exam_tag_associations (exam_id, tag_id) VALUES (?, ?)', (exam_id, tag_id))
        conn.commit()
        conn.close()

        return create_response(200, '标签关联成功')

    except Exception as e:
        logger.error(f"关联考试标签失败: {e}")
        return create_response(500, '关联考试标签失败')


@exam_enhancement_api.route('/api/exam/<int:exam_id>/tags', methods=['GET'])
def get_exam_tags(exam_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT et.id, et.tag_name, et.description, et.color
            FROM exam_tag_associations eta
            JOIN exam_tags et ON eta.tag_id = et.id
            WHERE eta.exam_id = ?
        ''', (exam_id,))

        tags = []
        for row in cursor.fetchall():
            tags.append({
                'id': row['id'],
                'tag_name': row['tag_name'],
                'description': row['description'] or '',
                'color': row['color'] or '#409eff'
            })
        conn.close()
        return create_response(200, 'success', {'tags': tags})

    except Exception as e:
        logger.error(f"获取考试标签失败: {e}")
        return create_response(500, '获取考试标签失败')


@exam_enhancement_api.route('/api/exam/wrong_answers', methods=['GET'])
@require_login
def get_wrong_answers():
    try:
        user_id = session.get('user_id')
        subject = request.args.get('subject', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clause = ''
        params = [user_id]

        if subject:
            where_clause = 'AND subject = ?'
            params.append(subject)

        cursor.execute(f'''
            SELECT id, exam_id, question_id, question_text, user_answer, correct_answer, 
                   subject, chapter, difficulty, review_count, mastered, created_at
            FROM wrong_answers
            WHERE user_id = ? {where_clause}
            ORDER BY created_at DESC
        ''', params)

        wrong_answers = []
        for row in cursor.fetchall():
            wrong_answers.append({
                'id': row['id'],
                'exam_id': row['exam_id'],
                'question_id': row['question_id'],
                'question_text': row['question_text'],
                'user_answer': row['user_answer'],
                'correct_answer': row['correct_answer'],
                'subject': row['subject'],
                'chapter': row['chapter'],
                'difficulty': row['difficulty'],
                'review_count': row['review_count'],
                'mastered': row['mastered'] == 1,
                'created_at': row['created_at']
            })
        conn.close()
        return create_response(200, 'success', {'wrong_answers': wrong_answers})

    except Exception as e:
        logger.error(f"获取错题失败: {e}")
        return create_response(500, '获取错题失败')


@exam_enhancement_api.route('/api/exam/wrong_answers/<int:wrong_id>/review', methods=['POST'])
@require_login
def review_wrong_answer(wrong_id):
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        mastered = data.get('mastered', False)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id FROM wrong_answers WHERE id = ?', (wrong_id,))
        row = cursor.fetchone()
        if not row or row['user_id'] != user_id:
            conn.close()
            return create_response(403, '无权操作')

        cursor.execute('''
            UPDATE wrong_answers 
            SET review_count = review_count + 1, 
                last_review_at = ?, 
                mastered = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), 1 if mastered else 0, wrong_id))
        conn.commit()
        conn.close()

        return create_response(200, '错题复习记录成功')

    except Exception as e:
        logger.error(f"复习错题失败: {e}")
        return create_response(500, '复习错题失败')


@exam_enhancement_api.route('/api/exam/wrong_answers/<int:wrong_id>', methods=['DELETE'])
@require_login
def remove_wrong_answer(wrong_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id FROM wrong_answers WHERE id = ?', (wrong_id,))
        row = cursor.fetchone()
        if not row or row['user_id'] != user_id:
            conn.close()
            return create_response(403, '无权操作')

        cursor.execute('DELETE FROM wrong_answers WHERE id = ?', (wrong_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected == 0:
            return create_response(404, '错题不存在')
        return create_response(200, '错题已移除')

    except Exception as e:
        logger.error(f"移除错题失败: {e}")
        return create_response(500, '移除错题失败')


@exam_enhancement_api.route('/api/exam/wrong_answers/batch_review', methods=['POST'])
@require_login
def batch_review_wrong_answers():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        wrong_ids = data.get('wrong_ids', [])

        if not wrong_ids:
            return create_response(400, '请选择要复习的错题')

        conn = get_db_connection()
        cursor = conn.cursor()

        placeholders = ','.join('?' * len(wrong_ids))
        cursor.execute(f'''
            UPDATE wrong_answers 
            SET review_count = review_count + 1, 
                last_review_at = ?
            WHERE id IN ({placeholders}) AND user_id = ?
        ''', [datetime.now().isoformat()] + wrong_ids + [user_id])

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return create_response(200, f'已复习 {affected} 道错题')

    except Exception as e:
        logger.error(f"批量复习错题失败: {e}")
        return create_response(500, '批量复习错题失败')


@exam_enhancement_api.route('/api/exam/notes', methods=['GET'])
@require_login
def get_exam_notes():
    try:
        user_id = session.get('user_id')
        exam_id = request.args.get('exam_id', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        if exam_id:
            cursor.execute('''
                SELECT id, exam_id, question_id, note_text, note_type, created_at, updated_at
                FROM exam_notes
                WHERE user_id = ? AND exam_id = ?
                ORDER BY created_at DESC
            ''', (user_id, exam_id))
        else:
            cursor.execute('''
                SELECT id, exam_id, e.title, question_id, note_text, note_type, created_at, updated_at
                FROM exam_notes en
                JOIN exams e ON en.exam_id = e.id
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))

        notes = []
        for row in cursor.fetchall():
            notes.append({
                'id': row['id'],
                'exam_id': row['exam_id'],
                'exam_title': row.get('title', ''),
                'question_id': row['question_id'],
                'note_text': row['note_text'],
                'note_type': row['note_type'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        conn.close()
        return create_response(200, 'success', {'notes': notes})

    except Exception as e:
        logger.error(f"获取考试笔记失败: {e}")
        return create_response(500, '获取考试笔记失败')


@exam_enhancement_api.route('/api/exam/notes', methods=['POST'])
@require_login
def create_exam_note():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        exam_id = data.get('exam_id')
        question_id = data.get('question_id')
        note_text = data.get('note_text', '')
        note_type = data.get('note_type', 'general')

        if not exam_id or not note_text:
            return create_response(400, '缺少必要参数')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM exams WHERE id = ?', (exam_id,))
        if not cursor.fetchone():
            conn.close()
            return create_response(404, '考试不存在')

        cursor.execute('INSERT INTO exam_notes (user_id, exam_id, question_id, note_text, note_type) VALUES (?, ?, ?, ?, ?)',
                     (user_id, exam_id, question_id, note_text, note_type))
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return create_response(201, '笔记创建成功', {'note_id': note_id})

    except Exception as e:
        logger.error(f"创建考试笔记失败: {e}")
        return create_response(500, '创建考试笔记失败')


@exam_enhancement_api.route('/api/exam/notes/<int:note_id>', methods=['PUT', 'DELETE'])
@require_login
def manage_exam_note(note_id):
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id FROM exam_notes WHERE id = ?', (note_id,))
        row = cursor.fetchone()
        if not row or row['user_id'] != user_id:
            conn.close()
            return create_response(403, '无权操作')

        if request.method == 'PUT':
            data = request.get_json() or {}
            note_text = data.get('note_text')
            note_type = data.get('note_type')

            updates = []
            params = []

            if note_text is not None:
                updates.append('note_text = ?')
                params.append(note_text)
            if note_type:
                updates.append('note_type = ?')
                params.append(note_type)

            if not updates:
                conn.close()
                return create_response(400, '没有可更新的字段')

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(note_id)

            cursor.execute(f'UPDATE exam_notes SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return create_response(200, '笔记更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM exam_notes WHERE id = ?', (note_id,))
            conn.commit()
            conn.close()
            return create_response(200, '笔记已删除')

    except Exception as e:
        logger.error(f"管理考试笔记失败: {e}")
        return create_response(500, '管理考试笔记失败')


@exam_enhancement_api.route('/api/exam/analysis/<int:user_id>', methods=['GET'])
@require_login
def get_exam_analysis(user_id):
    try:
        current_user_id = session.get('user_id')
        role = session.get('role')

        if role not in ['admin', 'super_admin', 'teacher'] and current_user_id != user_id:
            return create_response(403, '无权查看')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) as total_exams, 
                   AVG(total_score) as avg_score,
                   MAX(total_score) as highest_score,
                   MIN(total_score) as lowest_score
            FROM exam_results
            WHERE user_id = ? AND total_score IS NOT NULL
        ''', (user_id,))
        stats_row = cursor.fetchone()

        cursor.execute('''
            SELECT subject, COUNT(*) as exam_count, AVG(total_score) as avg_score
            FROM exam_results er
            JOIN exams e ON er.exam_id = e.id
            WHERE er.user_id = ? AND er.total_score IS NOT NULL
            GROUP BY subject
            ORDER BY exam_count DESC
        ''', (user_id,))
        subject_stats = []
        for row in cursor.fetchall():
            subject_stats.append({
                'subject': row['subject'],
                'exam_count': row['exam_count'],
                'avg_score': round(row['avg_score'] or 0, 2)
            })

        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as wrong_count
            FROM wrong_answers
            WHERE user_id = ?
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 7
        ''', (user_id,))
        wrong_trend = []
        for row in cursor.fetchall():
            wrong_trend.append({
                'date': row['date'],
                'wrong_count': row['wrong_count']
            })

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
            weak_chapters.append({
                'chapter': row['chapter'],
                'wrong_count': row['wrong_count']
            })

        conn.close()

        return create_response(200, 'success', {
            'stats': {
                'total_exams': stats_row['total_exams'] or 0,
                'avg_score': round(stats_row['avg_score'] or 0, 2),
                'highest_score': stats_row['highest_score'] or 0,
                'lowest_score': stats_row['lowest_score'] or 0
            },
            'subject_stats': subject_stats,
            'wrong_trend': wrong_trend,
            'weak_chapters': weak_chapters
        })

    except Exception as e:
        logger.error(f"获取考试分析失败: {e}")
        return create_response(500, '获取考试分析失败')


@exam_enhancement_api.route('/api/exam/compare', methods=['POST'])
@require_login
def compare_exams():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        exam_id_1 = data.get('exam_id_1')
        exam_id_2 = data.get('exam_id_2')

        if not exam_id_1 or not exam_id_2:
            return create_response(400, '缺少必要参数')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT total_score FROM exam_results WHERE user_id = ? AND exam_id = ?', (user_id, exam_id_1))
        score_1 = cursor.fetchone()
        cursor.execute('SELECT total_score FROM exam_results WHERE user_id = ? AND exam_id = ?', (user_id, exam_id_2))
        score_2 = cursor.fetchone()

        if not score_1 or not score_2:
            conn.close()
            return create_response(400, '考试成绩不存在')

        score_diff = score_2['total_score'] - score_1['total_score']

        cursor.execute('SELECT title, subject FROM exams WHERE id = ?', (exam_id_1,))
        exam_1_info = cursor.fetchone()
        cursor.execute('SELECT title, subject FROM exams WHERE id = ?', (exam_id_2,))
        exam_2_info = cursor.fetchone()

        analysis = ""
        if score_diff > 0:
            analysis = f"相比{exam_1_info['title']}，{exam_2_info['title']}成绩提升了{score_diff}分"
        elif score_diff < 0:
            analysis = f"相比{exam_1_info['title']}，{exam_2_info['title']}成绩下降了{abs(score_diff)}分"
        else:
            analysis = "两次考试成绩相同"

        cursor.execute('INSERT INTO exam_comparisons (user_id, exam_id_1, exam_id_2, score_diff, analysis) VALUES (?, ?, ?, ?, ?)',
                     (user_id, exam_id_1, exam_id_2, score_diff, analysis))
        conn.commit()
        conn.close()

        return create_response(200, '考试对比完成', {
            'exam_1': {
                'id': exam_id_1,
                'title': exam_1_info['title'],
                'subject': exam_1_info['subject'],
                'score': score_1['total_score']
            },
            'exam_2': {
                'id': exam_id_2,
                'title': exam_2_info['title'],
                'subject': exam_2_info['subject'],
                'score': score_2['total_score']
            },
            'score_diff': score_diff,
            'analysis': analysis
        })

    except Exception as e:
        logger.error(f"考试对比失败: {e}")
        return create_response(500, '考试对比失败')