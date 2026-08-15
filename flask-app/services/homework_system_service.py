#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 作业与练习管理服务 (v15.2.0)
====================================
提供作业发布、提交、批改、统计和练习题库等综合服务。

核心能力：
1. 作业管理 - 发布、编辑、删除作业，作业状态追踪
2. 作业提交 - 学生提交作业，多格式支持
3. 作业批改 - 自动批改+人工批改，评语反馈
4. 作业统计 - 班级作业完成率、正确率统计
5. 练习题库 - 分科目分难度练习题
6. 练习记录 - 做题记录和错题归集
7. 成人作业 - 成人教育作业管理
8. K12作业 - 九年制义务教育作业管理
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'homework_system_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HomeworkSystem')


# ========== 作业配置 ==========

# 作业类型
HOMEWORK_TYPES = {
    'daily': {'name': '日常作业', 'description': '每日课后作业', 'default_deadline_hours': 24},
    'weekly': {'name': '周作业', 'description': '每周总结作业', 'default_deadline_hours': 168},
    'monthly': {'name': '月作业', 'description': '月度综合作业', 'default_deadline_hours': 720},
    'exam_prep': {'name': '考前作业', 'description': '考试复习作业', 'default_deadline_hours': 72},
    'holiday': {'name': '假期作业', 'description': '寒暑假作业', 'default_deadline_hours': 1440},
    'project': {'name': '项目作业', 'description': '项目式学习作业', 'default_deadline_hours': 336}
}

# 作业难度
DIFFICULTY_LEVELS = {
    1: {'name': '简单', 'color': '#52c41a', 'score_weight': 0.8},
    2: {'name': '较易', 'color': '#73d13d', 'score_weight': 0.9},
    3: {'name': '中等', 'color': '#faad14', 'score_weight': 1.0},
    4: {'name': '较难', 'color': '#fa8c16', 'score_weight': 1.1},
    5: {'name': '困难', 'color': '#f5222d', 'score_weight': 1.2}
}

# 作业状态
HOMEWORK_STATUS = {
    'draft': '草稿',
    'published': '已发布',
    'submitting': '提交中',
    'grading': '批改中',
    'completed': '已完成',
    'archived': '已归档'
}

# 提交状态
SUBMISSION_STATUS = {
    'not_submitted': '未提交',
    'submitted': '已提交',
    'late': '迟交',
    'graded': '已批改',
    'resubmitted': '重交',
    'excused': '请假'
}

# 批改方式
GRADING_METHODS = {
    'auto': '自动批改',
    'manual': '人工批改',
    'semi_auto': '半自动批改',
    'peer': '同伴互评'
}

# 题型
QUESTION_TYPES = {
    'single_choice': {'name': '单选题', 'auto_grade': True, 'default_score': 2},
    'multiple_choice': {'name': '多选题', 'auto_grade': True, 'default_score': 3},
    'true_false': {'name': '判断题', 'auto_grade': True, 'default_score': 1},
    'fill_blank': {'name': '填空题', 'auto_grade': True, 'default_score': 2},
    'short_answer': {'name': '简答题', 'auto_grade': False, 'default_score': 5},
    'essay': {'name': '论述题', 'auto_grade': False, 'default_score': 10},
    'calculation': {'name': '计算题', 'auto_grade': False, 'default_score': 8},
    'listening': {'name': '听力题', 'auto_grade': True, 'default_score': 2},
    'reading': {'name': '阅读题', 'auto_grade': False, 'default_score': 5}
}

# 练习模式
PRACTICE_MODES = {
    'random': '随机练习',
    'by_chapter': '按章节练习',
    'by_difficulty': '按难度练习',
    'wrong_questions': '错题重做',
    'exam_mode': '模拟考试',
    'adaptive': '自适应练习'
}


