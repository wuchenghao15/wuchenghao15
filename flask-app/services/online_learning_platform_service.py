#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 在线学习平台服务 (v15.9.0)
====================================
提供在线课程、直播课堂、录播教学、互动答疑、作业考试等综合在线学习服务。
支持成人教育和K12教育的差异化需求。

核心能力：
1. 课程管理 - 直播课、录播课、混合课、微课管理
2. 直播课堂 - 在线直播、互动白板、屏幕共享、录制
3. 录播课程 - 视频管理、章节编排、断点续播
4. 互动教学 - 答题、投票、讨论、举手、分组
5. 学习进度 - 观看时长、完成度、学习轨迹
6. 在线答疑 - 提问、解答、知识库
7. 作业考试 - 在线作业、自动批改、在线考试
8. 学习社区 - 课程讨论、学习小组、互助
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'online_learning_platform_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OnlineLearning')


# ========== 在线学习平台配置 ==========

# 课程类型
COURSE_TYPES = {
    'live': {'name': '直播课', 'has_live': True},
    'recorded': {'name': '录播课', 'has_live': False},
    'blended': {'name': '混合课', 'has_live': True},
    'micro': {'name': '微课', 'has_live': False},
    'flipped': {'name': '翻转课堂', 'has_live': True},
    'project': {'name': '项目课', 'has_live': False}
}

# 直播状态
LIVE_STATUS = {
    'scheduled': '已安排',
    'live': '直播中',
    'ended': '已结束',
    'cancelled': '已取消',
    'recorded': '已录制'
}

# 互动类型
INTERACTION_TYPES = {
    'qa': {'name': '问答'},
    'poll': {'name': '投票'},
    'discuss': {'name': '讨论'},
    'raise_hand': {'name': '举手'},
    'breakout': {'name': '分组'},
    'whiteboard': {'name': '白板'},
    'screen_share': {'name': '屏幕共享'}
}

# 学习进度状态
PROGRESS_STATUS = {
    'not_started': '未开始',
    'learning': '学习中',
    'completed': '已完成',
    'abandoned': '已放弃'
}

# 答疑状态
QA_STATUS = {
    'open': '待解答',
    'answered': '已解答',
    'closed': '已关闭',
    'pinned': '置顶'
}

# 社区类型
COMMUNITY_TYPES = {
    'course_discussion': {'name': '课程讨论'},
    'study_group': {'name': '学习小组'},
    'peer_tutoring': {'name': '同伴辅导'},
    'knowledge_sharing': {'name': '知识分享'}
}

# 作业类型
ASSIGNMENT_TYPES = {
    'video': {'name': '视频作业', 'auto_grade': False},
    'quiz': {'name': '测验', 'auto_grade': True},
    'written': {'name': '书面', 'auto_grade': False},
    'coding': {'name': '编程', 'auto_grade': True},
    'group': {'name': '团队', 'auto_grade': False},
    'project': {'name': '项目', 'auto_grade': False}
}

# 难度等级
DIFFICULTY_LEVELS = {
    'introductory': {'name': '入门', 'level': 1},
    'beginner': {'name': '初级', 'level': 2},
    'intermediate': {'name': '中级', 'level': 3},
    'advanced': {'name': '高级', 'level': 4},
    'expert': {'name': '专家', 'level': 5}
}


