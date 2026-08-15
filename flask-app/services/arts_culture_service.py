#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 艺术与文化管理服务 (v15.7.0)
====================================
提供艺术课程、文艺活动、作品展览和文化传承等综合管理服务。

核心能力：
1. 艺术课程 - 课程管理、选课记录、考级管理
2. 文艺活动 - 活动组织、演出管理、票务系统
3. 作品管理 - 作品登记、展览管理、评价系统
4. 艺术考级 - 考级报名、成绩管理、证书发放
5. 社团管理 - 艺术社团、成员管理、活动记录
6. 文化传承 - 传统文化、非遗项目、文化课程
7. 成人艺术 - 成人教育艺术素养提升
8. K12美育 - 学生艺术素养培养与评价
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arts_culture_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ArtsCulture')


# ========== 艺术配置 ==========

# 艺术类别
ART_CATEGORIES = {
    'music': {'name': '音乐', 'sub': ['声乐', '器乐', '作曲', '音乐理论']},
    'dance': {'name': '舞蹈', 'sub': ['民族舞', '现代舞', '芭蕾', '街舞', '拉丁舞']},
    'fine_art': {'name': '美术', 'sub': ['素描', '色彩', '国画', '油画', '版画', '雕塑']},
    'calligraphy': {'name': '书法', 'sub': ['硬笔', '毛笔', '篆刻']},
    'drama': {'name': '戏剧', 'sub': ['话剧', '戏曲', '音乐剧', '朗诵']},
    'photography': {'name': '摄影', 'sub': ['风景', '人像', '纪实', '艺术摄影']},
    'design': {'name': '设计', 'sub': ['平面设计', 'UI设计', '服装设计', '环境设计']},
    'film': {'name': '影视', 'sub': ['导演', '编剧', '剪辑', '动画']},
    'literature': {'name': '文学', 'sub': ['诗歌', '散文', '小说', '剧本']},
    'craft': {'name': '工艺', 'sub': ['陶艺', '手工', '编织', '剪纸']}
}

# 活动类型
EVENT_TYPES = {
    'performance': {'name': '文艺演出', 'requires_tickets': True},
    'exhibition': {'name': '作品展览', 'requires_tickets': False},
    'competition': {'name': '艺术比赛', 'requires_tickets': False},
    'festival': {'name': '艺术节', 'requires_tickets': True},
    'lecture': {'name': '艺术讲座', 'requires_tickets': False},
    'workshop': {'name': '工作坊', 'requires_tickets': False},
    'cultural_fair': {'name': '文化集市', 'requires_tickets': False},
    'screening': {'name': '影视放映', 'requires_tickets': True}
}

# 考级机构与级别
GRADE_SYSTEMS = {
    'music': {'name': '音乐考级', 'levels': 10, 'organizations': ['中央音乐学院', '中国音乐学院', '上海音乐学院']},
    'art': {'name': '美术考级', 'levels': 10, 'organizations': ['中国美术学院', '文化部艺术发展中心']},
    'dance': {'name': '舞蹈考级', 'levels': 13, 'organizations': ['北京舞蹈学院', '中国舞蹈家协会']},
    'calligraphy': {'name': '书法考级', 'levels': 10, 'organizations': ['中国书法家协会', '文化部']},
    'drama': {'name': '戏剧考级', 'levels': 10, 'organizations': ['中国戏剧家协会']},
    'photography': {'name': '摄影考级', 'levels': 10, 'organizations': ['中国摄影家协会']}
}

# 作品类型
ARTWORK_TYPES = {
    'painting': {'name': '绘画作品', 'extensions': ['jpg', 'png', 'bmp']},
    'calligraphy': {'name': '书法作品', 'extensions': ['jpg', 'png']},
    'sculpture': {'name': '雕塑作品', 'extensions': ['jpg', 'png']},
    'photography': {'name': '摄影作品', 'extensions': ['jpg', 'png', 'raw']},
    'digital': {'name': '数字艺术', 'extensions': ['jpg', 'png', 'gif', 'mp4']},
    'craft': {'name': '手工艺品', 'extensions': ['jpg', 'png']},
    'video': {'name': '视频作品', 'extensions': ['mp4', 'avi', 'mov']},
    'music': {'name': '音乐作品', 'extensions': ['mp3', 'wav', 'flac']}
}

