#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育艺术教育服务 (v15.25.0)
====================================
提供音乐教育、美术教育、舞蹈教育、戏剧教育、影视教育、书法教育、艺术欣赏和艺术创作等综合管理服务。

核心能力：
1. 音乐教育 - 声乐/器乐/合唱/合奏/音乐理论/音乐欣赏/音乐创作/音乐表演
2. 美术教育 - 绘画/书法/雕塑/摄影/设计/工艺美术/艺术史/艺术鉴赏
3. 舞蹈教育 - 民族舞/现代舞/芭蕾舞/街舞/爵士舞/舞蹈创编/舞蹈表演/舞蹈欣赏
4. 戏剧教育 - 话剧/戏曲/音乐剧/儿童剧/表演艺术/舞台设计/戏剧创作/戏剧欣赏
5. 影视教育 - 电影制作/影视表演/影视编导/影视后期/动画制作/摄影摄像/影视鉴赏/数字媒体
6. 书法教育 - 楷书/行书/草书/隶书/篆书/篆刻/硬笔书法/书法鉴赏
7. 艺术欣赏 - 音乐欣赏/美术欣赏/舞蹈欣赏/戏剧欣赏/影视欣赏/书法欣赏/艺术评论/文化遗产
8. 艺术创作 - 音乐创作/美术创作/舞蹈创编/戏剧创作/影视创作/书法创作/艺术设计/综合艺术

差异化支持：成人教育 / K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_arts_education_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationArtsEducation')


# ========== 艺术教育配置 ==========

MUSIC_TYPES = {
    'vocal': {'name': '声乐', 'description': '歌唱技巧与表演', 'levels': ['初级', '中级', '高级', '专业']},
    'instrumental': {'name': '器乐', 'description': '乐器演奏技能', 'levels': ['初级', '中级', '高级', '专业']},
    'choir': {'name': '合唱', 'description': '多声部合唱训练', 'levels': ['初级', '中级', '高级', '专业']},
    'ensemble': {'name': '合奏', 'description': '乐队合奏训练', 'levels': ['初级', '中级', '高级', '专业']},
    'theory': {'name': '音乐理论', 'description': '乐理知识学习', 'levels': ['入门', '基础', '进阶', '高级']},
    'appreciation': {'name': '音乐欣赏', 'description': '音乐作品赏析', 'levels': ['入门', '基础', '进阶', '高级']},
    'composition': {'name': '音乐创作', 'description': '音乐作品创作', 'levels': ['初级', '中级', '高级', '专业']},
    'performance': {'name': '音乐表演', 'description': '舞台表演技巧', 'levels': ['初级', '中级', '高级', '专业']}
}

ART_TYPES = {
    'painting': {'name': '绘画', 'description': '绘画技法与创作', 'levels': ['初级', '中级', '高级', '专业']},
    'calligraphy': {'name': '书法', 'description': '书写艺术与技法', 'levels': ['初级', '中级', '高级', '专业']},
    'sculpture': {'name': '雕塑', 'description': '立体造型艺术', 'levels': ['初级', '中级', '高级', '专业']},
    'photography': {'name': '摄影', 'description': '摄影技术与艺术', 'levels': ['初级', '中级', '高级', '专业']},
    'design': {'name': '设计', 'description': '视觉设计与创意', 'levels': ['初级', '中级', '高级', '专业']},
    'craft': {'name': '工艺美术', 'description': '传统工艺制作', 'levels': ['初级', '中级', '高级', '专业']},
    'art_history': {'name': '艺术史', 'description': '艺术发展历程', 'levels': ['入门', '基础', '进阶', '高级']},
    'art_appreciation': {'name': '艺术鉴赏', 'description': '艺术品鉴赏能力', 'levels': ['入门', '基础', '进阶', '高级']}
}

