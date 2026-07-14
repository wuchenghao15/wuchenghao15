# -*- coding: utf-8 -*-
"""
作业系统API - 作业布置、作业提交、AI批改、作业统计
"""

from flask import Blueprint, jsonify, request, session
from app.middlewares.permission_decorators import require_login, require_admin
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

homework_system_api = Blueprint('homework_system_api', __name__)

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
            CREATE TABLE IF NOT EXISTS homework_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT,
                grade TEXT,
                total_score REAL DEFAULT 100,
                deadline TEXT,
                status TEXT DEFAULT 'active',
                created_by INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homework_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'essay',
                score REAL DEFAULT 0,
                correct_answer TEXT,
                hints TEXT,
                order_num INTEGER DEFAULT 0,
                FOREIGN KEY (homework_id) REFERENCES homework_assignments(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homework_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                submission_time TEXT,
                status TEXT DEFAULT 'pending',
                score REAL,
                feedback TEXT,
                ai_feedback TEXT,
                graded_at TEXT,
                FOREIGN KEY (homework_id) REFERENCES homework_assignments(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(homework_id, user_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                score REAL DEFAULT 0,
                ai_feedback TEXT,
                FOREIGN KEY (submission_id) REFERENCES homework_submissions(id),
                FOREIGN KEY (question_id) REFERENCES homework_questions(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homework_id INTEGER NOT NULL,
                total_submissions INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0,
                highest_score REAL DEFAULT 0,
                lowest_score REAL DEFAULT 0,
                pass_rate REAL DEFAULT 0,
                FOREIGN KEY (homework_id) REFERENCES homework_assignments(id),
                UNIQUE(homework_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homework_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                FOREIGN KEY (homework_id) REFERENCES homework_assignments(id),
                FOREIGN KEY (group_id) REFERENCES user_groups(id),
                UNIQUE(homework_id, group_id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✓ 作业系统表创建完成")
    except Exception as e:
        logger.error(f"✗ 创建作业系统表失败: {e}")


create_tables()


@homework_system_api.route('/api/homework', methods=['GET'])
@require_login
def get_homework_list():
    try:
        user_id = session.get('user_id')
        role = session.get('role')
        subject = request.args.get('subject', '')
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        conn = get_db_connection()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if role in ['admin', 'super_admin', 'teacher']:
            if subject:
                where_clauses.append('ha.subject = ?')
                params.append(subject)
            if status:
                where_clauses.append('ha.status = ?')
                params.append(status)
        else:
            cursor.execute('SELECT group_id FROM user_group_members WHERE user_id = ?', (user_id,))
            user_groups = [str(row['group_id']) for row in cursor.fetchall()]

            if user_groups:
                where_clauses.append('hg.group_id IN ({})'.format(','.join(['?'] * len(user_groups))))
                params.extend(user_groups)
            where_clauses.append('ha.status = "active"')
            where_clauses.append('ha.deadline > ?')
            params.append(datetime.now().isoformat())

        where_sql = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''
        join_sql = ' LEFT JOIN homework_groups hg ON ha.id = hg.homework_id' if role not in ['admin', 'super_admin', 'teacher'] else ''

        cursor.execute(f'''
            SELECT COUNT(DISTINCT ha.id) FROM homework_assignments ha {join_sql} {where_sql}
        ''', params)
        total = cursor.fetchone()[0] or 0

        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT ha.id, ha.title, ha.description, ha.subject, ha.grade, ha.total_score, 
                   ha.deadline, ha.status, ha.created_by, u.username as created_name, ha.created_at,
                   COUNT(DISTINCT hs.submission_id) as submission_count
            FROM homework_assignments ha
            JOIN users u ON ha.created_by = u.id
            LEFT JOIN homework_submissions hs ON ha.id = hs.homework_id
            {join_sql}
            {where_sql}
            GROUP BY ha.id
            ORDER BY ha.created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

        homework_list = []
        for row in cursor.fetchall():
            cursor.execute('SELECT submission_id, status, final_score FROM homework_submissions WHERE homework_id = ? AND student_id = ?', (row['id'], user_id))
            submission = cursor.fetchone()

            homework_list.append({
                'id': row['id'],
                'title': row['title'],
                'description': row['description'] or '',
                'subject': row['subject'] or '',
                'grade': row['grade'] or '',
                'total_score': row['total_score'] or 100,
                'deadline': row['deadline'],
                'status': row['status'],
                'created_by': row['created_by'],
                'created_name': row['created_name'],
                'submission_count': row['submission_count'] or 0,
                'created_at': row['created_at'],
                'submitted': submission is not None,
                'submission_status': submission['status'] if submission else None,
                'score': submission['final_score'] if submission else None
            })
        conn.close()
        return create_response(200, 'success', {
            'homework': homework_list,
            'total': total,
            'page': page,
            'per_page': per_page
        })

    except Exception as e:
        logger.error(f"获取作业列表失败: {e}")
        return create_response(500, '获取作业列表失败')


@homework_system_api.route('/api/homework/<int:homework_id>', methods=['GET'])
@require_login
def get_homework_detail(homework_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ha.id, ha.title, ha.description, ha.subject, ha.grade, ha.total_score, 
                   ha.deadline, ha.status, ha.created_by, u.username as created_name, ha.created_at
            FROM homework_assignments ha
            JOIN users u ON ha.created_by = u.id
            WHERE ha.id = ?
        ''', (homework_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '作业不存在')

        cursor.execute('''
            SELECT id, question_text, question_type, score, correct_answer, hints, order_num
            FROM homework_questions
            WHERE homework_id = ?
            ORDER BY order_num
        ''', (homework_id,))
        questions = []
        for q_row in cursor.fetchall():
            questions.append({
                'id': q_row['id'],
                'question_text': q_row['question_text'],
                'question_type': q_row['question_type'],
                'score': q_row['score'] or 0,
                'correct_answer': q_row['correct_answer'] or '',
                'hints': q_row['hints'] or '',
                'order_num': q_row['order_num']
            })

        cursor.execute('SELECT id, status, score, feedback, ai_feedback, submission_time FROM homework_submissions WHERE homework_id = ? AND user_id = ?', (homework_id, user_id))
        submission = cursor.fetchone()

        answers = []
        if submission:
            cursor.execute('''
                SELECT ha.id, ha.question_id, ha.answer_text, ha.score, ha.ai_feedback,
                       hq.question_text
                FROM homework_answers ha
                JOIN homework_questions hq ON ha.question_id = hq.id
                WHERE ha.submission_id = ?
            ''', (submission['id'],))
            for a_row in cursor.fetchall():
                answers.append({
                    'id': a_row['id'],
                    'question_id': a_row['question_id'],
                    'question_text': a_row['question_text'],
                    'answer_text': a_row['answer_text'] or '',
                    'score': a_row['score'] or 0,
                    'ai_feedback': a_row['ai_feedback'] or ''
                })

        conn.close()
        return create_response(200, 'success', {
            'id': row['id'],
            'title': row['title'],
            'description': row['description'] or '',
            'subject': row['subject'] or '',
            'grade': row['grade'] or '',
            'total_score': row['total_score'] or 100,
            'deadline': row['deadline'],
            'status': row['status'],
            'created_by': row['created_by'],
            'created_name': row['created_name'],
            'created_at': row['created_at'],
            'questions': questions,
            'submission': {
                'id': submission['id'],
                'status': submission['status'],
                'score': submission['score'],
                'feedback': submission['feedback'] or '',
                'ai_feedback': submission['ai_feedback'] or '',
                'submission_time': submission['submission_time'],
                'answers': answers
            } if submission else None
        })

    except Exception as e:
        logger.error(f"获取作业详情失败: {e}")
        return create_response(500, '获取作业详情失败')


@homework_system_api.route('/api/homework', methods=['POST'])
@require_admin
def create_homework():
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        title = data.get('title', '')
        description = data.get('description', '')
        subject = data.get('subject', '')
        grade = data.get('grade', '')
        total_score = data.get('total_score', 100)
        deadline = data.get('deadline', '')
        questions = data.get('questions', [])
        group_ids = data.get('group_ids', [])

        if not title:
            return create_response(400, '作业标题不能为空')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO homework_assignments (title, description, subject, grade, total_score, deadline, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (title, description, subject, grade, total_score, deadline, user_id))
        homework_id = cursor.lastrowid

        for i, question in enumerate(questions):
            cursor.execute('INSERT INTO homework_questions (homework_id, question_text, question_type, score, correct_answer, hints, order_num) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         (homework_id, question.get('question_text', ''), question.get('question_type', 'essay'), question.get('score', 0), question.get('correct_answer', ''), question.get('hints', ''), i))

        for group_id in group_ids:
            cursor.execute('INSERT OR IGNORE INTO homework_groups (homework_id, group_id) VALUES (?, ?)', (homework_id, group_id))

        conn.commit()
        conn.close()

        return create_response(201, '作业创建成功', {'homework_id': homework_id})

    except Exception as e:
        logger.error(f"创建作业失败: {e}")
        return create_response(500, '创建作业失败')


@homework_system_api.route('/api/homework/<int:homework_id>', methods=['PUT', 'DELETE'])
@require_admin
def manage_homework(homework_id):
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
            if 'grade' in data:
                updates.append('grade = ?')
                params.append(data['grade'])
            if 'total_score' in data:
                updates.append('total_score = ?')
                params.append(data['total_score'])
            if 'deadline' in data:
                updates.append('deadline = ?')
                params.append(data['deadline'])
            if 'status' in data:
                updates.append('status = ?')
                params.append(data['status'])

            if not updates:
                conn.close()
                return create_response(400, '没有可更新的字段')

            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(homework_id)

            cursor.execute(f'UPDATE homework_assignments SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return create_response(200, '作业更新成功')

        elif request.method == 'DELETE':
            cursor.execute('DELETE FROM homework_groups WHERE homework_id = ?', (homework_id,))
            cursor.execute('DELETE FROM homework_answers WHERE submission_id IN (SELECT id FROM homework_submissions WHERE homework_id = ?)', (homework_id,))
            cursor.execute('DELETE FROM homework_submissions WHERE homework_id = ?', (homework_id,))
            cursor.execute('DELETE FROM homework_questions WHERE homework_id = ?', (homework_id,))
            cursor.execute('DELETE FROM homework_assignments WHERE id = ?', (homework_id,))
            conn.commit()
            conn.close()
            return create_response(200, '作业已删除')

    except Exception as e:
        logger.error(f"作业管理操作失败: {e}")
        return create_response(500, '作业管理操作失败')


@homework_system_api.route('/api/homework/<int:homework_id>/submit', methods=['POST'])
@require_login
def submit_homework(homework_id):
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        answers = data.get('answers', [])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id, deadline, total_score FROM homework_assignments WHERE id = ?', (homework_id,))
        homework = cursor.fetchone()
        if not homework:
            conn.close()
            return create_response(404, '作业不存在')

        if homework['deadline'] and datetime.now().isoformat() > homework['deadline']:
            conn.close()
            return create_response(400, '作业已截止')

        cursor.execute('SELECT id FROM homework_submissions WHERE homework_id = ? AND user_id = ?', (homework_id, user_id))
        if cursor.fetchone():
            conn.close()
            return create_response(400, '已提交过该作业')

        cursor.execute('INSERT INTO homework_submissions (homework_id, user_id, submission_time, status) VALUES (?, ?, ?, ?)',
                     (homework_id, user_id, datetime.now().isoformat(), 'pending'))
        submission_id = cursor.lastrowid

        for answer in answers:
            cursor.execute('INSERT INTO homework_answers (submission_id, question_id, answer_text) VALUES (?, ?, ?)',
                         (submission_id, answer.get('question_id'), answer.get('answer_text', '')))

        ai_feedback = generate_ai_feedback(homework_id, submission_id, answers)
        cursor.execute('UPDATE homework_submissions SET ai_feedback = ? WHERE id = ?', (ai_feedback, submission_id))

        conn.commit()
        conn.close()

        return create_response(200, '作业提交成功', {'submission_id': submission_id})

    except Exception as e:
        logger.error(f"提交作业失败: {e}")
        return create_response(500, '提交作业失败')


def generate_ai_feedback(homework_id, submission_id, answers):
    feedback = []
    for answer in answers:
        feedback.append({
            'question_id': answer.get('question_id'),
            'feedback': 'AI正在分析您的答案，请等待教师批改。',
            'suggestion': '建议仔细检查答案，参考相关知识点进行复习。'
        })
    return json.dumps(feedback)


@homework_system_api.route('/api/homework/<int:homework_id>/grade', methods=['POST'])
@require_admin
def grade_homework(homework_id):
    try:
        data = request.get_json() or {}
        submissions = data.get('submissions', [])

        conn = get_db_connection()
        cursor = conn.cursor()

        for submission in submissions:
            submission_id = submission.get('submission_id')
            total_score = 0
            answer_scores = submission.get('answers', [])

            for ans_score in answer_scores:
                question_id = ans_score.get('question_id')
                score = ans_score.get('score', 0)
                ai_feedback = ans_score.get('ai_feedback', '')

                cursor.execute('UPDATE homework_answers SET score = ?, ai_feedback = ? WHERE submission_id = ? AND question_id = ?',
                             (score, ai_feedback, submission_id, question_id))
                total_score += score

            cursor.execute('UPDATE homework_submissions SET score = ?, status = "graded", graded_at = ? WHERE id = ?',
                         (total_score, datetime.now().isoformat(), submission_id))

        update_homework_stats(homework_id, cursor)
        conn.commit()
        conn.close()

        return create_response(200, '作业批改完成')

    except Exception as e:
        logger.error(f"批改作业失败: {e}")
        return create_response(500, '批改作业失败')


def update_homework_stats(homework_id, cursor):
    cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE homework_id = ? AND status = "graded"', (homework_id,))
    total_submissions = cursor.fetchone()[0] or 0

    if total_submissions > 0:
        cursor.execute('SELECT AVG(score), MAX(score), MIN(score) FROM homework_submissions WHERE homework_id = ? AND status = "graded"', (homework_id,))
        stats_row = cursor.fetchone()
        avg_score = stats_row[0] or 0
        highest_score = stats_row[1] or 0
        lowest_score = stats_row[2] or 0

        cursor.execute('SELECT total_score FROM homework_assignments WHERE id = ?', (homework_id,))
        total_score = cursor.fetchone()[0] or 100
        pass_score = total_score * 0.6

        cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE homework_id = ? AND status = "graded" AND score >= ?', (homework_id, pass_score))
        passed_count = cursor.fetchone()[0] or 0
        pass_rate = (passed_count / total_submissions) * 100 if total_submissions > 0 else 0

        cursor.execute('''
            INSERT OR REPLACE INTO homework_stats (homework_id, total_submissions, avg_score, highest_score, lowest_score, pass_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (homework_id, total_submissions, avg_score, highest_score, lowest_score, pass_rate))


@homework_system_api.route('/api/homework/<int:homework_id>/stats', methods=['GET'])
@require_admin
def get_homework_stats(homework_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM homework_stats WHERE homework_id = ?', (homework_id,))
        stats = cursor.fetchone()

        cursor.execute('SELECT title, total_score FROM homework_assignments WHERE id = ?', (homework_id,))
        homework = cursor.fetchone()

        if not stats:
            cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE homework_id = ? AND status = "graded"', (homework_id,))
            total_submissions = cursor.fetchone()[0] or 0

            if total_submissions > 0:
                cursor.execute('SELECT AVG(score), MAX(score), MIN(score) FROM homework_submissions WHERE homework_id = ? AND status = "graded"', (homework_id,))
                stats_row = cursor.fetchone()
                avg_score = stats_row[0] or 0
                highest_score = stats_row[1] or 0
                lowest_score = stats_row[2] or 0

                pass_score = (homework['total_score'] or 100) * 0.6
                cursor.execute('SELECT COUNT(*) FROM homework_submissions WHERE homework_id = ? AND status = "graded" AND score >= ?', (homework_id, pass_score))
                passed_count = cursor.fetchone()[0] or 0
                pass_rate = (passed_count / total_submissions) * 100 if total_submissions > 0 else 0

                stats_data = {
                    'total_submissions': total_submissions,
                    'avg_score': round(avg_score, 2),
                    'highest_score': highest_score,
                    'lowest_score': lowest_score,
                    'pass_rate': round(pass_rate, 2)
                }
            else:
                stats_data = {
                    'total_submissions': 0,
                    'avg_score': 0,
                    'highest_score': 0,
                    'lowest_score': 0,
                    'pass_rate': 0
                }
        else:
            stats_data = {
                'total_submissions': stats['total_submissions'] or 0,
                'avg_score': round(stats['avg_score'] or 0, 2),
                'highest_score': stats['highest_score'] or 0,
                'lowest_score': stats['lowest_score'] or 0,
                'pass_rate': round(stats['pass_rate'] or 0, 2)
            }

        conn.close()
        return create_response(200, 'success', {
            'homework_title': homework['title'] if homework else '',
            'total_score': homework['total_score'] if homework else 100,
            'stats': stats_data
        })

    except Exception as e:
        logger.error(f"获取作业统计失败: {e}")
        return create_response(500, '获取作业统计失败')


@homework_system_api.route('/api/homework/submissions/<int:submission_id>', methods=['GET'])
@require_login
def get_submission_detail(submission_id):
    try:
        user_id = session.get('user_id')
        role = session.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT hs.id, hs.homework_id, hs.user_id, u.username, hs.submission_time, 
                   hs.status, hs.score, hs.feedback, hs.ai_feedback, hs.graded_at,
                   ha.title as homework_title
            FROM homework_submissions hs
            JOIN users u ON hs.user_id = u.id
            JOIN homework_assignments ha ON hs.homework_id = ha.id
            WHERE hs.id = ?
        ''', (submission_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return create_response(404, '提交记录不存在')

        if role not in ['admin', 'super_admin', 'teacher'] and row['user_id'] != user_id:
            conn.close()
            return create_response(403, '无权查看')

        cursor.execute('''
            SELECT ha.id, ha.question_id, ha.answer_text, ha.score, ha.ai_feedback,
                   hq.question_text, hq.correct_answer, hq.score as question_score
            FROM homework_answers ha
            JOIN homework_questions hq ON ha.question_id = hq.id
            WHERE ha.submission_id = ?
        ''', (submission_id,))
        answers = []
        for a_row in cursor.fetchall():
            answers.append({
                'id': a_row['id'],
                'question_id': a_row['question_id'],
                'question_text': a_row['question_text'],
                'correct_answer': a_row['correct_answer'] or '',
                'question_score': a_row['question_score'] or 0,
                'answer_text': a_row['answer_text'] or '',
                'score': a_row['score'] or 0,
                'ai_feedback': a_row['ai_feedback'] or ''
            })

        conn.close()
        return create_response(200, 'success', {
            'id': row['id'],
            'homework_id': row['homework_id'],
            'homework_title': row['homework_title'],
            'user_id': row['user_id'],
            'username': row['username'],
            'submission_time': row['submission_time'],
            'status': row['status'],
            'score': row['score'],
            'feedback': row['feedback'] or '',
            'ai_feedback': row['ai_feedback'] or '',
            'graded_at': row['graded_at'],
            'answers': answers
        })

    except Exception as e:
        logger.error(f"获取提交详情失败: {e}")
        return create_response(500, '获取提交详情失败')