class HomeworkSystemService:
    """作业与练习管理服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS homeworks (
                        homework_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        education_type TEXT NOT NULL,
                        subject TEXT,
                        class_id TEXT,
                        teacher_id INTEGER,
                        homework_type TEXT DEFAULT 'daily',
                        difficulty INTEGER DEFAULT 3,
                        total_score REAL DEFAULT 100,
                        grading_method TEXT DEFAULT 'manual',
                        status TEXT DEFAULT 'draft',
                        publish_time TEXT,
                        deadline TEXT,
                        late_allowed INTEGER DEFAULT 1,
                        late_penalty REAL DEFAULT 0.1,
                        resubmit_allowed INTEGER DEFAULT 0,
                        max_resubmit INTEGER DEFAULT 1,
                        question_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS homework_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        homework_id TEXT NOT NULL,
                        question_id TEXT,
                        question_type TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        options TEXT,
                        correct_answer TEXT,
                        score REAL DEFAULT 10,
                        difficulty INTEGER DEFAULT 3,
                        sort_order INTEGER DEFAULT 0,
                        knowledge_points TEXT,
                        explanation TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS homework_submissions (
                        submission_id TEXT PRIMARY KEY,
                        homework_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        answers TEXT,
                        score REAL,
                        grade_status TEXT DEFAULT 'not_submitted',
                        submitted_at TEXT,
                        first_submitted_at TEXT,
                        graded_at TEXT,
                        graded_by INTEGER,
                        feedback TEXT,
                        comment TEXT,
                        attempt_count INTEGER DEFAULT 0,
                        is_late INTEGER DEFAULT 0,
                        auto_score REAL,
                        manual_score REAL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS practice_questions (
                        question_id TEXT PRIMARY KEY,
                        education_type TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        question_type TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        options TEXT,
                        correct_answer TEXT,
                        difficulty INTEGER DEFAULT 3,
                        chapter TEXT,
                        knowledge_points TEXT,
                        explanation TEXT,
                        tags TEXT,
                        source TEXT,
                        used_count INTEGER DEFAULT 0,
                        correct_count INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS practice_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        question_id TEXT NOT NULL,
                        user_answer TEXT,
                        is_correct INTEGER,
                        score REAL,
                        time_spent_seconds INTEGER,
                        practice_mode TEXT,
                        subject TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wrong_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        question_id TEXT NOT NULL,
                        subject TEXT,
                        question_type TEXT,
                        wrong_count INTEGER DEFAULT 1,
                        last_wrong_at TEXT,
                        mastered INTEGER DEFAULT 0,
                        notes TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS homework_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        homework_id TEXT NOT NULL UNIQUE,
                        total_students INTEGER DEFAULT 0,
                        submitted_count INTEGER DEFAULT 0,
                        graded_count INTEGER DEFAULT 0,
                        average_score REAL DEFAULT 0,
                        highest_score REAL DEFAULT 0,
                        lowest_score REAL DEFAULT 0,
                        pass_rate REAL DEFAULT 0,
                        completion_rate REAL DEFAULT 0,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('作业与练习服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def create_homework(self, title: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            homework_id = f"hw_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO homeworks (
                            homework_id, title, description, education_type, subject,
                            class_id, teacher_id, homework_type, difficulty, total_score,
                            grading_method, status, publish_time, deadline,
                            late_allowed, late_penalty, resubmit_allowed, max_resubmit,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        homework_id, title, kwargs.get('description'), education_type,
                        kwargs.get('subject'), kwargs.get('class_id'), kwargs.get('teacher_id'),
                        kwargs.get('homework_type', 'daily'), kwargs.get('difficulty', 3),
                        kwargs.get('total_score', 100), kwargs.get('grading_method', 'manual'),
                        kwargs.get('status', 'draft'), kwargs.get('publish_time'),
                        kwargs.get('deadline'), kwargs.get('late_allowed', 1),
                        kwargs.get('late_penalty', 0.1), kwargs.get('resubmit_allowed', 0),
                        kwargs.get('max_resubmit', 1), now, now
                    ))
                    conn.commit()
                    logger.info(f'创建作业: {title} ({homework_id})')
                    return {'success': True, 'homework_id': homework_id, 'title': title}
        except Exception as e:
            logger.error(f'创建作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_question_to_homework(self, homework_id: str, question_type: str,
                                  question_text: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT homework_id FROM homeworks WHERE homework_id = ?', (homework_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '作业不存在'}
                    options = json.dumps(kwargs.get('options'), ensure_ascii=False) if kwargs.get('options') else None
                    kps = json.dumps(kwargs.get('knowledge_points'), ensure_ascii=False) if kwargs.get('knowledge_points') else None
                    cursor.execute('''
                        INSERT INTO homework_questions (
                            homework_id, question_id, question_type, question_text, options,
                            correct_answer, score, difficulty, sort_order, knowledge_points, explanation
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        homework_id, kwargs.get('question_id', f"q_{uuid.uuid4().hex[:8]}"),
                        question_type, question_text, options,
                        kwargs.get('correct_answer'), kwargs.get('score', 10),
                        kwargs.get('difficulty', 3), kwargs.get('sort_order', 0),
                        kps, kwargs.get('explanation')
                    ))
                    cursor.execute('''
                        UPDATE homeworks SET question_count = question_count + 1, updated_at = ? WHERE homework_id = ?
                    ''', (datetime.now().isoformat(), homework_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加题目失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_homework(self, homework_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE homeworks SET status = 'published', publish_time = ?, updated_at = ?
                        WHERE homework_id = ? AND status = 'draft'
                    ''', (now, now, homework_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布作业: {homework_id}')
                        return {'success': True}
                    return {'success': False, 'error': '作业状态不允许发布'}
        except Exception as e:
            logger.error(f'发布作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_homework(self, homework_id: str, student_id: int, answers: dict) -> Dict[str, Any]:
        try:
            submission_id = f"sub_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT deadline, late_allowed, resubmit_allowed, max_resubmit, grading_method FROM homeworks WHERE homework_id = ?', (homework_id,))
                    hw = cursor.fetchone()
                    if not hw:
                        return {'success': False, 'error': '作业不存在'}
                    deadline, late_allowed, resubmit_allowed, max_resubmit, grading_method = hw
                    is_late = 0
                    if deadline and now > deadline:
                        if not late_allowed:
                            return {'success': False, 'error': '已超过截止时间'}
                        is_late = 1
                    cursor.execute('SELECT submission_id, attempt_count FROM homework_submissions WHERE homework_id = ? AND student_id = ?', (homework_id, student_id))
                    existing = cursor.fetchone()
                    if existing:
                        if not resubmit_allowed or existing[1] >= max_resubmit:
                            return {'success': False, 'error': '不允许再次提交'}
                        cursor.execute('''
                            UPDATE homework_submissions SET
                                answers = ?, submitted_at = ?, attempt_count = attempt_count + 1,
                                grade_status = 'submitted', is_late = ?
                            WHERE submission_id = ?
                        ''', (json.dumps(answers, ensure_ascii=False), now, is_late, existing[0]))
                        submission_id = existing[0]
                    else:
                        cursor.execute('''
                            INSERT INTO homework_submissions (
                                submission_id, homework_id, student_id, answers,
                                grade_status, submitted_at, first_submitted_at,
                                attempt_count, is_late
                            ) VALUES (?, ?, ?, ?, 'submitted', ?, ?, 1, ?)
                        ''', (submission_id, homework_id, student_id, json.dumps(answers, ensure_ascii=False),
                              now, now, is_late))
                    auto_score = None
                    if grading_method in ('auto', 'semi_auto'):
                        auto_score = self._auto_grade(homework_id, answers)
                        cursor.execute('UPDATE homework_submissions SET auto_score = ? WHERE submission_id = ?', (auto_score, submission_id))
                        if grading_method == 'auto':
                            cursor.execute('''
                                UPDATE homework_submissions SET
                                    grade_status = 'graded', score = auto_score, graded_at = ?
                                WHERE submission_id = ?
                            ''', (now, submission_id))
                    conn.commit()
                    logger.info(f'学生 {student_id} 提交作业 {homework_id}')
                    return {'success': True, 'submission_id': submission_id, 'auto_score': auto_score}
        except Exception as e:
            logger.error(f'提交作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def _auto_grade(self, homework_id: str, answers: dict) -> float:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, question_type, correct_answer, score
                    FROM homework_questions WHERE homework_id = ? ORDER BY sort_order, id
                ''', (homework_id,))
                questions = cursor.fetchall()
                total_score = 0
                earned_score = 0
                for q in questions:
                    qid, qtype, correct, score = q
                    total_score += score
                    user_ans = answers.get(str(qid), '')
                    if correct and user_ans:
                        if qtype in ('single_choice', 'true_false', 'fill_blank'):
                            if str(user_ans).strip() == str(correct).strip():
                                earned_score += score
                        elif qtype == 'multiple_choice':
                            if sorted(str(user_ans).split(',')) == sorted(str(correct).split(',')):
                                earned_score += score
                return round(earned_score, 2) if total_score > 0 else 0
        except Exception as e:
            logger.error(f'自动批改失败: {e}')
            return 0

    def grade_homework(self, submission_id: str, score: float,
                        feedback: str = None, comment: str = None,
                        graded_by: int = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE homework_submissions SET
                            grade_status = 'graded', score = ?, manual_score = ?,
                            graded_at = ?, graded_by = ?, feedback = ?, comment = ?
                        WHERE submission_id = ?
                    ''', (score, score, now, graded_by, feedback, comment, submission_id))
                    conn.commit()
                    logger.info(f'批改作业: {submission_id}, 得分: {score}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'批改作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_homework(self, homework_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM homeworks WHERE homework_id = ?', (homework_id,))
                row = cursor.fetchone()
                if row:
                    hw = dict(row)
                    cursor.execute('SELECT * FROM homework_questions WHERE homework_id = ? ORDER BY sort_order, id', (homework_id,))
                    questions = [dict(q) for q in cursor.fetchall()]
                    hw['questions'] = questions
                    return hw
                return None
        except Exception as e:
            logger.error(f'获取作业信息失败: {e}')
            return None

    def list_homeworks(self, education_type: str = None, subject: str = None,
                       class_id: str = None, status: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM homeworks WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if class_id:
                    query += ' AND class_id = ?'
                    params.append(class_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                rows = cursor.fetchall()
                homeworks = [dict(r) for r in rows]
                return {'success': True, 'homeworks': homeworks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取作业列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM homework_submissions WHERE submission_id = ?', (submission_id,))
                row = cursor.fetchone()
                if row:
                    sub = dict(row)
                    if sub.get('answers'):
                        sub['answers'] = json.loads(sub['answers'])
                    return sub
                return None
        except Exception as e:
            logger.error(f'获取提交信息失败: {e}')
            return None

    def get_homework_submissions(self, homework_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT hs.* FROM homework_submissions hs
                    WHERE hs.homework_id = ? ORDER BY hs.submitted_at DESC
                ''', (homework_id,))
                submissions = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'submissions': submissions, 'count': len(submissions)}
        except Exception as e:
            logger.error(f'获取作业提交列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_homework_status(self, homework_id: str, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM homework_submissions
                    WHERE homework_id = ? AND student_id = ?
                ''', (homework_id, student_id))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'submission': dict(row), 'exists': True}
                return {'success': True, 'exists': False, 'status': 'not_submitted'}
        except Exception as e:
            logger.error(f'获取学生作业状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_practice_question(self, education_type: str, subject: str,
                               question_type: str, question_text: str, **kwargs) -> Dict[str, Any]:
        try:
            question_id = f"pq_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            options = json.dumps(kwargs.get('options'), ensure_ascii=False) if kwargs.get('options') else None
            kps = json.dumps(kwargs.get('knowledge_points'), ensure_ascii=False) if kwargs.get('knowledge_points') else None
            tags = json.dumps(kwargs.get('tags'), ensure_ascii=False) if kwargs.get('tags') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO practice_questions (
                            question_id, education_type, subject, question_type, question_text,
                            options, correct_answer, difficulty, chapter, knowledge_points,
                            explanation, tags, source, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        question_id, education_type, subject, question_type, question_text,
                        options, kwargs.get('correct_answer'), kwargs.get('difficulty', 3),
                        kwargs.get('chapter'), kps, kwargs.get('explanation'), tags,
                        kwargs.get('source'), now
                    ))
                    conn.commit()
                    logger.info(f'添加练习题: {question_id}')
                    return {'success': True, 'question_id': question_id}
        except Exception as e:
            logger.error(f'添加练习题失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_practice_questions(self, education_type: str = None, subject: str = None,
                                difficulty: int = None, chapter: str = None,
                                limit: int = 10, mode: str = 'random') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM practice_questions WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if difficulty:
                    query += ' AND difficulty = ?'
                    params.append(difficulty)
                if chapter:
                    query += ' AND chapter = ?'
                    params.append(chapter)
                if mode == 'random':
                    query += ' ORDER BY RANDOM()'
                else:
                    query += ' ORDER BY created_at DESC'
                query += ' LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                questions = [dict(q) for q in cursor.fetchall()]
                return {'success': True, 'questions': questions, 'count': len(questions)}
        except Exception as e:
            logger.error(f'获取练习题失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_practice(self, student_id: int, question_id: str, user_answer: str,
                         is_correct: bool, score: float, time_spent: int = None,
                         practice_mode: str = None, subject: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO practice_records (
                            student_id, question_id, user_answer, is_correct, score,
                            time_spent_seconds, practice_mode, subject, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (student_id, question_id, user_answer, 1 if is_correct else 0,
                          score, time_spent, practice_mode, subject, now))
                    if is_correct:
                        cursor.execute('''
                            UPDATE practice_questions SET used_count = used_count + 1,
                                correct_count = correct_count + 1 WHERE question_id = ?
                        ''', (question_id,))
                    else:
                        cursor.execute('''
                            UPDATE practice_questions SET used_count = used_count + 1 WHERE question_id = ?
                        ''', (question_id,))
                        cursor.execute('''
                            INSERT INTO wrong_questions (student_id, question_id, subject, question_type, wrong_count, last_wrong_at)
                            VALUES (?, ?, ?, (SELECT question_type FROM practice_questions WHERE question_id = ?), 1, ?)
                            ON CONFLICT(student_id, question_id) DO UPDATE SET
                                wrong_count = wrong_count + 1, last_wrong_at = ?, mastered = 0
                        ''', (student_id, question_id, subject, question_id, now, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录练习失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_wrong_questions(self, student_id: int, subject: str = None,
                             mastered: int = 0, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT wq.*, pq.question_text, pq.question_type, pq.difficulty, pq.chapter
                    FROM wrong_questions wq
                    LEFT JOIN practice_questions pq ON wq.question_id = pq.question_id
                    WHERE wq.student_id = ? AND wq.mastered = ?
                '''
                params = [student_id, mastered]
                if subject:
                    query += ' AND wq.subject = ?'
                    params.append(subject)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY wq.last_wrong_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                questions = [dict(q) for q in cursor.fetchall()]
                return {'success': True, 'questions': questions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取错题列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_homework_stats(self, homework_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM homework_stats WHERE homework_id = ?', (homework_id,))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'stats': dict(row)}
                cursor.execute('''
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN grade_status IN ('submitted', 'graded') THEN 1 ELSE 0 END) as submitted,
                        SUM(CASE WHEN grade_status = 'graded' THEN 1 ELSE 0 END) as graded,
                        AVG(CASE WHEN grade_status = 'graded' THEN score END) as avg_score,
                        MAX(CASE WHEN grade_status = 'graded' THEN score END) as max_score,
                        MIN(CASE WHEN grade_status = 'graded' THEN score END) as min_score
                    FROM homework_submissions WHERE homework_id = ?
                ''', (homework_id,))
                s = cursor.fetchone()
                return {
                    'success': True,
                    'stats': {
                        'homework_id': homework_id,
                        'total_students': s['total'] or 0,
                        'submitted_count': s['submitted'] or 0,
                        'graded_count': s['graded'] or 0,
                        'average_score': round(s['avg_score'] or 0, 2),
                        'highest_score': s['max_score'] or 0,
                        'lowest_score': s['min_score'] or 0,
                        'completion_rate': round((s['submitted'] or 0) / (s['total'] or 1) * 100, 2)
                    }
                }
        except Exception as e:
            logger.error(f'获取作业统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_practice_stats(self, student_id: int, days: int = 30) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_questions,
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
                        AVG(score) as avg_score,
                        SUM(time_spent_seconds) as total_time,
                        COUNT(DISTINCT DATE(created_at)) as active_days
                    FROM practice_records
                    WHERE student_id = ? AND created_at >= ?
                ''', (student_id, start_date))
                s = cursor.fetchone()
                total = s[0] or 0
                correct = s[1] or 0
                cursor.execute('''
                    SELECT subject, COUNT(*), SUM(is_correct)
                    FROM practice_records
                    WHERE student_id = ? AND created_at >= ?
                    GROUP BY subject
                ''', (student_id, start_date))
                by_subject = {}
                for row in cursor.fetchall():
                    subj, cnt, cor = row
                    by_subject[subj] = {
                        'total': cnt,
                        'correct': cor or 0,
                        'accuracy': round((cor or 0) / cnt * 100, 2) if cnt > 0 else 0
                    }
                return {
                    'success': True,
                    'stats': {
                        'total_questions': total,
                        'correct_count': correct,
                        'accuracy': round(correct / total * 100, 2) if total > 0 else 0,
                        'average_score': round(s[2] or 0, 2),
                        'total_time_minutes': round((s[3] or 0) / 60, 1),
                        'active_days': s[4] or 0,
                        'by_subject': by_subject
                    }
                }
        except Exception as e:
            logger.error(f'获取学生练习统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_wrong_mastered(self, student_id: int, question_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE wrong_questions SET mastered = 1
                        WHERE student_id = ? AND question_id = ?
                    ''', (student_id, question_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'标记错题掌握失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_homework_list(self, student_id: int, education_type: str = None,
                                   status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT h.*, hs.grade_status, hs.score, hs.submitted_at, hs.submission_id
                    FROM homeworks h
                    LEFT JOIN homework_submissions hs ON h.homework_id = hs.homework_id AND hs.student_id = ?
                    WHERE 1=1
                '''
                params = [student_id]
                if education_type:
                    query += ' AND h.education_type = ?'
                    params.append(education_type)
                if status:
                    if status == 'not_submitted':
                        query += ' AND (hs.grade_status IS NULL OR hs.grade_status = ?)'
                        params.append('not_submitted')
                    else:
                        query += ' AND hs.grade_status = ?'
                        params.append(status)
                query += ' ORDER BY h.created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                homeworks = [dict(h) for h in cursor.fetchall()]
                return {'success': True, 'homeworks': homeworks, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学生作业列表失败: {e}')
            return {'success': False, 'error': str(e)}