DANCE_TYPES = {
    'folk': {'name': '民族舞', 'description': '民族舞蹈风格', 'levels': ['初级', '中级', '高级', '专业']},
    'modern': {'name': '现代舞', 'description': '现代舞蹈表达', 'levels': ['初级', '中级', '高级', '专业']},
    'ballet': {'name': '芭蕾舞', 'description': '古典芭蕾训练', 'levels': ['初级', '中级', '高级', '专业']},
    'street': {'name': '街舞', 'description': '流行街舞风格', 'levels': ['初级', '中级', '高级', '专业']},
    'jazz': {'name': '爵士舞', 'description': '爵士舞蹈风格', 'levels': ['初级', '中级', '高级', '专业']},
    'choreography': {'name': '舞蹈创编', 'description': '舞蹈编排创作', 'levels': ['初级', '中级', '高级', '专业']},
    'performance': {'name': '舞蹈表演', 'description': '舞台表演技巧', 'levels': ['初级', '中级', '高级', '专业']},
    'appreciation': {'name': '舞蹈欣赏', 'description': '舞蹈作品赏析', 'levels': ['入门', '基础', '进阶', '高级']}
}

THEATER_TYPES = {
    'drama': {'name': '话剧', 'description': '话剧表演与创作', 'levels': ['初级', '中级', '高级', '专业']},
    'opera': {'name': '戏曲', 'description': '传统戏曲表演', 'levels': ['初级', '中级', '高级', '专业']},
    'musical': {'name': '音乐剧', 'description': '音乐戏剧表演', 'levels': ['初级', '中级', '高级', '专业']},
    'children': {'name': '儿童剧', 'description': '儿童戏剧创作', 'levels': ['初级', '中级', '高级', '专业']},
    'performing': {'name': '表演艺术', 'description': '综合表演训练', 'levels': ['初级', '中级', '高级', '专业']},
    'stage_design': {'name': '舞台设计', 'description': '舞台美术设计', 'levels': ['初级', '中级', '高级', '专业']},
    'creation': {'name': '戏剧创作', 'description': '剧本创作与编排', 'levels': ['初级', '中级', '高级', '专业']},
    'appreciation': {'name': '戏剧欣赏', 'description': '戏剧作品赏析', 'levels': ['入门', '基础', '进阶', '高级']}
}

FILM_TYPES = {
    'production': {'name': '电影制作', 'description': '电影拍摄制作', 'levels': ['初级', '中级', '高级', '专业']},
    'acting': {'name': '影视表演', 'description': '影视表演技巧', 'levels': ['初级', '中级', '高级', '专业']},
    'directing': {'name': '影视编导', 'description': '导演与编剧', 'levels': ['初级', '中级', '高级', '专业']},
    'post_production': {'name': '影视后期', 'description': '后期剪辑制作', 'levels': ['初级', '中级', '高级', '专业']},
    'animation': {'name': '动画制作', 'description': '动画创作设计', 'levels': ['初级', '中级', '高级', '专业']},
    'cinematography': {'name': '摄影摄像', 'description': '镜头语言运用', 'levels': ['初级', '中级', '高级', '专业']},
    'appreciation': {'name': '影视鉴赏', 'description': '影视作品赏析', 'levels': ['入门', '基础', '进阶', '高级']},
    'digital_media': {'name': '数字媒体', 'description': '数字媒体艺术', 'levels': ['初级', '中级', '高级', '专业']}
}

CALLIGRAPHY_TYPES = {
    'regular': {'name': '楷书', 'description': '楷书书法技法', 'levels': ['初级', '中级', '高级', '专业']},
    'running': {'name': '行书', 'description': '行书书法技法', 'levels': ['初级', '中级', '高级', '专业']},
    'cursive': {'name': '草书', 'description': '草书书法技法', 'levels': ['初级', '中级', '高级', '专业']},
    'official': {'name': '隶书', 'description': '隶书书法技法', 'levels': ['初级', '中级', '高级', '专业']},
    'seal': {'name': '篆书', 'description': '篆书书法技法', 'levels': ['初级', '中级', '高级', '专业']},
    'seal_carving': {'name': '篆刻', 'description': '印章雕刻艺术', 'levels': ['初级', '中级', '高级', '专业']},
    'hard_pen': {'name': '硬笔书法', 'description': '硬笔书写技巧', 'levels': ['初级', '中级', '高级', '专业']},
    'appreciation': {'name': '书法鉴赏', 'description': '书法作品赏析', 'levels': ['入门', '基础', '进阶', '高级']}
}