# 社团类型
CLUB_TYPES = {
    'choir': {'name': '合唱团', 'category': 'music'},
    'band': {'name': '乐队', 'category': 'music'},
    'orchestra': {'name': '管弦乐团', 'category': 'music'},
    'dance_club': {'name': '舞蹈社', 'category': 'dance'},
    'art_club': {'name': '美术社', 'category': 'fine_art'},
    'calligraphy_club': {'name': '书法社', 'category': 'calligraphy'},
    'drama_club': {'name': '戏剧社', 'category': 'drama'},
    'photo_club': {'name': '摄影社', 'category': 'photography'},
    'literature_club': {'name': '文学社', 'category': 'literature'},
    'traditional_culture': {'name': '传统文化社', 'category': 'culture'}
}

# 非遗项目
HERITAGE_ITEMS = {
    'calligraphy': {'name': '中国书法', 'level': 'world'},
    'paper_cutting': {'name': '剪纸', 'level': 'world'},
    'peking_opera': {'name': '京剧', 'level': 'world'},
    'tea_ceremony': {'name': '茶艺', 'level': 'national'},
    'guqin': {'name': '古琴艺术', 'level': 'world'},
    'chinese_painting': {'name': '中国画', 'level': 'national'},
    'ceramics': {'name': '陶瓷艺术', 'level': 'national'},
    'silk_craft': {'name': '丝绸技艺', 'level': 'world'}
}


