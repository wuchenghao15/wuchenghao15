#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 社区服务与志愿管理服务 (v15.7.0)
====================================
提供志愿活动、社区合作、服务时长和社会实践等综合管理服务。

核心能力：
1. 志愿活动 - 活动发布、报名管理、签到签退
2. 社区合作 - 社区结对、服务基地、合作项目
3. 服务时长 - 时长记录、统计排名、证书管理
4. 社会实践 - 实践项目、调研报告、成果展示
5. 公益捐赠 - 物资募集、捐赠记录、公示管理
6. 志愿团队 - 团队组建、分工管理、绩效评估
7. 成人志愿 - 成人教育社会责任管理
8. K12实践 - 学生社会实践与劳动教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'community_volunteer_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CommunityVolunteer')


# ========== 志愿服务配置 ==========

# 活动类型
ACTIVITY_TYPES = {
    'elderly_care': {'name': '敬老服务', 'category': '助老', 'icon': 'heart'},
    'children_aid': {'name': '儿童帮扶', 'category': '助学', 'icon': 'child'},
    'environment': {'name': '环境保护', 'category': '环保', 'icon': 'tree'},
    'charity_sale': {'name': '义卖募捐', 'category': '公益', 'icon': 'gift'},
    'community_service': {'name': '社区服务', 'category': '社区', 'icon': 'home'},
    'cultural_promotion': {'name': '文化推广', 'category': '文化', 'icon': 'book'},
    'traffic_assist': {'name': '交通引导', 'category': '安全', 'icon': 'car'},
    'medical_assist': {'name': '医疗辅助', 'category': '健康', 'icon': 'medkit'},
    'disaster_relief': {'name': '灾害救助', 'category': '应急', 'icon': 'exclamation-triangle'},
    'animal_protection': {'name': '动物保护', 'category': '环保', 'icon': 'paw'},
    'education_support': {'name': '教育支援', 'category': '助学', 'icon': 'graduation-cap'},
    'poverty_alleviation': {'name': '扶贫济困', 'category': '公益', 'icon': 'hands-helping'}
}

# 活动状态
ACTIVITY_STATUS = {
    'draft': {'name': '草稿', 'color': '#d9d9d9'},
    'published': {'name': '已发布', 'color': '#1890ff'},
    'registration': {'name': '报名中', 'color': '#1890ff'},
    'full': {'name': '名额已满', 'color': '#faad14'},
    'ongoing': {'name': '进行中', 'color': '#52c41a'},
    'completed': {'name': '已完成', 'color': '#52c41a'},
    'cancelled': {'name': '已取消', 'color': '#f5222d'}
}

# 社区合作类型
COMMUNITY_PARTNERSHIP_TYPES = {
    'paired': {'name': '结对共建', 'description': '与社区建立长期结对关系'},
    'service_base': {'name': '服务基地', 'description': '设立志愿服务基地'},
    'project_based': {'name': '项目合作', 'description': '按项目开展合作'},
    'seasonal': {'name': '季节性合作', 'description': '按季节开展活动'},
    'emergency': {'name': '应急协作', 'description': '应急情况下的协作'}
}

# 实践类型
PRACTICE_TYPES = {
    'social_investigation': {'name': '社会调查', 'duration_days': 7, 'report_required': True},
    'volunteer_service': {'name': '志愿服务', 'duration_days': 3, 'report_required': False},
    'labor_practice': {'name': '劳动实践', 'duration_days': 5, 'report_required': True},
    'research_practice': {'name': '研究性实践', 'duration_days': 14, 'report_required': True},
    'career_exploration': {'name': '职业体验', 'duration_days': 5, 'report_required': True},
    'cultural_exchange': {'name': '文化交流', 'duration_days': 7, 'report_required': True}
}

# 志愿者等级
VOLUNTEER_LEVELS = {
    1: {'name': '注册志愿者', 'min_hours': 0, 'badge': 'bronze'},
    2: {'name': '一星志愿者', 'min_hours': 30, 'badge': 'silver'},
    3: {'name': '二星志愿者', 'min_hours': 60, 'badge': 'gold'},
    4: {'name': '三星志愿者', 'min_hours': 120, 'badge': 'platinum'},
    5: {'name': '四星志愿者', 'min_hours': 240, 'badge': 'diamond'},
    6: {'name': '五星志愿者', 'min_hours': 500, 'badge': 'crown'}
}