APPRECIATION_TYPES = {
    'music': {'name': '音乐欣赏', 'description': '经典音乐作品赏析'},
    'art': {'name': '美术欣赏', 'description': '美术作品鉴赏分析'},
    'dance': {'name': '舞蹈欣赏', 'description': '舞蹈作品审美解读'},
    'theater': {'name': '戏剧欣赏', 'description': '戏剧作品赏析'},
    'film': {'name': '影视欣赏', 'description': '影视作品鉴赏'},
    'calligraphy': {'name': '书法欣赏', 'description': '书法作品赏析'},
    'art_criticism': {'name': '艺术评论', 'description': '艺术作品评论写作'},
    'cultural_heritage': {'name': '文化遗产', 'description': '文化遗产保护与传承'}
}

CREATION_TYPES = {
    'music': {'name': '音乐创作', 'description': '音乐作品创作'},
    'art': {'name': '美术创作', 'description': '美术作品创作'},
    'dance': {'name': '舞蹈创编', 'description': '舞蹈作品编排'},
    'theater': {'name': '戏剧创作', 'description': '戏剧剧本创作'},
    'film': {'name': '影视创作', 'description': '影视内容创作'},
    'calligraphy': {'name': '书法创作', 'description': '书法作品创作'},
    'art_design': {'name': '艺术设计', 'description': '艺术设计实践'},
    'comprehensive': {'name': '综合艺术', 'description': '跨媒介艺术创作'}
}


