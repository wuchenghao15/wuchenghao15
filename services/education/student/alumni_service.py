from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 校友服务 (v15.5.0) ==================================== 提供校友档案管理、校友活动、校友联络和捐赠管理等综合服务。  核心能力： 1. 校友档案 - 校友信息、毕业信息、职业发展 2. 校友活动 - 活动组织、报名参与 3. 校友联络 - 校友通讯录、班级联络 4. 捐赠管理 - 捐赠登记、捐赠公示 5. 校友分会 - 地区分会、行业分会 6. 就业服务 - 校友招聘、实习推荐 7. 成教校友 - 成人教育校友管理 8. K12校友 - 九年制毕业校友管理 """
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alumni_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Alumni')


# ========== 校友配置 ==========

# 校友等级
ALUMNI_LEVELS = {
    1: {'name': '普通校友', 'perks': ['校友通讯录', '活动参与']},
    2: {'name': '活跃校友', 'perks': ['普通校友权益', '优先报名', '专属活动']},
    3: {'name': '贡献校友', 'perks': ['活跃校友权益', '捐赠荣誉', '校友会席位']},
    4: {'name': '卓越校友', 'perks': ['贡献校友权益', '导师资格', '校董会列席']},
    5: {'name': '荣誉校友', 'perks': ['卓越校友权益', '终身荣誉', '名誉头衔']}
}

# 校友身份认证状态
ALUMNI_STATUS = {
    'pending': {'name': '待认证', 'color': '#faad14'},
    'verified': {'name': '已认证', 'color': '#52c41a'},
    'rejected': {'name': '认证失败', 'color': '#f5222d'},
    'suspended': {'name': '已暂停', 'color': '#8c8c8c'}
}

# 活动类型
EVENT_TYPES = {
    'reunion': {'name': '同学聚会', 'icon': 'team'},
    'forum': {'name': '校友论坛', 'icon': 'message'},
    'lecture': {'name': '讲座分享', 'icon': 'book'},
    'career': {'name': '职业发展', 'icon': 'briefcase'},
    'charity': {'name': '公益活动', 'icon': 'heart'},
    'sports': {'name': '体育活动', 'icon': 'trophy'},
    'cultural': {'name': '文化活动', 'icon': 'star'},
    'annual': {'name': '年会庆典', 'icon': 'calendar'}
}

# 活动状态
EVENT_STATUS = {
    'draft': '草稿',
    'published': '已发布',
    'registration': '报名中',
    'full': '报名已满',
    'ongoing': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
}

# 捐赠类型
DONATION_TYPES = {
    'general': {'name': '一般捐赠', 'use': '学校发展'},
    'scholarship': {'name': '奖学金捐赠', 'use': '学生奖学金'},
    'infrastructure': {'name': '基础设施', 'use': '校园建设'},
    'research': {'name': '科研基金', 'use': '科研支持'},
    'library': {'name': '图书馆基金', 'use': '图书资源'},
    'specific': {'name': '定向捐赠', 'use': '指定用途'},
    'in_kind': {'name': '实物捐赠', 'use': '物资捐赠'}
}

# 校友会/分会类型
CHAPTER_TYPES = {
    'geographic': {'name': '地区分会', 'description': '按地区组织的校友分会'},
    'industry': {'name': '行业分会', 'description': '按行业组织的校友分会'},
    'interest': {'name': '兴趣分会', 'description': '按兴趣爱好组织的校友分会'},
    'class': {'name': '班级分会', 'description': '按班级组织的校友分会'},
    'major': {'name': '专业分会', 'description': '按专业组织的校友分会'}
}

# 就业服务类型
CAREER_TYPES = {
    'job_posting': {'name': '招聘信息', 'description': '校友企业招聘'},
    'internship': {'name': '实习机会', 'description': '实习岗位推荐'},
    'mentor': {'name': '导师计划', 'description': '校友导师指导'},
    'career_talk': {'name': '职业讲座', 'description': '职业发展讲座'},
    'networking': {'name': '人脉拓展', 'description': '行业人脉交流'}
}


class AlumniService:
    """校友服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS alumni_profiles ( alumni_id TEXT PRIMARY KEY, user_id INTEGER UNIQUE, real_name TEXT NOT NULL, gender TEXT, birth_date TEXT, phone TEXT, email TEXT, education_type TEXT, graduation_year TEXT, graduation_semester TEXT, grade_level INTEGER, class_id TEXT, major TEXT, degree TEXT, current_city TEXT, current_company TEXT, current_position TEXT, industry TEXT, bio TEXT, avatar_url TEXT, level INTEGER DEFAULT 1, status TEXT DEFAULT 'pending', verified_at TEXT, join_date TEXT, last_active TEXT, total_donation REAL DEFAULT 0, total_events INTEGER DEFAULT 0, points INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS alumni_events ( event_id TEXT PRIMARY KEY, event_name TEXT NOT NULL, event_type TEXT, organizer TEXT, description TEXT, location TEXT, city TEXT, start_date TEXT, end_date TEXT, registration_start TEXT, registration_end TEXT, max_participants INTEGER DEFAULT 50, current_participants INTEGER DEFAULT 0, fee REAL DEFAULT 0, status TEXT DEFAULT 'draft', cover_image TEXT, created_by INTEGER, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS event_registrations ( id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL, alumni_id TEXT NOT NULL, register_time TEXT, status TEXT DEFAULT 'registered', attendance INTEGER DEFAULT 0, guest_count INTEGER DEFAULT 0, fee_paid INTEGER DEFAULT 0, remark TEXT, created_at TEXT, UNIQUE(event_id, alumni_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS donations ( donation_id TEXT PRIMARY KEY, alumni_id TEXT, donor_name TEXT NOT NULL, donation_type TEXT NOT NULL, amount REAL, in_kind_description TEXT, purpose TEXT, anonymous INTEGER DEFAULT 0, message TEXT, status TEXT DEFAULT 'pending', payment_method TEXT, transaction_no TEXT, received_at TEXT, acknowledged INTEGER DEFAULT 0, acknowledgement_sent_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS alumni_chapters ( chapter_id TEXT PRIMARY KEY, chapter_name TEXT NOT NULL, chapter_type TEXT, description TEXT, region TEXT, industry TEXT, president_alumni_id TEXT, member_count INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, founded_date TEXT, avatar_url TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS chapter_members ( id INTEGER PRIMARY KEY AUTOINCREMENT, chapter_id TEXT NOT NULL, alumni_id TEXT NOT NULL, role TEXT DEFAULT 'member', joined_at TEXT, UNIQUE(chapter_id, alumni_id) ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS career_opportunities ( opportunity_id TEXT PRIMARY KEY, alumni_id TEXT NOT NULL, company_name TEXT, position_title TEXT NOT NULL, career_type TEXT, location TEXT, salary_range TEXT, description TEXT, requirements TEXT, contact_email TEXT, status TEXT DEFAULT 'active', views INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS mentor_programs ( program_id TEXT PRIMARY KEY, mentor_alumni_id TEXT NOT NULL, industry TEXT, expertise TEXT, capacity INTEGER DEFAULT 5, current_mentees INTEGER DEFAULT 0, description TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS alumni_news ( news_id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT, category TEXT, author TEXT, cover_image TEXT, views INTEGER DEFAULT 0, is_published INTEGER DEFAULT 0, published_at TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS class_reunions ( reunion_id TEXT PRIMARY KEY, class_id TEXT NOT NULL, graduation_year TEXT, reunion_year TEXT, event_name TEXT, location TEXT, date TEXT, organizer TEXT, attendee_count INTEGER DEFAULT 0, photo_album TEXT, description TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('校友服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 校友档案 ==========

    def register_alumni(self, real_name: str, **kwargs) -> Dict[str, Any]:
        try:
            alumni_id = f"alm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO alumni_profiles ( alumni_id, user_id, real_name, gender, birth_date, phone, email, education_type, graduation_year, graduation_semester, grade_level, class_id, major, degree, current_city, current_company, current_position, industry, bio, avatar_url, level, status, join_date, last_active, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'pending', ?, ?, ?, ?) ''', (alumni_id, kwargs.get('user_id'), real_name,
                          kwargs.get('gender'), kwargs.get('birth_date'),
                          kwargs.get('phone'), kwargs.get('email'),
                          kwargs.get('education_type'), kwargs.get('graduation_year'),
                          kwargs.get('graduation_semester'), kwargs.get('grade_level'),
                          kwargs.get('class_id'), kwargs.get('major'),
                          kwargs.get('degree'), kwargs.get('current_city'),
                          kwargs.get('current_company'), kwargs.get('current_position'),
                          kwargs.get('industry'), kwargs.get('bio'),
                          kwargs.get('avatar_url'), now, now, now, now))
                    conn.commit()
                    logger.info(f'注册校友: {real_name} ({alumni_id})')
                    return {'success': True, 'alumni_id': alumni_id}
        except Exception as e:
            logger.error(f'注册校友失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_alumni(self, alumni_id: str, verified: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'verified' if verified else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE alumni_profiles SET status = ?, verified_at = ?, updated_at = ? WHERE alumni_id = ? AND status = 'pending' ''', (status, now if verified else None, now, alumni_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'校友认证: {alumni_id} -> {status}')
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '校友不存在或状态不允许认证'}
        except Exception as e:
            logger.error(f'校友认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alumni_profile(self, alumni_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM alumni_profiles WHERE alumni_id = ?', (alumni_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f'获取校友档案失败: {e}')
            return None

    def search_alumni(self, keyword: str = None, education_type: str = None,
                       graduation_year: str = None, industry: str = None,
                       city: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT alumni_id, real_name, graduation_year, major, current_city, current_company, current_position, industry, level, status FROM alumni_profiles WHERE status = 'verified'"
                params = []
                if keyword:
                    query += ' AND ( real_name LIKE ? OR current_company LIKE ? OR current_position LIKE ? OR major LIKE ?)'
                    kw = f'%{keyword}%'
                    params.extend([kw, kw, kw, kw])
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if graduation_year:
                    query += ' AND graduation_year = ?'
                    params.append(graduation_year)
                if industry:
                    query += ' AND industry = ?'
                    params.append(industry)
                if city:
                    query += ' AND current_city = ?'
                    params.append(city)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY level DESC, graduation_year DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alumni = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alumni': alumni, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索校友失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_alumni_profile(self, alumni_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            update_fields = []
            params = []
            for field in ['current_city', 'current_company', 'current_position', 'industry', 'bio', 'phone', 'email',
            'avatar_url']:
                if field in kwargs:
                    update_fields.append(f'{field} = ?')
                    params.append(kwargs[field])
            if not update_fields:
                return {'success': False, 'error': '没有可更新的字段'}
            update_fields.append('updated_at = ?')
            params.extend([now, alumni_id])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE alumni_profiles SET {", ".join(update_fields)} WHERE alumni_id = ?', params)
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新校友档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 校友活动 ==========

    def create_event(self, event_name: str, event_type: str,
                      start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"evt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO alumni_events ( event_id, event_name, event_type, organizer, description, location, city, start_date, end_date, registration_start, registration_end, max_participants, fee, status, cover_image, created_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?) ''', (event_id, event_name, event_type,
                          kwargs.get('organizer', ''), kwargs.get('description'),
                          kwargs.get('location'), kwargs.get('city'),
                          start_date, kwargs.get('end_date'),
                          kwargs.get('registration_start'),
                          kwargs.get('registration_end'),
                          kwargs.get('max_participants', 50),
                          kwargs.get('fee', 0), kwargs.get('cover_image'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建校友活动: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'创建活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_event(self, event_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE alumni_events SET status = 'published', updated_at = ? WHERE event_id = ? AND status = 'draft' ''', (now, event_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '活动状态不允许发布'}
        except Exception as e:
            logger.error(f'发布活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_event(self, event_id: str, alumni_id: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, current_participants, status FROM alumni_events WHERE event_id = ?', (event_id,))
                    event = cursor.fetchone()
                    if not event:
                        return {'success': False, 'error': '活动不存在'}
                    if event[2] not in ('published', 'registration'):
                        return {'success': False, 'error': f'活动状态不允许报名: {event[2]}'}
                    if event[0] and event[1] >= event[0]:
                        return {'success': False, 'error': '活动名额已满'}
                    cursor.execute(''' INSERT OR IGNORE INTO event_registrations (event_id, alumni_id, register_time, guest_count, status, created_at) VALUES (?, ?, ?, ?, 'registered', ?) ''', (event_id, alumni_id, now, kwargs.get('guest_count', 0), now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE alumni_events SET current_participants = current_participants + 1, updated_at = ? WHERE event_id = ?', (now, event_id))
                        cursor.execute('UPDATE alumni_profiles SET total_events = total_events + 1, last_active = ?, updated_at = ? WHERE alumni_id = ?', (now, now, alumni_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_events(self, event_type: str = None, status: str = 'published',
                    city: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM alumni_events WHERE 1=1'
                params = []
                if event_type:
                    query += ' AND event_type = ?'
                    params.append(event_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if city:
                    query += ' AND city = ?'
                    params.append(city)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                events = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'events': events, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_event_registrations(self, event_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(''' SELECT er.*, ap.real_name, ap.current_city, ap.current_company FROM event_registrations er JOIN alumni_profiles ap ON er.alumni_id = ap.alumni_id WHERE er.event_id = ? ORDER BY er.register_time ''', (event_id,))
                registrations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'registrations': registrations, 'count': len(registrations)}
        except Exception as e:
            logger.error(f'获取活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 捐赠管理 ==========

    def record_donation(self, donor_name: str, donation_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            donation_id = f"don_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO donations ( donation_id, alumni_id, donor_name, donation_type, amount, in_kind_description, purpose, anonymous, message, status, payment_method, transaction_no, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'received', ?, ?, ?, ?) ''', (donation_id, kwargs.get('alumni_id'), donor_name,
                          donation_type, kwargs.get('amount'),
                          kwargs.get('in_kind_description'), kwargs.get('purpose'),
                          kwargs.get('anonymous', 0), kwargs.get('message'),
                          kwargs.get('payment_method'), kwargs.get('transaction_no'),
                          now, now))
                    if kwargs.get('alumni_id') and kwargs.get('amount'):
                        cursor.execute('UPDATE alumni_profiles SET total_donation = total_donation + ?, points = points + ?, updated_at = ? WHERE alumni_id = ?',
                                     (kwargs['amount'], int(kwargs['amount']), now, kwargs['alumni_id']))
                    conn.commit()
                    logger.info(f'记录捐赠: {donation_id}, 金额{kwargs.get("amount", 0)}')
                    return {'success': True, 'donation_id': donation_id}
        except Exception as e:
            logger.error(f'记录捐赠失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_donation_statistics(self, education_type: str = None,
                                 year: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = ''' SELECT COUNT(*) as total_donations, COALESCE(SUM(amount), 0) as total_amount, COUNT(DISTINCT alumni_id) as donor_count FROM donations WHERE status = 'received' '''
                params = []
                if year:
                    query += ' AND strftime("%Y", created_at) = ?'
                    params.append(year)
                cursor.execute(query, params)
                row = cursor.fetchone()
                cursor.execute('SELECT donation_type, COUNT(*), COALESCE(SUM(amount), 0) FROM donations WHERE status = ? GROUP BY donation_type', ('received',))
                by_type = {r[0]: {'count': r[1], 'amount': r[2]} for r in cursor.fetchall()}
                return {
                    'success': True,
                    'stats': {
                        'total_donations': row[0],
                        'total_amount': round(row[1], 2),
                        'donor_count': row[2],
                        'by_type': by_type
                    }
                }
        except Exception as e:
            logger.error(f'获取捐赠统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 校友分会 ==========

    def create_chapter(self, chapter_name: str, chapter_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            chapter_id = f"chp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO alumni_chapters ( chapter_id, chapter_name, chapter_type, description, region, industry, president_alumni_id, is_active, founded_date, avatar_url, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?) ''', (chapter_id, chapter_name, chapter_type,
                          kwargs.get('description'), kwargs.get('region'),
                          kwargs.get('industry'), kwargs.get('president_alumni_id'),
                          kwargs.get('founded_date'), kwargs.get('avatar_url'),
                          now, now))
                    if kwargs.get('president_alumni_id'):
                        cursor.execute(''' INSERT OR IGNORE INTO chapter_members (chapter_id, alumni_id, role, joined_at) VALUES (?, ?, 'president', ?) ''', (chapter_id, kwargs['president_alumni_id'], now))
                    conn.commit()
                    logger.info(f'创建校友分会: {chapter_name} ({chapter_id})')
                    return {'success': True, 'chapter_id': chapter_id}
        except Exception as e:
            logger.error(f'创建分会失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_chapter(self, chapter_id: str, alumni_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO chapter_members (chapter_id, alumni_id, role, joined_at) VALUES (?, ?, \'member\', ?)',
                                 (chapter_id, alumni_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE alumni_chapters SET member_count = member_count + 1, updated_at = ? WHERE chapter_id = ?', (now, chapter_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该分会'}
        except Exception as e:
            logger.error(f'加入分会失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_chapters(self, chapter_type: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM alumni_chapters WHERE is_active = 1"
                params = []
                if chapter_type:
                    query += ' AND chapter_type = ?'
                    params.append(chapter_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY member_count DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                chapters = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'chapters': chapters, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取分会列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 就业服务 ==========

    def post_opportunity(self, alumni_id: str, position_title: str,
                          company_name: str, **kwargs) -> Dict[str, Any]:
        try:
            opportunity_id = f"job_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO career_opportunities ( opportunity_id, alumni_id, company_name, position_title, career_type, location, salary_range, description, requirements, contact_email, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (opportunity_id, alumni_id, company_name, position_title,
                          kwargs.get('career_type'), kwargs.get('location'),
                          kwargs.get('salary_range'), kwargs.get('description'),
                          kwargs.get('requirements'), kwargs.get('contact_email'),
                          now, now))
                    conn.commit()
                    logger.info(f'发布职位: {position_title} ({opportunity_id})')
                    return {'success': True, 'opportunity_id': opportunity_id}
        except Exception as e:
            logger.error(f'发布职位失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_opportunities(self, career_type: str = None, location: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM career_opportunities WHERE status = 'active'"
                params = []
                if career_type:
                    query += ' AND career_type = ?'
                    params.append(career_type)
                if location:
                    query += ' AND location LIKE ?'
                    params.append(f'%{location}%')
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                opportunities = [dict(o) for o in cursor.fetchall()]
                return {'success': True, 'opportunities': opportunities, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取职位列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 校友会统计 ==========

    def get_alumni_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT COUNT(*), COUNT(CASE WHEN status = 'verified' THEN 1 END) FROM alumni_profiles WHERE 1=1"
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                row = cursor.fetchone()
                cursor.execute('SELECT graduation_year, COUNT( *) FROM alumni_profiles WHERE status = ? GROUP BY graduation_year ORDER BY graduation_year DESC LIMIT 10', ('verified',))
                by_year = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT industry, COUNT( *) FROM alumni_profiles WHERE status = ? AND industry IS NOT NULL GROUP BY industry ORDER BY COUNT( *) DESC LIMIT 10', ('verified',))
                by_industry = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'success': True,
                    'stats': {
                        'total_registered': row[0],
                        'total_verified': row[1],
                        'by_graduation_year': by_year,
                        'by_industry': by_industry
                    }
                }
        except Exception as e:
            logger.error(f'获取校友统计失败: {e}')
            return {'success': False, 'error': str(e)}