class OnlineLearningPlatformService:
    """在线学习平台服务"""

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
                    CREATE TABLE IF NOT EXISTS online_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_type TEXT NOT NULL,
                        subject TEXT,
                        education_type TEXT,
                        teacher_id TEXT,
                        teacher_name TEXT,
                        grade_level TEXT,
                        description TEXT,
                        cover_image TEXT,
                        difficulty TEXT,
                        total_hours REAL DEFAULT 0,
                        enrolled_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0,
                        rating_count INTEGER DEFAULT 0,
                        price REAL DEFAULT 0,
                        is_free INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'draft',
                        tags TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_chapters (
                        chapter_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        chapter_name TEXT NOT NULL,
                        chapter_order INTEGER DEFAULT 0,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_lessons (
                        lesson_id TEXT PRIMARY KEY,
                        chapter_id TEXT NOT NULL,
                        course_id TEXT NOT NULL,
                        lesson_name TEXT NOT NULL,
                        lesson_order INTEGER DEFAULT 0,
                        lesson_type TEXT,
                        duration_minutes INTEGER DEFAULT 0,
                        video_url TEXT,
                        content TEXT,
                        is_preview INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS live_sessions (
                        session_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        lesson_id TEXT,
                        session_name TEXT NOT NULL,
                        teacher_id TEXT,
                        teacher_name TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        live_status TEXT DEFAULT 'scheduled',
                        stream_url TEXT,
                        record_url TEXT,
                        max_participants INTEGER DEFAULT 100,
                        actual_participants INTEGER DEFAULT 0,
                        is_recorded INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS live_attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        join_time TEXT,
                        leave_time TEXT,
                        duration_minutes INTEGER DEFAULT 0,
                        interaction_count INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        lesson_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        status TEXT DEFAULT 'not_started',
                        progress_percent REAL DEFAULT 0,
                        watch_duration REAL DEFAULT 0,
                        last_position REAL DEFAULT 0,
                        last_learn_time TEXT,
                        completed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interactions (
                        interaction_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        course_id TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        user_id TEXT,
                        user_name TEXT,
                        content TEXT,
                        options TEXT,
                        result TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS online_qa (
                        qa_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        lesson_id TEXT,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        question TEXT NOT NULL,
                        question_type TEXT DEFAULT 'general',
                        status TEXT DEFAULT 'open',
                        answer TEXT,
                        answered_by TEXT,
                        answered_at TEXT,
                        answer_count INTEGER DEFAULT 0,
                        helpful_count INTEGER DEFAULT 0,
                        is_pinned INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS online_assignments (
                        assignment_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        lesson_id TEXT,
                        assignment_name TEXT NOT NULL,
                        assignment_type TEXT NOT NULL,
                        description TEXT,
                        total_score REAL DEFAULT 100,
                        deadline TEXT,
                        auto_grade INTEGER DEFAULT 0,
                        allow_resubmit INTEGER DEFAULT 0,
                        max_attempts INTEGER DEFAULT 1,
                        submit_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assignment_submissions (
                        submission_id TEXT PRIMARY KEY,
                        assignment_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        content TEXT,
                        file_url TEXT,
                        score REAL,
                        feedback TEXT,
                        graded_by TEXT,
                        graded_at TEXT,
                        attempt_number INTEGER DEFAULT 1,
                        submit_time TEXT,
                        status TEXT DEFAULT 'submitted',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_communities (
                        community_id TEXT PRIMARY KEY,
                        community_name TEXT NOT NULL,
                        community_type TEXT NOT NULL,
                        course_id TEXT,
                        creator_id TEXT NOT NULL,
                        creator_name TEXT,
                        description TEXT,
                        member_count INTEGER DEFAULT 1,
                        max_members INTEGER DEFAULT 100,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        community_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        role TEXT DEFAULT 'member',
                        joined_at TEXT,
                        contribution_score REAL DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_posts (
                        post_id TEXT PRIMARY KEY,
                        community_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        title TEXT NOT NULL,
                        content TEXT,
                        post_type TEXT DEFAULT 'discussion',
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        reply_count INTEGER DEFAULT 0,
                        is_pinned INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        enroll_time TEXT,
                        progress_percent REAL DEFAULT 0,
                        last_learn_time TEXT,
                        completed_lessons INTEGER DEFAULT 0,
                        total_lessons INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('在线学习平台服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 课程管理 ==========

    def create_course(self, course_name: str, course_type: str,
                      subject: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"ol_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            tags = kwargs.get('tags')
            tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
            is_free = 1 if kwargs.get('price', 0) == 0 else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO online_courses (
                            course_id, course_name, course_type, subject,
                            education_type, teacher_id, teacher_name, grade_level,
                            description, cover_image, difficulty, total_hours,
                            enrolled_count, rating, rating_count, price, is_free,
                            status, tags, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?, ?)
                    ''', (course_id, course_name, course_type, subject,
                          kwargs.get('education_type', 'common'),
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('grade_level'), kwargs.get('description'),
                          kwargs.get('cover_image'), kwargs.get('difficulty', 'beginner'),
                          kwargs.get('total_hours', 0),
                          kwargs.get('price', 0), is_free,
                          kwargs.get('status', 'draft'), tags_json, now, now))
                    conn.commit()
                    logger.info(f'创建在线课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建在线课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_chapter(self, course_id: str, chapter_name: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            chapter_id = f"chp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM course_chapters WHERE course_id = ?', (course_id,))
                    chapter_order = cursor.fetchone()[0] + 1
                    cursor.execute('''
                        INSERT INTO course_chapters (
                            chapter_id, course_id, chapter_name, chapter_order,
                            description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (chapter_id, course_id, chapter_name,
                          kwargs.get('chapter_order', chapter_order),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'添加章节: {chapter_name} ({chapter_id})')
                    return {'success': True, 'chapter_id': chapter_id}
        except Exception as e:
            logger.error(f'添加章节失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_lesson(self, chapter_id: str, lesson_name: str,
                   lesson_type: str, **kwargs) -> Dict[str, Any]:
        try:
            lesson_id = f"lsn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            course_id = kwargs.get('course_id')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if not course_id:
                        cursor.execute('SELECT course_id FROM course_chapters WHERE chapter_id = ?', (chapter_id,))
                        row = cursor.fetchone()
                        if row:
                            course_id = row[0]
                    cursor.execute('SELECT COUNT(*) FROM course_lessons WHERE chapter_id = ?', (chapter_id,))
                    lesson_order = cursor.fetchone()[0] + 1
                    cursor.execute('''
                        INSERT INTO course_lessons (
                            lesson_id, chapter_id, course_id, lesson_name,
                            lesson_order, lesson_type, duration_minutes, video_url,
                            content, is_preview, view_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''', (lesson_id, chapter_id, course_id, lesson_name,
                          kwargs.get('lesson_order', lesson_order), lesson_type,
                          kwargs.get('duration_minutes', 0),
                          kwargs.get('video_url'), kwargs.get('content'),
                          kwargs.get('is_preview', 0), now, now))
                    conn.commit()
                    logger.info(f'添加课时: {lesson_name} ({lesson_id})')
                    return {'success': True, 'lesson_id': lesson_id}
        except Exception as e:
            logger.error(f'添加课时失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course(self, course_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM online_courses WHERE course_id = ?', (course_id,))
                course_row = cursor.fetchone()
                if not course_row:
                    return {'success': False, 'error': '课程不存在'}
                course = dict(course_row)
                if course.get('tags'):
                    try:
                        course['tags'] = json.loads(course['tags'])
                    except (ValueError, TypeError):
                        pass
                cursor.execute('SELECT * FROM course_chapters WHERE course_id = ? ORDER BY chapter_order', (course_id,))
                chapters = []
                for ch in cursor.fetchall():
                    chapter = dict(ch)
                    cursor.execute('SELECT * FROM course_lessons WHERE chapter_id = ? ORDER BY lesson_order', (chapter['chapter_id'],))
                    chapter['lessons'] = [dict(l) for l in cursor.fetchall()]
                    chapters.append(chapter)
                course['chapters'] = chapters
                return {'success': True, 'course': course}
        except Exception as e:
            logger.error(f'获取课程详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_courses(self, page: int = 1, page_size: int = 20,
                     **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM online_courses WHERE 1=1'
                params = []
                if filters.get('course_type'):
                    query += ' AND course_type = ?'
                    params.append(filters['course_type'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('subject'):
                    query += ' AND subject = ?'
                    params.append(filters['subject'])
                if filters.get('difficulty'):
                    query += ' AND difficulty = ?'
                    params.append(filters['difficulty'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_course(self, course_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM online_courses WHERE course_id = ?', (course_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '课程不存在'}
                    allowed = ['course_name', 'course_type', 'subject', 'education_type',
                               'teacher_id', 'teacher_name', 'grade_level', 'description',
                               'cover_image', 'difficulty', 'total_hours', 'price', 'status']
                    sets = []
                    params = []
                    for k in allowed:
                        if k in kwargs:
                            sets.append(f'{k} = ?')
                            params.append(kwargs[k])
                    if 'tags' in kwargs:
                        sets.append('tags = ?')
                        params.append(json.dumps(kwargs['tags'], ensure_ascii=False))
                    if kwargs.get('price', None) is not None:
                        sets.append('is_free = ?')
                        params.append(1 if kwargs['price'] == 0 else 0)
                    if not sets:
                        return {'success': False, 'error': '无可更新字段'}
                    sets.append('updated_at = ?')
                    params.append(now)
                    params.append(course_id)
                    cursor.execute(f'UPDATE online_courses SET {", ".join(sets)} WHERE course_id = ?', params)
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新课程失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 直播课堂 ==========

    def create_live_session(self, course_id: str, session_name: str,
                            start_time: str, end_time: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"lvs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO live_sessions (
                            session_id, course_id, lesson_id, session_name,
                            teacher_id, teacher_name, start_time, end_time,
                            live_status, stream_url, record_url, max_participants,
                            actual_participants, is_recorded, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?, 0, ?, ?, ?)
                    ''', (session_id, course_id, kwargs.get('lesson_id'),
                          session_name, kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), start_time, end_time,
                          kwargs.get('stream_url'), kwargs.get('record_url'),
                          kwargs.get('max_participants', 100),
                          kwargs.get('is_recorded', 1), now, now))
                    conn.commit()
                    logger.info(f'创建直播场次: {session_name} ({session_id})')
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'创建直播场次失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_live_session(self, session_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE live_sessions SET live_status = 'live', updated_at = ? WHERE session_id = ? AND live_status = 'scheduled'",
                                 (now, session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'开始直播: {session_id}')
                        return {'success': True, 'status': 'live'}
                    return {'success': False, 'error': '直播场次状态不允许开始'}
        except Exception as e:
            logger.error(f'开始直播失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_live_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_url = kwargs.get('record_url')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    new_status = 'recorded' if record_url else 'ended'
                    cursor.execute('''
                        UPDATE live_sessions
                        SET live_status = ?, end_time = ?, record_url = COALESCE(?, record_url),
                            is_recorded = ?, updated_at = ?
                        WHERE session_id = ? AND live_status = 'live'
                    ''', (new_status, kwargs.get('end_time', now), record_url,
                          1 if record_url else 0, now, session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'结束直播: {session_id} -> {new_status}')
                        return {'success': True, 'status': new_status, 'record_url': record_url}
                    return {'success': False, 'error': '直播场次不在直播中'}
        except Exception as e:
            logger.error(f'结束直播失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_attendance(self, session_id: str, user_id: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT actual_participants, max_participants, live_status FROM live_sessions WHERE session_id = ?', (session_id,))
                    session = cursor.fetchone()
                    if not session:
                        return {'success': False, 'error': '直播场次不存在'}
                    cursor.execute('SELECT id FROM live_attendance WHERE session_id = ? AND user_id = ? AND leave_time IS NULL',
                                 (session_id, user_id))
                    existing = cursor.fetchone()
                    if existing:
                        return {'success': False, 'error': '用户已签到且未签退'}
                    cursor.execute('''
                        INSERT INTO live_attendance (
                            session_id, user_id, user_name, join_time,
                            leave_time, duration_minutes, interaction_count, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (session_id, user_id, kwargs.get('user_name'),
                          kwargs.get('join_time', now), kwargs.get('leave_time'),
                          kwargs.get('duration_minutes', 0),
                          kwargs.get('interaction_count', 0), now))
                    if session[2] == 'live':
                        new_count = session[0] + 1
                        cursor.execute('UPDATE live_sessions SET actual_participants = ?, updated_at = ? WHERE session_id = ?',
                                     (new_count, now, session_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_live_session(self, session_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM live_sessions WHERE session_id = ?', (session_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '直播场次不存在'}
                session = dict(row)
                cursor.execute('SELECT COUNT(*) as cnt, COALESCE(SUM(duration_minutes), 0) as total_dur FROM live_attendance WHERE session_id = ?',
                             (session_id,))
                stats = cursor.fetchone()
                session['attendance_count'] = stats['cnt']
                session['total_duration'] = stats['total_dur']
                return {'success': True, 'session': session}
        except Exception as e:
            logger.error(f'获取直播详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习进度 ==========

    def update_progress(self, course_id: str, lesson_id: str,
                        user_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            progress_percent = kwargs.get('progress_percent', 0)
            status = 'completed' if progress_percent >= 100 else 'learning'
            completed_at = now if status == 'completed' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT id, watch_duration FROM learning_progress WHERE course_id = ? AND lesson_id = ? AND user_id = ?',
                                 (course_id, lesson_id, user_id))
                    row = cursor.fetchone()
                    new_watch = (row[1] if row else 0) + kwargs.get('watch_duration', 0)
                    if row:
                        cursor.execute('''
                            UPDATE learning_progress SET status = ?, progress_percent = ?,
                                watch_duration = ?, last_position = ?, last_learn_time = ?,
                                completed_at = COALESCE(completed_at, ?), updated_at = ?
                            WHERE id = ?
                        ''', (status, progress_percent, new_watch,
                              kwargs.get('last_position', 0), now, completed_at, now, row[0]))
                    else:
                        cursor.execute('''
                            INSERT INTO learning_progress (
                                course_id, lesson_id, user_id, user_name, status,
                                progress_percent, watch_duration, last_position,
                                last_learn_time, completed_at, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (course_id, lesson_id, user_id,
                              kwargs.get('user_name'), status, progress_percent,
                              kwargs.get('watch_duration', 0),
                              kwargs.get('last_position', 0), now, completed_at, now, now))
                    cursor.execute('SELECT COUNT(*) FROM learning_progress WHERE course_id = ? AND user_id = ? AND status = "completed"',
                                 (course_id, user_id))
                    completed_count = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM course_lessons WHERE course_id = ?', (course_id,))
                    total_lessons = cursor.fetchone()[0]
                    overall = round(completed_count / total_lessons * 100, 1) if total_lessons > 0 else 0
                    cursor.execute('SELECT id FROM course_enrollments WHERE course_id = ? AND user_id = ?',
                                 (course_id, user_id))
                    enroll = cursor.fetchone()
                    if enroll:
                        cursor.execute('UPDATE course_enrollments SET progress_percent = ?, completed_lessons = ?, total_lessons = ?, last_learn_time = ? WHERE id = ?',
                                     (overall, completed_count, total_lessons, now, enroll[0]))
                    conn.commit()
                    return {'success': True, 'status': status,
                            'overall_progress': overall,
                            'completed_lessons': completed_count,
                            'total_lessons': total_lessons}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_progress(self, course_id: str, user_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_progress WHERE course_id = ? AND user_id = ? ORDER BY last_learn_time DESC',
                             (course_id, user_id))
                progress_list = [dict(p) for p in cursor.fetchall()]
                cursor.execute('SELECT COUNT(*) as total FROM course_lessons WHERE course_id = ?', (course_id,))
                total_lessons = cursor.fetchone()['total']
                completed = sum(1 for p in progress_list if p.get('status') == 'completed')
                overall = round(completed / total_lessons * 100, 1) if total_lessons > 0 else 0
                return {'success': True, 'progress_list': progress_list,
                        'total_lessons': total_lessons, 'completed_lessons': completed,
                        'overall_progress': overall}
        except Exception as e:
            logger.error(f'获取用户进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course_progress_stats(self, course_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(DISTINCT user_id) as learner_cnt FROM learning_progress WHERE course_id = ?',
                             (course_id,))
                learner_count = cursor.fetchone()['learner_cnt']
                status_dist = {}
                cursor.execute('SELECT status, COUNT(*) as cnt FROM learning_progress WHERE course_id = ? GROUP BY status',
                             (course_id,))
                for row in cursor.fetchall():
                    status_dist[row['status']] = row['cnt']
                cursor.execute('SELECT AVG(progress_percent) as avg_progress FROM learning_progress WHERE course_id = ?',
                             (course_id,))
                avg_row = cursor.fetchone()
                avg_progress = round(avg_row['avg_progress'], 1) if avg_row['avg_progress'] else 0
                cursor.execute('SELECT COUNT(*) as enroll_cnt FROM course_enrollments WHERE course_id = ?', (course_id,))
                enrolled = cursor.fetchone()['enroll_cnt']
                return {'success': True, 'course_id': course_id,
                        'learner_count': learner_count, 'enrolled_count': enrolled,
                        'status_distribution': status_dist,
                        'avg_progress': avg_progress}
        except Exception as e:
            logger.error(f'获取课程进度统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 互动教学 ==========

    def create_interaction(self, session_id: str, interaction_type: str,
                           user_id: str, **kwargs) -> Dict[str, Any]:
        try:
            interaction_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            options_json = json.dumps(kwargs.get('options'), ensure_ascii=False) if kwargs.get('options') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT course_id FROM live_sessions WHERE session_id = ?', (session_id,))
                    session = cursor.fetchone()
                    course_id = session[0] if session else kwargs.get('course_id')
                    cursor.execute('''
                        INSERT INTO interactions (
                            interaction_id, session_id, course_id, interaction_type,
                            user_id, user_name, content, options, result, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (interaction_id, session_id, course_id, interaction_type,
                          user_id, kwargs.get('user_name'),
                          kwargs.get('content'), options_json,
                          kwargs.get('result_json'), now))
                    conn.commit()
                    logger.info(f'创建互动: {interaction_type} ({interaction_id})')
                    return {'success': True, 'interaction_id': interaction_id}
        except Exception as e:
            logger.error(f'创建互动失败: {e}')
            return {'success': False, 'error': str(e)}

    def answer_interaction(self, interaction_id: str, user_id: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            result = {'answer': kwargs.get('answer'),
                      'answered_by': user_id,
                      'answered_at': now,
                      'answer_user_name': kwargs.get('user_name')}
            if kwargs.get('selected_options'):
                result['selected_options'] = kwargs.get('selected_options')
            result_json = json.dumps(result, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE interactions SET result = ? WHERE interaction_id = ?',
                                 (result_json, interaction_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'result': result}
                    return {'success': False, 'error': '互动不存在'}
        except Exception as e:
            logger.error(f'回答互动失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_interactions(self, session_id: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM interactions WHERE 1=1'
                params = []
                if session_id:
                    query += ' AND session_id = ?'
                    params.append(session_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                for item in items:
                    if item.get('options'):
                        try:
                            item['options'] = json.loads(item['options'])
                        except (ValueError, TypeError):
                            pass
                    if item.get('result'):
                        try:
                            item['result'] = json.loads(item['result'])
                        except (ValueError, TypeError):
                            pass
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取互动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 在线答疑 ==========

    def ask_question(self, course_id: str, user_id: str, question: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            qa_id = f"qa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO online_qa (
                            qa_id, course_id, lesson_id, user_id, user_name,
                            question, question_type, status, answer_count,
                            helpful_count, is_pinned, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', 0, 0, 0, ?, ?)
                    ''', (qa_id, course_id, kwargs.get('lesson_id'),
                          user_id, kwargs.get('user_name'), question,
                          kwargs.get('question_type', 'general'), now, now))
                    conn.commit()
                    logger.info(f'在线提问: {question[:20]}... ({qa_id})')
                    return {'success': True, 'qa_id': qa_id}
        except Exception as e:
            logger.error(f'在线提问失败: {e}')
            return {'success': False, 'error': str(e)}

    def answer_question(self, qa_id: str, answered_by: str, answer: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, answer_count FROM online_qa WHERE qa_id = ?', (qa_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '问题不存在'}
                    new_status = 'answered' if row[1] == 0 else 'answered'
                    cursor.execute('''
                        UPDATE online_qa SET answer = ?, answered_by = ?, answered_at = ?,
                            status = ?, answer_count = answer_count + 1, updated_at = ?
                        WHERE qa_id = ?
                    ''', (answer, answered_by, now, new_status, now, qa_id))
                    conn.commit()
                    logger.info(f'解答问题: {qa_id}')
                    return {'success': True, 'status': new_status}
        except Exception as e:
            logger.error(f'解答问题失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_questions(self, course_id: str = None, page: int = 1,
                       page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM online_qa WHERE 1=1'
                params = []
                if course_id:
                    query += ' AND course_id = ?'
                    params.append(course_id)
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('lesson_id'):
                    query += ' AND lesson_id = ?'
                    params.append(filters['lesson_id'])
                query += ' ORDER BY is_pinned DESC, created_at DESC'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(q) for q in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取问题列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 作业管理 ==========

    def create_assignment(self, course_id: str, assignment_name: str,
                          assignment_type: str, **kwargs) -> Dict[str, Any]:
        try:
            assignment_id = f"asg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ASSIGNMENT_TYPES.get(assignment_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO online_assignments (
                            assignment_id, course_id, lesson_id, assignment_name,
                            assignment_type, description, total_score, deadline,
                            auto_grade, allow_resubmit, max_attempts, submit_count,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''', (assignment_id, course_id, kwargs.get('lesson_id'),
                          assignment_name, assignment_type, kwargs.get('description'),
                          kwargs.get('total_score', 100), kwargs.get('deadline'),
                          1 if kwargs.get('auto_grade', config.get('auto_grade', False)) else 0,
                          kwargs.get('allow_resubmit', 0),
                          kwargs.get('max_attempts', 1), now, now))
                    conn.commit()
                    logger.info(f'创建作业: {assignment_name} ({assignment_id})')
                    return {'success': True, 'assignment_id': assignment_id}
        except Exception as e:
            logger.error(f'创建作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_assignment(self, assignment_id: str, user_id: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            submission_id = f"sub_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT auto_grade, max_attempts, allow_resubmit, submit_count FROM online_assignments WHERE assignment_id = ?',
                                 (assignment_id,))
                    assignment = cursor.fetchone()
                    if not assignment:
                        return {'success': False, 'error': '作业不存在'}
                    cursor.execute('SELECT MAX(attempt_number) as max_attempt FROM assignment_submissions WHERE assignment_id = ? AND user_id = ?',
                                 (assignment_id, user_id))
                    attempt_row = cursor.fetchone()
                    current_attempt = (attempt_row['max_attempt'] or 0) + 1
                    if not assignment[2] and current_attempt > assignment[1]:
                        return {'success': False, 'error': '已达最大提交次数'}
                    status = 'submitted'
                    score = None
                    feedback = None
                    if assignment[0] and kwargs.get('auto_score') is not None:
                        score = kwargs.get('auto_score')
                        feedback = kwargs.get('auto_feedback', '系统自动批改')
                        status = 'graded'
                    cursor.execute('''
                        INSERT INTO assignment_submissions (
                            submission_id, assignment_id, user_id, user_name,
                            content, file_url, score, feedback, graded_by, graded_at,
                            attempt_number, submit_time, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (submission_id, assignment_id, user_id,
                          kwargs.get('user_name'), kwargs.get('content'),
                          kwargs.get('file_url'), score, feedback,
                          kwargs.get('graded_by') if status == 'graded' else None,
                          now if status == 'graded' else None,
                          current_attempt, now, status, now))
                    cursor.execute('UPDATE online_assignments SET submit_count = submit_count + 1, updated_at = ? WHERE assignment_id = ?',
                                 (now, assignment_id))
                    conn.commit()
                    logger.info(f'提交作业: {assignment_id} 第{current_attempt}次')
                    return {'success': True, 'submission_id': submission_id,
                            'attempt_number': current_attempt, 'status': status}
        except Exception as e:
            logger.error(f'提交作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def grade_assignment(self, submission_id: str, score: float,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT assignment_id FROM assignment_submissions WHERE submission_id = ?',
                                 (submission_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '提交记录不存在'}
                    cursor.execute('SELECT total_score FROM online_assignments WHERE assignment_id = ?', (row[0],))
                    assignment = cursor.fetchone()
                    total_score = assignment[0] if assignment else 100
                    if score > total_score:
                        return {'success': False, 'error': f'分数超过总分({total_score})'}
                    cursor.execute('''
                        UPDATE assignment_submissions SET score = ?, feedback = ?,
                            graded_by = ?, graded_at = ?, status = 'graded'
                        WHERE submission_id = ?
                    ''', (score, kwargs.get('feedback'), kwargs.get('graded_by'),
                          now, submission_id))
                    conn.commit()
                    logger.info(f'批改作业: {submission_id} 分数 {score}')
                    return {'success': True, 'score': score, 'total_score': total_score}
        except Exception as e:
            logger.error(f'批改作业失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_assignments(self, course_id: str = None, page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM online_assignments WHERE 1=1'
                params = []
                if course_id:
                    query += ' AND course_id = ?'
                    params.append(course_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取作业列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习社区 ==========

    def create_community(self, community_name: str, community_type: str,
                         creator_id: str, **kwargs) -> Dict[str, Any]:
        try:
            community_id = f"com_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_communities (
                            community_id, community_name, community_type, course_id,
                            creator_id, creator_name, description, member_count,
                            max_members, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 1, ?, ?)
                    ''', (community_id, community_name, community_type,
                          kwargs.get('course_id'), creator_id,
                          kwargs.get('creator_name'), kwargs.get('description'),
                          kwargs.get('max_members', 100), now, now))
                    cursor.execute('INSERT INTO community_members (community_id, user_id, user_name, role, joined_at, contribution_score, created_at) VALUES (?, ?, ?, "creator", ?, 0, ?)',
                                 (community_id, creator_id, kwargs.get('creator_name'), now, now))
                    conn.commit()
                    logger.info(f'创建学习社区: {community_name} ({community_id})')
                    return {'success': True, 'community_id': community_id}
        except Exception as e:
            logger.error(f'创建学习社区失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_community(self, community_id: str, user_id: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT member_count, max_members, is_active FROM learning_communities WHERE community_id = ?',
                                 (community_id,))
                    community = cursor.fetchone()
                    if not community:
                        return {'success': False, 'error': '社区不存在'}
                    if not community[2]:
                        return {'success': False, 'error': '社区已关闭'}
                    if community[1] and community[0] >= community[1]:
                        return {'success': False, 'error': '社区成员已满'}
                    cursor.execute('INSERT OR IGNORE INTO community_members (community_id, user_id, user_name, role, joined_at, contribution_score, created_at) VALUES (?, ?, ?, "member", ?, 0, ?)',
                                 (community_id, user_id, kwargs.get('user_name'), now, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE learning_communities SET member_count = member_count + 1, updated_at = ? WHERE community_id = ?',
                                     (now, community_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该社区'}
        except Exception as e:
            logger.error(f'加入社区失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_post(self, community_id: str, user_id: str, title: str,
                    content: str, **kwargs) -> Dict[str, Any]:
        try:
            post_id = f"pst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM learning_communities WHERE community_id = ?', (community_id,))
                    community = cursor.fetchone()
                    if not community:
                        return {'success': False, 'error': '社区不存在'}
                    if not community[0]:
                        return {'success': False, 'error': '社区已关闭'}
                    cursor.execute('''
                        INSERT INTO community_posts (
                            post_id, community_id, user_id, user_name, title,
                            content, post_type, view_count, like_count,
                            reply_count, is_pinned, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)
                    ''', (post_id, community_id, user_id, kwargs.get('user_name'),
                          title, content, kwargs.get('post_type', 'discussion'),
                          kwargs.get('is_pinned', 0), now, now))
                    conn.commit()
                    logger.info(f'发布帖子: {title} ({post_id})')
                    return {'success': True, 'post_id': post_id}
        except Exception as e:
            logger.error(f'发布帖子失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_communities(self, page: int = 1, page_size: int = 20,
                         **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_communities WHERE 1=1'
                params = []
                if filters.get('community_type'):
                    query += ' AND community_type = ?'
                    params.append(filters['community_type'])
                if filters.get('course_id'):
                    query += ' AND course_id = ?'
                    params.append(filters['course_id'])
                if filters.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if filters['is_active'] else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社区列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_posts(self, community_id: str, page: int = 1,
                   page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM community_posts WHERE community_id = ?'
                params = [community_id]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY is_pinned DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取帖子列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 课程报名 ==========

    def enroll_course(self, course_id: str, user_id: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, education_type FROM online_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[0] != 'published':
                        return {'success': False, 'error': '课程未发布'}
                    cursor.execute('SELECT id FROM course_enrollments WHERE course_id = ? AND user_id = ?',
                                 (course_id, user_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该课程'}
                    cursor.execute('SELECT COUNT(*) FROM course_lessons WHERE course_id = ?', (course_id,))
                    total_lessons = cursor.fetchone()[0]
                    cursor.execute('''
                        INSERT INTO course_enrollments (
                            course_id, user_id, user_name, education_type,
                            enroll_time, progress_percent, last_learn_time,
                            completed_lessons, total_lessons, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, 0, ?, 'active', ?)
                    ''', (course_id, user_id, kwargs.get('user_name'),
                          kwargs.get('education_type', course[1]),
                          now, now, total_lessons, now))
                    cursor.execute('UPDATE online_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?',
                                 (now, course_id))
                    conn.commit()
                    logger.info(f'报名课程: {course_id} 用户 {user_id}')
                    return {'success': True, 'total_lessons': total_lessons}
        except Exception as e:
            logger.error(f'报名课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_user_courses(self, user_id: str, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT e.*, c.course_name, c.course_type, c.subject,
                           c.difficulty, c.cover_image, c.total_hours
                    FROM course_enrollments e
                    LEFT JOIN online_courses c ON e.course_id = c.course_id
                    WHERE e.user_id = ?
                '''
                params = [user_id]
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY e.created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取用户课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                course_filter = ' WHERE education_type = ?' if education_type else ''
                params = [education_type] if education_type else []
                cursor.execute(f'SELECT course_type, COUNT(*) as cnt FROM online_courses{course_filter} GROUP BY course_type', params)
                course_type_dist = {row['course_type']: row['cnt'] for row in cursor.fetchall()}
                cursor.execute(f'SELECT COUNT(*) as cnt FROM online_courses{course_filter}', params)
                total_courses = cursor.fetchone()['cnt']
                cursor.execute('SELECT live_status, COUNT(*) as cnt FROM live_sessions GROUP BY live_status')
                live_stats = {row['live_status']: row['cnt'] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) as total_sessions, COALESCE(SUM(actual_participants), 0) as total_participants FROM live_sessions')
                live_row = cursor.fetchone()
                live_summary = {'total_sessions': live_row['total_sessions'],
                                'total_participants': live_row['total_participants'],
                                'status_distribution': live_stats}
                cursor.execute('SELECT status, COUNT(*) as cnt FROM learning_progress GROUP BY status')
                progress_dist = {row['status']: row['cnt'] for row in cursor.fetchall()}
                cursor.execute('SELECT status, COUNT(*) as cnt FROM online_qa GROUP BY status')
                qa_stats = {row['status']: row['cnt'] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) as total_qa, COALESCE(SUM(helpful_count), 0) as total_helpful FROM online_qa')
                qa_row = cursor.fetchone()
                qa_summary = {'total_questions': qa_row['total_qa'],
                              'total_helpful': qa_row['total_helpful'],
                              'status_distribution': qa_stats}
                cursor.execute('SELECT COUNT(*) as total_communities, COALESCE(SUM(member_count), 0) as total_members FROM learning_communities WHERE is_active = 1')
                com_row = cursor.fetchone()
                cursor.execute('SELECT COUNT(*) as total_posts, COALESCE(SUM(like_count), 0) as total_likes FROM community_posts')
                post_row = cursor.fetchone()
                community_summary = {'total_communities': com_row['total_communities'],
                                     'total_members': com_row['total_members'],
                                     'total_posts': post_row['total_posts'],
                                     'total_likes': post_row['total_likes']}
                cursor.execute('SELECT COUNT(*) as total_enrollments FROM course_enrollments')
                total_enrollments = cursor.fetchone()[0]
                return {'success': True, 'education_type': education_type,
                        'total_courses': total_courses,
                        'total_enrollments': total_enrollments,
                        'course_type_distribution': course_type_dist,
                        'live_statistics': live_summary,
                        'progress_distribution': progress_dist,
                        'qa_statistics': qa_summary,
                        'community_activity': community_summary}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = OnlineLearningPlatformService()
    print('在线学习平台服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