# 捐赠类型
DONATION_TYPES = {
    'money': {'name': '资金捐赠', 'unit': '元'},
    'books': {'name': '图书捐赠', 'unit': '本'},
    'clothes': {'name': '衣物捐赠', 'unit': '件'},
    'supplies': {'name': '学习用品', 'unit': '件'},
    'equipment': {'name': '设备捐赠', 'unit': '台'},
    'food': {'name': '食品捐赠', 'unit': '份'},
    'other': {'name': '其他物资', 'unit': '件'}
}


class CommunityVolunteerService:
    """社区服务与志愿管理服务"""

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
                    CREATE TABLE IF NOT EXISTS volunteer_profiles (
                        volunteer_id TEXT PRIMARY KEY,
                        user_id INTEGER UNIQUE,
                        real_name TEXT NOT NULL,
                        phone TEXT,
                        email TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        class_id TEXT,
                        skills TEXT,
                        interests TEXT,
                        total_hours REAL DEFAULT 0,
                        total_activities INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        badge TEXT DEFAULT 'bronze',
                        status TEXT DEFAULT 'active',
                        registered_at TEXT,
                        last_active TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volunteer_activities (
                        activity_id TEXT PRIMARY KEY,
                        activity_name TEXT NOT NULL,
                        activity_type TEXT,
                        organizer TEXT,
                        description TEXT,
                        location TEXT,
                        community TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        max_participants INTEGER DEFAULT 20,
                        current_participants INTEGER DEFAULT 0,
                        hours_per_volunteer REAL DEFAULT 2,
                        contact_person TEXT,
                        contact_phone TEXT,
                        status TEXT DEFAULT 'draft',
                        cover_image TEXT,
                        education_type TEXT,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id TEXT NOT NULL,
                        volunteer_id TEXT NOT NULL,
                        volunteer_name TEXT,
                        register_time TEXT,
                        status TEXT DEFAULT 'registered',
                        check_in_time TEXT,
                        check_out_time TEXT,
                        actual_hours REAL DEFAULT 0,
                        performance TEXT,
                        feedback TEXT,
                        rating INTEGER,
                        UNIQUE(activity_id, volunteer_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_partnerships (
                        partnership_id TEXT PRIMARY KEY,
                        community_name TEXT NOT NULL,
                        partnership_type TEXT,
                        contact_person TEXT,
                        contact_phone TEXT,
                        address TEXT,
                        description TEXT,
                        start_date TEXT,
                        is_active INTEGER DEFAULT 1,
                        total_activities INTEGER DEFAULT 0,
                        total_volunteers INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS social_practices (
                        practice_id TEXT PRIMARY KEY,
                        practice_name TEXT NOT NULL,
                        practice_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        duration_days INTEGER,
                        leader_id INTEGER,
                        leader_name TEXT,
                        participant_count INTEGER DEFAULT 0,
                        report_required INTEGER DEFAULT 1,
                        report_url TEXT,
                        report_status TEXT DEFAULT 'not_submitted',
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS practice_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        practice_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        role TEXT DEFAULT 'participant',
                        joined_at TEXT,
                        report_url TEXT,
                        score REAL,
                        UNIQUE(practice_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS donations (
                        donation_id TEXT PRIMARY KEY,
                        donor_name TEXT NOT NULL,
                        donor_id INTEGER,
                        donation_type TEXT,
                        amount REAL,
                        quantity INTEGER,
                        unit TEXT,
                        purpose TEXT,
                        recipient TEXT,
                        anonymous INTEGER DEFAULT 0,
                        message TEXT,
                        received_at TEXT,
                        acknowledged INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volunteer_teams (
                        team_id TEXT PRIMARY KEY,
                        team_name TEXT NOT NULL,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        member_count INTEGER DEFAULT 1,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        founded_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS team_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team_id TEXT NOT NULL,
                        volunteer_id TEXT NOT NULL,
                        volunteer_name TEXT,
                        role TEXT DEFAULT 'member',
                        joined_at TEXT,
                        UNIQUE(team_id, volunteer_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_certificates (
                        certificate_id TEXT PRIMARY KEY,
                        volunteer_id TEXT NOT NULL,
                        volunteer_name TEXT,
                        certificate_type TEXT,
                        title TEXT,
                        hours REAL,
                        issued_date TEXT,
                        issued_by TEXT,
                        verification_code TEXT,
                        file_url TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('社区服务与志愿管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 志愿者档案 ==========

    def register_volunteer(self, real_name: str, **kwargs) -> Dict[str, Any]:
        try:
            volunteer_id = f"vol_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO volunteer_profiles (
                            volunteer_id, user_id, real_name, phone, email,
                            education_type, grade_level, class_id, skills,
                            interests, total_hours, total_activities, level,
                            badge, status, registered_at, last_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 1, 'bronze', 'active', ?, ?, ?, ?)
                    ''', (volunteer_id, kwargs.get('user_id'), real_name,
                          kwargs.get('phone'), kwargs.get('email'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('class_id'), kwargs.get('skills'),
                          kwargs.get('interests'), now, now, now, now))
                    conn.commit()
                    logger.info(f'注册志愿者: {real_name} ({volunteer_id})')
                    return {'success': True, 'volunteer_id': volunteer_id}
        except Exception as e:
            logger.error(f'注册志愿者失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_volunteer_profile(self, volunteer_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM volunteer_profiles WHERE volunteer_id = ?', (volunteer_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f'获取志愿者档案失败: {e}')
            return None

    def _update_volunteer_level(self, cursor, volunteer_id: str, total_hours: float):
        new_level = 1
        new_badge = 'bronze'
        for level, config in sorted(VOLUNTEER_LEVELS.items()):
            if total_hours >= config['min_hours']:
                new_level = level
                new_badge = config['badge']
        now = datetime.now().isoformat()
        cursor.execute('UPDATE volunteer_profiles SET total_hours = ?, level = ?, badge = ?, updated_at = ? WHERE volunteer_id = ?',
                      (total_hours, new_level, new_badge, now, volunteer_id))

    # ========== 志愿活动 ==========

    def create_activity(self, activity_name: str, activity_type: str,
                         start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"act_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO volunteer_activities (
                            activity_id, activity_name, activity_type, organizer,
                            description, location, community, start_date, end_date,
                            start_time, end_time, max_participants,
                            current_participants, hours_per_volunteer,
                            contact_person, contact_phone, status, cover_image,
                            education_type, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'published', ?, ?, ?, ?, ?)
                    ''', (activity_id, activity_name, activity_type,
                          kwargs.get('organizer', ''), kwargs.get('description'),
                          kwargs.get('location'), kwargs.get('community'),
                          start_date, kwargs.get('end_date'),
                          kwargs.get('start_time', '09:00'),
                          kwargs.get('end_time', '12:00'),
                          kwargs.get('max_participants', 20),
                          kwargs.get('hours_per_volunteer', 2),
                          kwargs.get('contact_person'),
                          kwargs.get('contact_phone'),
                          kwargs.get('cover_image'),
                          kwargs.get('education_type'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建志愿活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建志愿活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_activity(self, activity_id: str, volunteer_id: str,
                           volunteer_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, current_participants, status FROM volunteer_activities WHERE activity_id = ?', (activity_id,))
                    act = cursor.fetchone()
                    if not act:
                        return {'success': False, 'error': '活动不存在'}
                    if act[2] not in ('published', 'registration'):
                        return {'success': False, 'error': f'活动状态不允许报名: {act[2]}'}
                    if act[0] and act[1] >= act[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO activity_registrations (activity_id, volunteer_id, volunteer_name, register_time, status)
                        VALUES (?, ?, ?, ?, 'registered')
                    ''', (activity_id, volunteer_id, volunteer_name, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE volunteer_activities SET current_participants = current_participants + 1, updated_at = ? WHERE activity_id = ?', (now, activity_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_in(self, activity_id: str, volunteer_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE activity_registrations SET check_in_time = ?, status = 'checked_in'
                        WHERE activity_id = ? AND volunteer_id = ? AND status = 'registered'
                    ''', (now, activity_id, volunteer_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'check_in_time': now}
                    return {'success': False, 'error': '报名记录不存在或状态不允许签到'}
        except Exception as e:
            logger.error(f'签到失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_out(self, activity_id: str, volunteer_id: str,
                   actual_hours: float = None, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT check_in_time FROM activity_registrations WHERE activity_id = ? AND volunteer_id = ? AND status = ?', (activity_id, volunteer_id, 'checked_in'))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '未找到签到记录'}
                    cursor.execute('SELECT hours_per_volunteer FROM volunteer_activities WHERE activity_id = ?', (activity_id,))
                    act = cursor.fetchone()
                    hours = actual_hours if actual_hours else (act[0] if act else 2)
                    cursor.execute('''
                        UPDATE activity_registrations SET
                            check_out_time = ?, actual_hours = ?, status = 'completed',
                            performance = ?, feedback = ?, rating = ?
                        WHERE activity_id = ? AND volunteer_id = ?
                    ''', (now, hours, kwargs.get('performance'),
                          kwargs.get('feedback'), kwargs.get('rating'),
                          activity_id, volunteer_id))
                    cursor.execute('SELECT total_hours, total_activities FROM volunteer_profiles WHERE volunteer_id = ?', (volunteer_id,))
                    vol = cursor.fetchone()
                    if vol:
                        new_hours = vol[0] + hours
                        new_count = vol[1] + 1
                        cursor.execute('UPDATE volunteer_profiles SET total_activities = ?, last_active = ?, updated_at = ? WHERE volunteer_id = ?',
                                     (new_count, now, now, volunteer_id))
                        self._update_volunteer_level(cursor, volunteer_id, new_hours)
                    conn.commit()
                    logger.info(f'签退: {volunteer_id}, 时长: {hours}h')
                    return {'success': True, 'actual_hours': hours, 'check_out_time': now}
        except Exception as e:
            logger.error(f'签退失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_activities(self, activity_type: str = None, status: str = 'published',
                         education_type: str = None, page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM volunteer_activities WHERE 1=1'
                params = []
                if activity_type:
                    query += ' AND activity_type = ?'
                    params.append(activity_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                activities = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'activities': activities, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 社区合作 ==========

    def create_partnership(self, community_name: str, partnership_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            partnership_id = f"cps_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO community_partnerships (
                            partnership_id, community_name, partnership_type,
                            contact_person, contact_phone, address, description,
                            start_date, is_active, total_activities, total_volunteers,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0, ?, ?)
                    ''', (partnership_id, community_name, partnership_type,
                          kwargs.get('contact_person'), kwargs.get('contact_phone'),
                          kwargs.get('address'), kwargs.get('description'),
                          kwargs.get('start_date', now[:10]), now, now))
                    conn.commit()
                    return {'success': True, 'partnership_id': partnership_id}
        except Exception as e:
            logger.error(f'创建社区合作失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_partnerships(self, is_active: bool = True,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM community_partnerships WHERE 1=1'
                params = []
                if is_active is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if is_active else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                partnerships = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'partnerships': partnerships, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社区合作列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 社会实践 ==========

    def create_practice(self, practice_name: str, practice_type: str,
                        start_date: str, **kwargs) -> Dict[str, Any]:
        try:
            practice_id = f"prc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PRACTICE_TYPES.get(practice_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO social_practices (
                            practice_id, practice_name, practice_type,
                            education_type, description, location, start_date,
                            end_date, duration_days, leader_id, leader_name,
                            participant_count, report_required, report_url,
                            report_status, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, NULL, 'not_submitted', 'planned', ?, ?)
                    ''', (practice_id, practice_name, practice_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('location'), start_date,
                          kwargs.get('end_date'),
                          kwargs.get('duration_days', config.get('duration_days', 7)),
                          kwargs.get('leader_id'), kwargs.get('leader_name'),
                          1 if config.get('report_required', True) else 0,
                          now, now))
                    conn.commit()
                    logger.info(f'创建社会实践: {practice_name} ({practice_id})')
                    return {'success': True, 'practice_id': practice_id}
        except Exception as e:
            logger.error(f'创建社会实践失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_practice(self, practice_id: str, student_id: int,
                       student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO practice_participants (practice_id, student_id, student_name, role, joined_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (practice_id, student_id, student_name,
                          kwargs.get('role', 'participant'), now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE social_practices SET participant_count = participant_count + 1, updated_at = ? WHERE practice_id = ?', (now, practice_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该实践'}
        except Exception as e:
            logger.error(f'加入实践失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_practice_report(self, practice_id: str, report_url: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE social_practices SET
                            report_url = ?, report_status = 'submitted',
                            updated_at = ?
                        WHERE practice_id = ? AND report_status = 'not_submitted'
                    ''', (report_url, now, practice_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '实践报告状态不允许提交'}
        except Exception as e:
            logger.error(f'提交实践报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 志愿团队 ==========

    def create_team(self, team_name: str, leader_id: int,
                     leader_name: str, **kwargs) -> Dict[str, Any]:
        try:
            team_id = f"vtm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO volunteer_teams (
                            team_id, team_name, description, leader_id,
                            leader_name, member_count, education_type,
                            is_active, founded_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 1, ?, 1, ?, ?, ?)
                    ''', (team_id, team_name, kwargs.get('description'),
                          leader_id, leader_name,
                          kwargs.get('education_type'),
                          kwargs.get('founded_date', now[:10]),
                          now, now))
                    conn.commit()
                    logger.info(f'创建志愿团队: {team_name} ({team_id})')
                    return {'success': True, 'team_id': team_id}
        except Exception as e:
            logger.error(f'创建志愿团队失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_team(self, team_id: str, volunteer_id: str,
                   volunteer_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO team_members (team_id, volunteer_id, volunteer_name, role, joined_at) VALUES (?, ?, ?, \'member\', ?)',
                                 (team_id, volunteer_id, volunteer_name, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE volunteer_teams SET member_count = member_count + 1, updated_at = ? WHERE team_id = ?', (now, team_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该团队'}
        except Exception as e:
            logger.error(f'加入团队失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书管理 ==========

    def issue_certificate(self, volunteer_id: str, certificate_type: str,
                           title: str, hours: float, **kwargs) -> Dict[str, Any]:
        try:
            certificate_id = f"vsc_{uuid.uuid4().hex[:12]}"
            verification_code = uuid.uuid4().hex[:8].upper()
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT real_name FROM volunteer_profiles WHERE volunteer_id = ?', (volunteer_id,))
                    vol = cursor.fetchone()
                    volunteer_name = vol[0] if vol else kwargs.get('volunteer_name', '')
                    cursor.execute('''
                        INSERT INTO service_certificates (
                            certificate_id, volunteer_id, volunteer_name,
                            certificate_type, title, hours, issued_date,
                            issued_by, verification_code, file_url, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (certificate_id, volunteer_id, volunteer_name,
                          certificate_type, title, hours, now[:10],
                          kwargs.get('issued_by', ''), verification_code,
                          kwargs.get('file_url'), now))
                    conn.commit()
                    logger.info(f'颁发证书: {title} ({certificate_id})')
                    return {'success': True, 'certificate_id': certificate_id,
                            'verification_code': verification_code}
        except Exception as e:
            logger.error(f'颁发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_volunteer_statistics(self, education_type: str = None,
                                  year: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*), SUM(total_hours), AVG(total_hours) FROM volunteer_profiles WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                row = cursor.fetchone()
                cursor.execute('SELECT level, COUNT(*) FROM volunteer_profiles GROUP BY level ORDER BY level')
                by_level = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT activity_type, COUNT(*) FROM volunteer_activities GROUP BY activity_type')
                by_type = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'success': True,
                    'stats': {
                        'total_volunteers': row[0] or 0,
                        'total_hours': round(row[1], 1) if row[1] else 0,
                        'average_hours': round(row[2], 1) if row[2] else 0,
                        'by_level': by_level,
                        'activities_by_type': by_type
                    }
                }
        except Exception as e:
            logger.error(f'获取志愿统计失败: {e}')
            return {'success': False, 'error': str(e)}