class EducationArtsEducationService:
    """教育艺术教育服务"""

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
                    CREATE TABLE IF NOT EXISTS music_education (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        music_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS music_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        feedback TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS art_education (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        art_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS art_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        feedback TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dance_education (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        dance_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        feedback TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS theater_education (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        theater_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS theater_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        feedback TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS film_education (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        film_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS film_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        feedback TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calligraphy_education (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        calligraphy_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS calligraphy_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        feedback TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS art_appreciation (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        appreciation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        instructor_id INTEGER,
                        instructor_name TEXT,
                        description TEXT,
                        content TEXT,
                        duration INTEGER DEFAULT 90,
                        max_participants INTEGER DEFAULT 50,
                        registered_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS appreciation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        program_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        register_date TEXT,
                        completed INTEGER DEFAULT 0,
                        score REAL,
                        feedback TEXT,
                        UNIQUE(program_id, student_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS art_creation (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        creation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        description TEXT,
                        requirements TEXT,
                        deadline TEXT,
                        max_participants INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS creation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        submission_url TEXT,
                        submission_date TEXT,
                        score REAL,
                        grade TEXT,
                        feedback TEXT,
                        status TEXT DEFAULT 'pending',
                        UNIQUE(project_id, student_id)
                    )
                ''')

                conn.commit()
                logger.info('教育艺术教育服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 音乐教育 ==========

    def create_music_course(self, course_name: str, music_type: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"mus_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO music_education (
                            course_id, course_name, music_type, education_type,
                            grade_level, teacher_id, teacher_name, semester,
                            weekly_hours, location, max_students, enrolled_count,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (course_id, course_name, music_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('semester'),
                          kwargs.get('weekly_hours', 2), kwargs.get('location'),
                          kwargs.get('max_students', 30), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建音乐教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建音乐教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_music_course(self, course_id: str, student_id: int,
                            student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM music_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO music_records (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE music_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'音乐选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_music_attendance(self, course_id: str, student_id: int,
                                attendance_count: int = 1) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE music_records SET attendance_count = attendance_count + ? WHERE course_id = ? AND student_id = ?',
                                 (attendance_count, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录音乐出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_music_score(self, course_id: str, student_id: int,
                           score: float, **kwargs) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE music_records SET final_score = ?, grade = ?, feedback = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, kwargs.get('feedback'), course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录音乐成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 美术教育 ==========

    def create_art_course(self, course_name: str, art_type: str,
                          education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"art_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO art_education (
                            course_id, course_name, art_type, education_type,
                            grade_level, teacher_id, teacher_name, semester,
                            weekly_hours, location, max_students, enrolled_count,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (course_id, course_name, art_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('semester'),
                          kwargs.get('weekly_hours', 2), kwargs.get('location'),
                          kwargs.get('max_students', 30), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建美术教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建美术教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_art_course(self, course_id: str, student_id: int,
                          student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM art_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO art_records (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE art_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'美术选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_art_attendance(self, course_id: str, student_id: int,
                              attendance_count: int = 1) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE art_records SET attendance_count = attendance_count + ? WHERE course_id = ? AND student_id = ?',
                                 (attendance_count, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录美术出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_art_score(self, course_id: str, student_id: int,
                         score: float, **kwargs) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE art_records SET final_score = ?, grade = ?, feedback = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, kwargs.get('feedback'), course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录美术成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 舞蹈教育 ==========

    def create_dance_course(self, course_name: str, dance_type: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"dac_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO dance_education (
                            course_id, course_name, dance_type, education_type,
                            grade_level, teacher_id, teacher_name, semester,
                            weekly_hours, location, max_students, enrolled_count,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (course_id, course_name, dance_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('semester'),
                          kwargs.get('weekly_hours', 2), kwargs.get('location'),
                          kwargs.get('max_students', 30), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建舞蹈教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建舞蹈教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_dance_course(self, course_id: str, student_id: int,
                            student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM dance_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO dance_records (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE dance_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'舞蹈选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_dance_attendance(self, course_id: str, student_id: int,
                                attendance_count: int = 1) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE dance_records SET attendance_count = attendance_count + ? WHERE course_id = ? AND student_id = ?',
                                 (attendance_count, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录舞蹈出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_dance_score(self, course_id: str, student_id: int,
                           score: float, **kwargs) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE dance_records SET final_score = ?, grade = ?, feedback = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, kwargs.get('feedback'), course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录舞蹈成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 戏剧教育 ==========

    def create_theater_course(self, course_name: str, theater_type: str,
                              education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"the_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO theater_education (
                            course_id, course_name, theater_type, education_type,
                            grade_level, teacher_id, teacher_name, semester,
                            weekly_hours, location, max_students, enrolled_count,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (course_id, course_name, theater_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('semester'),
                          kwargs.get('weekly_hours', 2), kwargs.get('location'),
                          kwargs.get('max_students', 30), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建戏剧教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建戏剧教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_theater_course(self, course_id: str, student_id: int,
                              student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM theater_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO theater_records (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE theater_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'戏剧选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_theater_attendance(self, course_id: str, student_id: int,
                                  attendance_count: int = 1) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE theater_records SET attendance_count = attendance_count + ? WHERE course_id = ? AND student_id = ?',
                                 (attendance_count, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录戏剧出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_theater_score(self, course_id: str, student_id: int,
                             score: float, **kwargs) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE theater_records SET final_score = ?, grade = ?, feedback = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, kwargs.get('feedback'), course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录戏剧成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_theater_performance(self, course_id: str, title: str,
                                   performance_date: str, **kwargs) -> Dict[str, Any]:
        try:
            perf_id = f"tpf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO theater_performances (
                            perf_id, course_id, title, performance_date,
                            location, description, max_seats, seats_sold,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'scheduled', ?, ?)
                    ''', (perf_id, course_id, title, performance_date,
                          kwargs.get('location'), kwargs.get('description'),
                          kwargs.get('max_seats', 200), now, now))
                    conn.commit()
                    logger.info(f'创建戏剧演出: {title} ({perf_id})')
                    return {'success': True, 'perf_id': perf_id}
        except Exception as e:
            logger.error(f'创建戏剧演出失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 影视教育 ==========

    def create_film_course(self, course_name: str, film_type: str,
                           education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"fil_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO film_education (
                            course_id, course_name, film_type, education_type,
                            grade_level, teacher_id, teacher_name, semester,
                            weekly_hours, location, max_students, enrolled_count,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (course_id, course_name, film_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('semester'),
                          kwargs.get('weekly_hours', 2), kwargs.get('location'),
                          kwargs.get('max_students', 30), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建影视教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建影视教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_film_course(self, course_id: str, student_id: int,
                           student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM film_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO film_records (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE film_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'影视选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_film_attendance(self, course_id: str, student_id: int,
                               attendance_count: int = 1) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE film_records SET attendance_count = attendance_count + ? WHERE course_id = ? AND student_id = ?',
                                 (attendance_count, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录影视出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_film_score(self, course_id: str, student_id: int,
                          score: float, **kwargs) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE film_records SET final_score = ?, grade = ?, feedback = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, kwargs.get('feedback'), course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录影视成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 书法教育 ==========

    def create_calligraphy_course(self, course_name: str, calligraphy_type: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"cal_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO calligraphy_education (
                            course_id, course_name, calligraphy_type, education_type,
                            grade_level, teacher_id, teacher_name, semester,
                            weekly_hours, location, max_students, enrolled_count,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (course_id, course_name, calligraphy_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('semester'),
                          kwargs.get('weekly_hours', 2), kwargs.get('location'),
                          kwargs.get('max_students', 30), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建书法教育课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建书法教育课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_calligraphy_course(self, course_id: str, student_id: int,
                                   student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM calligraphy_education WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO calligraphy_records (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE calligraphy_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'书法选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_calligraphy_attendance(self, course_id: str, student_id: int,
                                       attendance_count: int = 1) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE calligraphy_records SET attendance_count = attendance_count + ? WHERE course_id = ? AND student_id = ?',
                                 (attendance_count, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录书法出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_calligraphy_score(self, course_id: str, student_id: int,
                                  score: float, **kwargs) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE calligraphy_records SET final_score = ?, grade = ?, feedback = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, kwargs.get('feedback'), course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录书法成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 艺术欣赏 ==========

    def create_appreciation_program(self, program_name: str, appreciation_type: str,
                                    education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"app_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO art_appreciation (
                            program_id, program_name, appreciation_type, education_type,
                            grade_level, instructor_id, instructor_name, description,
                            content, duration, max_participants, registered_count,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (program_id, program_name, appreciation_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('instructor_id'),
                          kwargs.get('instructor_name'), kwargs.get('description'),
                          kwargs.get('content'), kwargs.get('duration', 90),
                          kwargs.get('max_participants', 50), now, now))
                    conn.commit()
                    logger.info(f'创建艺术欣赏项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建艺术欣赏项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_appreciation(self, program_id: str, student_id: int,
                              student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM art_appreciation WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'active':
                        return {'success': False, 'error': '项目状态不允许报名'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO appreciation_records (program_id, student_id, student_name, register_date) VALUES (?, ?, ?, ?)',
                                 (program_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE art_appreciation SET registered_count = registered_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该项目'}
        except Exception as e:
            logger.error(f'艺术欣赏报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_appreciation_completed(self, program_id: str, student_id: int) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE appreciation_records SET completed = 1 WHERE program_id = ? AND student_id = ?',
                                 (program_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'标记艺术欣赏完成失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_appreciation_score(self, program_id: str, student_id: int,
                                   score: float, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE appreciation_records SET score = ?, feedback = ?, completed = 1 WHERE program_id = ? AND student_id = ?',
                                 (score, kwargs.get('feedback'), program_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录艺术欣赏成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 艺术创作 ==========

    def create_creation_project(self, project_name: str, creation_type: str,
                                education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"cre_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO art_creation (
                            project_id, project_name, creation_type, education_type,
                            grade_level, teacher_id, teacher_name, description,
                            requirements, deadline, max_participants, enrolled_count,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (project_id, project_name, creation_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('description'),
                          kwargs.get('requirements'), kwargs.get('deadline'),
                          kwargs.get('max_participants', 30), now, now))
                    conn.commit()
                    logger.info(f'创建艺术创作项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建艺术创作项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_creation_project(self, project_id: str, student_id: int,
                                 student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM art_creation WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    if project[2] != 'active':
                        return {'success': False, 'error': '项目状态不允许报名'}
                    if project[0] and project[1] >= project[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO creation_records (project_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (project_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE art_creation SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE project_id = ?', (now, project_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该项目'}
        except Exception as e:
            logger.error(f'艺术创作报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_creation(self, project_id: str, student_id: int,
                         submission_url: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE creation_records SET submission_url = ?, submission_date = ?, status = ? WHERE project_id = ? AND student_id = ?',
                                 (submission_url, now[:10], 'submitted', project_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'提交艺术创作失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_creation(self, project_id: str, student_id: int,
                           score: float, **kwargs) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE creation_records SET score = ?, grade = ?, feedback = ?, status = ? WHERE project_id = ? AND student_id = ?',
                                 (score, grade, kwargs.get('feedback'), 'evaluated', project_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '提交记录不存在'}
        except Exception as e:
            logger.error(f'评价艺术创作失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_education_statistics(self, education_type: str = None,
                                 **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                tables = [
                    ('music_education', 'music_records'),
                    ('art_education', 'art_records'),
                    ('dance_education', 'dance_records'),
                    ('theater_education', 'theater_records'),
                    ('film_education', 'film_records'),
                    ('calligraphy_education', 'calligraphy_records'),
                    ('art_appreciation', 'appreciation_records'),
                    ('art_creation', 'creation_records')
                ]

                for course_table, record_table in tables:
                    if education_type:
                        cursor.execute(f'SELECT COUNT(*) FROM {course_table} WHERE education_type = ?', (education_type,))
                        course_count = cursor.fetchone()[0]
                        cursor.execute(f'SELECT COUNT(*) FROM {record_table} r JOIN {course_table} c ON r.course_id = c.course_id WHERE c.education_type = ?', (education_type,))
                        student_count = cursor.fetchone()[0]
                    else:
                        cursor.execute(f'SELECT COUNT(*) FROM {course_table}')
                        course_count = cursor.fetchone()[0]
                        cursor.execute(f'SELECT COUNT(*) FROM {record_table}')
                        student_count = cursor.fetchone()[0]

                    stats[course_table] = {
                        'course_count': course_count,
                        'student_count': student_count
                    }

                cursor.execute('SELECT education_type, COUNT(*) FROM music_education GROUP BY education_type')
                music_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['music_by_type'] = music_by_type

                cursor.execute('SELECT education_type, COUNT(*) FROM art_education GROUP BY education_type')
                art_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['art_by_type'] = art_by_type

                cursor.execute('SELECT education_type, COUNT(*) FROM dance_education GROUP BY education_type')
                dance_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['dance_by_type'] = dance_by_type

                cursor.execute('SELECT education_type, COUNT(*) FROM theater_education GROUP BY education_type')
                theater_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['theater_by_type'] = theater_by_type

                cursor.execute('SELECT education_type, COUNT(*) FROM film_education GROUP BY education_type')
                film_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['film_by_type'] = film_by_type

                cursor.execute('SELECT education_type, COUNT(*) FROM calligraphy_education GROUP BY education_type')
                calligraphy_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['calligraphy_by_type'] = calligraphy_by_type

                cursor.execute('SELECT education_type, COUNT(*) FROM art_appreciation GROUP BY education_type')
                appreciation_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['appreciation_by_type'] = appreciation_by_type

                cursor.execute('SELECT education_type, COUNT(*) FROM art_creation GROUP BY education_type')
                creation_by_type = {row[0]: row[1] for row in cursor.fetchall()}
                stats['creation_by_type'] = creation_by_type

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取教育统计失败: {e}')
            return {'success': False, 'error': str(e)}