class ArtsCultureService:
    """艺术与文化管理服务"""

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
                    CREATE TABLE IF NOT EXISTS art_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        art_category TEXT NOT NULL,
                        sub_category TEXT,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        is_grade_prep INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS art_enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cultural_events (
                        event_id TEXT PRIMARY KEY,
                        event_name TEXT NOT NULL,
                        event_type TEXT,
                        art_category TEXT,
                        organizer TEXT,
                        description TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        requires_tickets INTEGER DEFAULT 0,
                        ticket_price REAL DEFAULT 0,
                        tickets_sold INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        cover_image TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS event_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL,
                        student_id INTEGER,
                        student_name TEXT,
                        register_time TEXT,
                        ticket_no TEXT,
                        seat_number TEXT,
                        status TEXT DEFAULT 'registered',
                        attended INTEGER DEFAULT 0,
                        UNIQUE(event_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS artworks (
                        artwork_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
        artwork_type TEXT,
                        art_category TEXT,
                        artist_id INTEGER,
                        artist_name TEXT,
                        education_type TEXT,
                        creation_date TEXT,
                        description TEXT,
                        file_url TEXT,
                        thumbnail_url TEXT,
                        medium TEXT,
                        dimensions TEXT,
                        exhibition_id TEXT,
                        is_displayed INTEGER DEFAULT 0,
                        views INTEGER DEFAULT 0,
                        average_rating REAL DEFAULT 0,
                        rating_count INTEGER DEFAULT 0,
                        awards TEXT,
                        status TEXT DEFAULT 'submitted',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS artwork_ratings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        artwork_id TEXT NOT NULL,
                        rater_id INTEGER,
                        rater_name TEXT,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        created_at TEXT,
                        UNIQUE(artwork_id, rater_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exhibitions (
                        exhibition_id TEXT PRIMARY KEY,
                        exhibition_name TEXT NOT NULL,
                        theme TEXT,
                        description TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        curator TEXT,
                        artwork_count INTEGER DEFAULT 0,
                        visitor_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'planned',
                        cover_image TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS grade_exams (
                        exam_id TEXT PRIMARY KEY,
                        grade_system TEXT,
                        organization TEXT,
                        level INTEGER,
                        exam_date TEXT,
                        registration_deadline TEXT,
                        location TEXT,
                        fee REAL,
                        max_participants INTEGER DEFAULT 50,
                        registered_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS grade_results (
                        result_id TEXT PRIMARY KEY,
                        exam_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        applied_level INTEGER,
                        result TEXT,
                        score REAL,
                        certificate_no TEXT,
                        certificate_url TEXT,
                        exam_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS art_clubs (
                        club_id TEXT PRIMARY KEY,
                        club_name TEXT NOT NULL,
                        club_type TEXT,
                        art_category TEXT,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        advisor_id INTEGER,
                        advisor_name TEXT,
                        member_count INTEGER DEFAULT 1,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        founded_date TEXT,
                        logo_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        club_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        role TEXT DEFAULT 'member',
                        joined_at TEXT,
                        UNIQUE(club_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS heritage_programs (
                        program_id TEXT PRIMARY KEY,
                        heritage_name TEXT NOT NULL,
                        heritage_type TEXT,
                        level TEXT,
                        description TEXT,
                        instructor TEXT,
                        schedule TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('艺术与文化管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 艺术课程 ==========

    def create_art_course(self, course_name: str, art_category: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"art_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO art_courses (
                            course_id, course_name, art_category, sub_category,
                            teacher_id, teacher_name, education_type, grade_level,
                            semester, weekly_hours, location, max_students,
                            enrolled_count, description, is_grade_prep, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?)
                    ''', (course_id, course_name, art_category,
                          kwargs.get('sub_category'),
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('semester'), kwargs.get('weekly_hours', 2),
                          kwargs.get('location'), kwargs.get('max_students', 30),
                          kwargs.get('description'),
                          kwargs.get('is_grade_prep', 0), now, now))
                    conn.commit()
                    logger.info(f'创建艺术课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建艺术课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_art_course(self, course_id: str, student_id: int,
                           student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM art_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO art_enrollments (course_id, student_id, student_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (course_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE art_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'艺术选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_art_score(self, course_id: str, student_id: int,
                          score: float) -> Dict[str, Any]:
        try:
            grade = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE art_enrollments SET final_score = ?, grade = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录艺术成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 文艺活动 ==========

    def create_event(self, event_name: str, event_type: str,
                      start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"cev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EVENT_TYPES.get(event_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cultural_events (
                            event_id, event_name, event_type, art_category,
                            organizer, description, location, start_date, end_date,
                            start_time, end_time, max_participants,
                            registered_count, requires_tickets, ticket_price,
                            tickets_sold, status, cover_image, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 0, 'scheduled', ?, ?, ?, ?)
                    ''', (event_id, event_name, event_type,
                          kwargs.get('art_category'), kwargs.get('organizer'),
                          kwargs.get('description'), kwargs.get('location'),
                          start_date, kwargs.get('end_date'),
                          kwargs.get('start_time', '19:00'),
                          kwargs.get('end_time', '21:00'),
                          kwargs.get('max_participants', 100),
                          1 if config.get('requires_tickets') else 0,
                          kwargs.get('ticket_price', 0),
                          kwargs.get('cover_image'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建文艺活动: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'创建文艺活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_event(self, event_id: str, student_id: int,
                        student_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status, requires_tickets FROM cultural_events WHERE event_id = ?', (event_id,))
                    event = cursor.fetchone()
                    if not event:
                        return {'success': False, 'error': '活动不存在'}
                    if event[2] != 'scheduled':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if event[0] and event[1] >= event[0]:
                        return {'success': False, 'error': '名额已满'}
                    ticket_no = f"TKT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if event[3] else None
                    cursor.execute('''
                        INSERT OR IGNORE INTO event_registrations (event_id, student_id, student_name, register_time, ticket_no, status)
                        VALUES (?, ?, ?, ?, ?, 'registered')
                    ''', (event_id, student_id, student_name, now, ticket_no))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE cultural_events SET registered_count = registered_count + 1, updated_at = ? WHERE event_id = ?', (now, event_id))
                        if event[3]:
                            cursor.execute('UPDATE cultural_events SET tickets_sold = tickets_sold + 1 WHERE event_id = ?', (event_id,))
                        conn.commit()
                        return {'success': True, 'ticket_no': ticket_no}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 作品管理 ==========

    def submit_artwork(self, title: str, artwork_type: str,
                        artist_id: int, artist_name: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            artwork_id = f"awk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO artworks (
                            artwork_id, title, artwork_type, art_category,
                            artist_id, artist_name, education_type,
                            creation_date, description, file_url, thumbnail_url,
                            medium, dimensions, exhibition_id, is_displayed,
                            views, average_rating, rating_count, awards,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, 0, 0, 0, ?, 'submitted', ?, ?)
                    ''', (artwork_id, title, artwork_type,
                          kwargs.get('art_category'), artist_id, artist_name,
                          kwargs.get('education_type'),
                          kwargs.get('creation_date', now[:10]),
                          kwargs.get('description'), kwargs.get('file_url'),
                          kwargs.get('thumbnail_url'), kwargs.get('medium'),
                          kwargs.get('dimensions'), kwargs.get('awards'),
                          now, now))
                    conn.commit()
                    logger.info(f'提交作品: {title} ({artwork_id})')
                    return {'success': True, 'artwork_id': artwork_id}
        except Exception as e:
            logger.error(f'提交作品失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_artwork(self, artwork_id: str, approved: bool,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE artworks SET status = ?, updated_at = ? WHERE artwork_id = ? AND status = ?',
                                 (status, now, artwork_id, 'submitted'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '作品状态不允许审核'}
        except Exception as e:
            logger.error(f'审核作品失败: {e}')
            return {'success': False, 'error': str(e)}

    def rate_artwork(self, artwork_id: str, rater_id: int,
                      rating: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO artwork_ratings (artwork_id, rater_id, rater_name, rating, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (artwork_id, rater_id, kwargs.get('rater_name'), rating, kwargs.get('comment'), now))
                    cursor.execute('SELECT AVG(rating), COUNT(*) FROM artwork_ratings WHERE artwork_id = ?', (artwork_id,))
                    stats = cursor.fetchone()
                    avg = round(stats[0], 1) if stats[0] else 0
                    count = stats[1] or 0
                    cursor.execute('UPDATE artworks SET average_rating = ?, rating_count = ?, updated_at = ? WHERE artwork_id = ?',
                                 (avg, count, now, artwork_id))
                    conn.commit()
                    return {'success': True, 'average_rating': avg, 'rating_count': count}
        except Exception as e:
            logger.error(f'评价作品失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_artworks(self, art_category: str = None, artwork_type: str = None,
                       status: str = 'approved', page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM artworks WHERE 1=1'
                params = []
                if art_category:
                    query += ' AND art_category = ?'
                    params.append(art_category)
                if artwork_type:
                    query += ' AND artwork_type = ?'
                    params.append(artwork_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                artworks = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'artworks': artworks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取作品列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 展览管理 ==========

    def create_exhibition(self, exhibition_name: str, start_date: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            exhibition_id = f"exh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO exhibitions (
                            exhibition_name, theme, description, location,
                            start_date, end_date, curator, artwork_count,
                            visitor_count, status, cover_image, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 'planned', ?, ?, ?)
                    ''', (exhibition_name, kwargs.get('theme'),
                          kwargs.get('description'), kwargs.get('location'),
                          start_date, kwargs.get('end_date'),
                          kwargs.get('curator'), kwargs.get('cover_image'),
                          now, now))
                    cursor.execute('UPDATE exhibitions SET exhibition_id = ? WHERE exhibition_name = ? AND start_date = ?', (exhibition_id, exhibition_name, start_date))
                    conn.commit()
                    logger.info(f'创建展览: {exhibition_name} ({exhibition_id})')
                    return {'success': True, 'exhibition_id': exhibition_id}
        except Exception as e:
            logger.error(f'创建展览失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_to_exhibition(self, artwork_id: str, exhibition_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE artworks SET exhibition_id = ?, is_displayed = 1, updated_at = ? WHERE artwork_id = ?',
                                 (exhibition_id, now, artwork_id))
                    cursor.execute('UPDATE exhibitions SET artwork_count = artwork_count + 1, updated_at = ? WHERE exhibition_id = ?', (now, exhibition_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'加入展览失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 艺术考级 ==========

    def create_grade_exam(self, grade_system: str, level: int,
                           exam_date: str, **kwargs) -> Dict[str, Any]:
        try:
            exam_id = f"gre_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = GRADE_SYSTEMS.get(grade_system, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO grade_exams (
                            exam_id, grade_system, organization, level,
                            exam_date, registration_deadline, location, fee,
                            max_participants, registered_count, description,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'open', ?, ?)
                    ''', (exam_id, grade_system, kwargs.get('organization', config.get('organizations', [''])[0]),
                          level, exam_date, kwargs.get('registration_deadline'),
                          kwargs.get('location'), kwargs.get('fee', 0),
                          kwargs.get('max_participants', 50),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    return {'success': True, 'exam_id': exam_id}
        except Exception as e:
            logger.error(f'创建考级失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_grade_exam(self, exam_id: str, student_id: int,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM grade_exams WHERE exam_id = ?', (exam_id,))
                    exam = cursor.fetchone()
                    if not exam:
                        return {'success': False, 'error': '考级不存在'}
                    if exam[2] != 'open':
                        return {'success': False, 'error': '考级报名已关闭'}
                    if exam[0] and exam[1] >= exam[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('SELECT exam_id FROM grade_results WHERE exam_id = ? AND student_id = ?', (exam_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该考级'}
                    cursor.execute('''
                        INSERT INTO grade_results (result_id, exam_id, student_id, student_name, applied_level, exam_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (f"grs_{uuid.uuid4().hex[:12]}", exam_id, student_id,
                          kwargs.get('student_name'),
                          kwargs.get('applied_level'),
                          kwargs.get('exam_date'), now))
                    cursor.execute('UPDATE grade_exams SET registered_count = registered_count + 1, updated_at = ? WHERE exam_id = ?', (now, exam_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'考级报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_grade_result(self, result_id: str, result: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            certificate_no = f"GRC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if result == 'pass' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE grade_results SET
                            result = ?, score = ?, certificate_no = ?,
                            certificate_url = ?
                        WHERE result_id = ?
                    ''', (result, kwargs.get('score'), certificate_no,
                          kwargs.get('certificate_url'), result_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'certificate_no': certificate_no}
                    return {'success': False, 'error': '考级结果不存在'}
        except Exception as e:
            logger.error(f'记录考级结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 艺术社团 ==========

    def create_club(self, club_name: str, club_type: str,
                     leader_id: int, leader_name: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            club_id = f"clb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CLUB_TYPES.get(club_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO art_clubs (
                            club_id, club_name, club_type, art_category,
                            description, leader_id, leader_name, advisor_id,
                            advisor_name, member_count, education_type,
                            is_active, founded_date, logo_url, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 1, ?, ?, ?, ?)
                    ''', (club_id, club_name, club_type,
                          kwargs.get('art_category', config.get('category')),
                          kwargs.get('description'), leader_id, leader_name,
                          kwargs.get('advisor_id'), kwargs.get('advisor_name'),
                          kwargs.get('education_type'),
                          kwargs.get('founded_date', now[:10]),
                          kwargs.get('logo_url'), now, now))
                    cursor.execute('INSERT INTO club_members (club_id, student_id, student_name, role, joined_at) VALUES (?, ?, ?, \'leader\', ?)',
                                 (club_id, leader_id, leader_name, now))
                    conn.commit()
                    logger.info(f'创建艺术社团: {club_name} ({club_id})')
                    return {'success': True, 'club_id': club_id}
        except Exception as e:
            logger.error(f'创建艺术社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_club(self, club_id: str, student_id: int,
                   student_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO club_members (club_id, student_id, student_name, role, joined_at) VALUES (?, ?, ?, \'member\', ?)',
                                 (club_id, student_id, student_name, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE art_clubs SET member_count = member_count + 1, updated_at = ? WHERE club_id = ?', (now, club_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该社团'}
        except Exception as e:
            logger.error(f'加入社团失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 非遗传承 ==========

    def create_heritage_program(self, heritage_name: str, heritage_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"hrg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = HERITAGE_ITEMS.get(heritage_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO heritage_programs (
                            program_id, heritage_name, heritage_type, level,
                            description, instructor, schedule, location,
                            max_participants, enrolled_count, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
                    ''', (program_id, heritage_name, heritage_type,
                          kwargs.get('level', config.get('level', 'national')),
                          kwargs.get('description'), kwargs.get('instructor'),
                          kwargs.get('schedule'), kwargs.get('location'),
                          kwargs.get('max_participants', 30), now, now))
                    conn.commit()
                    logger.info(f'创建非遗项目: {heritage_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建非遗项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_heritage_programs(self, is_active: bool = True,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM heritage_programs WHERE 1=1'
                params = []
                if is_active is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if is_active else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取非遗项目列表失败: {e}')
            return {'success': False, 'error': str(e)}
