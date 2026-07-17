#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 家校社协同育人服务 (v15.10.0)
====================================
提供家校沟通、家庭教育指导、家长学校、社区协同、家访管理、协同活动、
家庭教育档案等综合管理服务。同时支持成人教育和K12教育的差异化需求。

核心能力：
1. 家校沟通 - 家长教师沟通、消息、家长会
2. 家庭教育指导 - 家庭教育课程、讲座、咨询服务
3. 家长学校 - 家长培训、家长委员会、家长志愿者
4. 社区协同 - 社区教育资源、社区活动、共建项目
5. 家访管理 - 家访计划、家访记录、家访跟进
6. 协同活动 - 家校社联合活动、开放日、亲子活动
7. 家庭教育档案 - 家庭情况、教育需求、沟通历史
8. K12家校协同与成人教育家庭支持差异化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'home_school_community_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HomeSchoolCommunity')


# ========== 家校社协同配置 ==========

# 沟通渠道
COMMUNICATION_CHANNELS = {
    'face_to_face': {'name': '面谈', 'is_realtime': True},
    'phone': {'name': '电话', 'is_realtime': True},
    'online': {'name': '在线', 'is_realtime': True},
    'message': {'name': '消息', 'is_realtime': False},
    'home_visit': {'name': '家访', 'is_realtime': True},
    'parent_meeting': {'name': '家长会', 'is_realtime': True}
}

# 沟通主题
COMMUNICATION_TOPICS = {
    'academic': {'name': '学业'},
    'behavior': {'name': '行为'},
    'psychological': {'name': '心理'},
    'attendance': {'name': '考勤'},
    'family': {'name': '家庭'},
    'career': {'name': '升学就业'},
    'health': {'name': '健康'},
    'other': {'name': '其他'}
}

# 家长会类型
PARENT_MEETING_TYPES = {
    'grade': {'name': '年级会', 'typical_duration': 120},
    'class': {'name': '班级会', 'typical_duration': 90},
    'individual': {'name': '个别会', 'typical_duration': 30},
    'online': {'name': '线上会', 'typical_duration': 60},
    'theme': {'name': '主题会', 'typical_duration': 90}
}

# 家庭教育指导类型
FAMILY_EDUCATION_TYPES = {
    'lecture': {'name': '讲座', 'target_audience': '全体家长'},
    'course': {'name': '课程', 'target_audience': '报名家长'},
    'workshop': {'name': '工作坊', 'target_audience': '小组家长'},
    'consultation': {'name': '咨询', 'target_audience': '个别家长'},
    'support_group': {'name': '支持小组', 'target_audience': '特定家长'}
}

# 家长角色
PARENT_ROLES = {
    'committee_member': {'name': '家委会成员', 'responsibilities': '参与学校决策与管理'},
    'volunteer': {'name': '志愿者', 'responsibilities': '协助学校活动组织'},
    'tutor': {'name': '辅导员', 'responsibilities': '为学生提供学习辅导'},
    'activity_organizer': {'name': '活动组织者', 'responsibilities': '组织家校社活动'},
    'advocate': {'name': '代表', 'responsibilities': '代表家长群体发言'}
}

# 社区资源类型
COMMUNITY_RESOURCE_TYPES = {
    'venue': {'name': '场地'},
    'equipment': {'name': '设备'},
    'expert': {'name': '专家'},
    'volunteer': {'name': '志愿者'},
    'funding': {'name': '资金'},
    'program': {'name': '项目'},
    'service': {'name': '服务'}
}

# 家访类型
HOME_VISIT_TYPES = {
    'routine': {'name': '常规', 'priority': 'normal'},
    'concern': {'name': '关注', 'priority': 'high'},
    'problem': {'name': '问题', 'priority': 'urgent'},
    'new_student': {'name': '新生', 'priority': 'normal'},
    'transfer': {'name': '转学', 'priority': 'normal'},
    'special_needs': {'name': '特殊需要', 'priority': 'high'}
}

# 协同活动类型
ACTIVITY_TYPES = {
    'open_day': {'name': '开放日', 'requires_registration': True},
    'parent_child': {'name': '亲子活动', 'requires_registration': True},
    'family_lecture': {'name': '家庭讲座', 'requires_registration': True},
    'community_service': {'name': '社区服务', 'requires_registration': True},
    'cultural_exchange': {'name': '文化交流', 'requires_registration': True},
    'sports_day': {'name': '运动会', 'requires_registration': True},
    'festival': {'name': '节日活动', 'requires_registration': False}
}


class HomeSchoolCommunityService:
    """家校社协同育人服务"""

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
                # 1. 家长档案表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_profiles (
                        parent_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        name TEXT NOT NULL,
                        gender TEXT,
                        phone TEXT,
                        email TEXT,
                        relationship TEXT,
                        occupation TEXT,
                        education_level TEXT,
                        student_ids TEXT,
                        family_type TEXT,
                        address TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 2. 家校沟通记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teacher_parent_communications (
                        comm_id TEXT PRIMARY KEY,
                        parent_id TEXT,
                        parent_name TEXT,
                        teacher_id TEXT,
                        teacher_name TEXT,
                        student_id TEXT,
                        student_name TEXT,
                        channel TEXT,
                        topic TEXT,
                        title TEXT,
                        content TEXT,
                        direction TEXT,
                        status TEXT,
                        response TEXT,
                        response_time TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 3. 家长会表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_meetings (
                        meeting_id TEXT PRIMARY KEY,
                        meeting_name TEXT NOT NULL,
                        meeting_type TEXT,
                        organizer_id TEXT,
                        organizer_name TEXT,
                        target_grade TEXT,
                        target_class TEXT,
                        meeting_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        location TEXT,
                        agenda TEXT,
                        max_attendees INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        actual_attendees INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        summary TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 4. 家长会报名表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meeting_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL,
                        parent_id TEXT,
                        parent_name TEXT,
                        student_id TEXT,
                        student_name TEXT,
                        register_time TEXT,
                        attend_status TEXT DEFAULT 'registered',
                        created_at TEXT
                    )
                ''')
                # 5. 家庭教育指导项目表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS family_education_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        program_type TEXT,
                        target_audience TEXT,
                        instructor TEXT,
                        description TEXT,
                        content TEXT,
                        schedule TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 50,
                        enrolled_count INTEGER DEFAULT 0,
                        is_free INTEGER DEFAULT 1,
                        fee REAL DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 6. 项目报名表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS program_enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        program_id TEXT NOT NULL,
                        parent_id TEXT,
                        parent_name TEXT,
                        student_id TEXT,
                        enroll_time TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        completion TEXT DEFAULT 'ongoing',
                        feedback TEXT,
                        created_at TEXT
                    )
                ''')
                # 7. 家长委员会表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_committees (
                        committee_id TEXT PRIMARY KEY,
                        committee_name TEXT NOT NULL,
                        committee_type TEXT,
                        level TEXT,
                        parent_id TEXT,
                        parent_name TEXT,
                        role TEXT,
                        term_start TEXT,
                        term_end TEXT,
                        responsibilities TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 8. 家长志愿者表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS parent_volunteers (
                        volunteer_id TEXT PRIMARY KEY,
                        parent_id TEXT,
                        parent_name TEXT,
                        student_id TEXT,
                        specialties TEXT,
                        available_times TEXT,
                        total_hours REAL DEFAULT 0,
                        activity_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 9. 社区教育资源表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_resources (
                        resource_id TEXT PRIMARY KEY,
                        resource_name TEXT NOT NULL,
                        resource_type TEXT,
                        provider_name TEXT,
                        provider_contact TEXT,
                        description TEXT,
                        availability TEXT,
                        location TEXT,
                        cost REAL DEFAULT 0,
                        is_free INTEGER DEFAULT 1,
                        rating REAL DEFAULT 0,
                        usage_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 10. 社区活动表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_activities (
                        activity_id TEXT PRIMARY KEY,
                        activity_name TEXT NOT NULL,
                        activity_type TEXT,
                        organizer TEXT,
                        description TEXT,
                        target_audience TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        outcome TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 11. 社区共建项目表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_cooperations (
                        coop_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        partner_organization TEXT,
                        partner_type TEXT,
                        description TEXT,
                        objectives TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'ongoing',
                        contribution TEXT,
                        outcome TEXT,
                        contact_person TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 12. 家访记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS home_visits (
                        visit_id TEXT PRIMARY KEY,
                        teacher_id TEXT,
                        teacher_name TEXT,
                        student_id TEXT,
                        student_name TEXT,
                        parent_id TEXT,
                        parent_name TEXT,
                        visit_type TEXT,
                        planned_date TEXT,
                        actual_date TEXT,
                        duration INTEGER,
                        purpose TEXT,
                        family_situation TEXT,
                        discussion_content TEXT,
                        findings TEXT,
                        recommendations TEXT,
                        follow_up_plan TEXT,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 13. 协同活动表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaborative_activities (
                        activity_id TEXT PRIMARY KEY,
                        activity_name TEXT NOT NULL,
                        activity_type TEXT,
                        organizer TEXT,
                        description TEXT,
                        target_audience TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        parent_participants INTEGER DEFAULT 0,
                        community_participants INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        outcome TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 14. 活动报名表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id TEXT NOT NULL,
                        activity_type TEXT,
                        participant_id TEXT,
                        participant_name TEXT,
                        participant_role TEXT,
                        register_time TEXT,
                        attend_status TEXT DEFAULT 'registered',
                        created_at TEXT
                    )
                ''')
                # 15. 家庭教育档案表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS family_education_profiles (
                        profile_id TEXT PRIMARY KEY,
                        student_id TEXT,
                        student_name TEXT,
                        parent_id TEXT,
                        parent_name TEXT,
                        family_structure TEXT,
                        education_environment TEXT,
                        parent_expectations TEXT,
                        communication_frequency TEXT,
                        last_communication TEXT,
                        needs TEXT,
                        risk_factors TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('家校社协同育人服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 家长档案 ==========

    def register_parent(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            parent_id = f"hc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            student_ids = kwargs.get('student_ids', [])
            if isinstance(student_ids, (list, tuple)):
                student_ids = json.dumps(student_ids, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO parent_profiles (
                            parent_id, user_id, name, gender, phone, email,
                            relationship, occupation, education_level,
                            student_ids, family_type, address, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (parent_id, kwargs.get('user_id'), name,
                          kwargs.get('gender'), kwargs.get('phone'),
                          kwargs.get('email'), kwargs.get('relationship'),
                          kwargs.get('occupation'), kwargs.get('education_level'),
                          student_ids, kwargs.get('family_type', 'nuclear'),
                          kwargs.get('address'), now, now))
                    conn.commit()
                    logger.info(f'注册家长档案: {name} ({parent_id})')
                    return {'success': True, 'parent_id': parent_id}
        except Exception as e:
            logger.error(f'注册家长档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_parent(self, parent_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM parent_profiles WHERE parent_id = ?', (parent_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '家长档案不存在'}
                parent = dict(row)
                if parent.get('student_ids'):
                    try:
                        parent['student_ids'] = json.loads(parent['student_ids'])
                    except Exception:
                        pass
                return {'success': True, 'parent': parent}
        except Exception as e:
            logger.error(f'获取家长档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_parent(self, parent_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            allowed = ['user_id', 'name', 'gender', 'phone', 'email', 'relationship',
                       'occupation', 'education_level', 'student_ids', 'family_type', 'address']
            fields = []
            values = []
            for k, v in kwargs.items():
                if k in allowed:
                    if k == 'student_ids' and isinstance(v, (list, tuple)):
                        v = json.dumps(v, ensure_ascii=False)
                    fields.append(f'{k} = ?')
                    values.append(v)
            if not fields:
                return {'success': False, 'error': '无可更新字段'}
            fields.append('updated_at = ?')
            values.append(now)
            values.append(parent_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE parent_profiles SET {", ".join(fields)} WHERE parent_id = ?', values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '家长档案不存在'}
        except Exception as e:
            logger.error(f'更新家长档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_parents(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM parent_profiles WHERE 1=1'
                params = []
                for key in ['family_type', 'gender', 'relationship', 'education_level']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                parents = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'parents': parents, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取家长列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家校沟通 ==========

    def create_communication(self, parent_id: str, teacher_id: str,
                             channel: str, topic: str, **kwargs) -> Dict[str, Any]:
        try:
            comm_id = f"hcm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teacher_parent_communications (
                            comm_id, parent_id, parent_name, teacher_id, teacher_name,
                            student_id, student_name, channel, topic, title, content,
                            direction, status, response, response_time,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                    ''', (comm_id, parent_id, kwargs.get('parent_name'),
                          teacher_id, kwargs.get('teacher_name'),
                          kwargs.get('student_id'), kwargs.get('student_name'),
                          channel, topic, kwargs.get('title'),
                          kwargs.get('content'), kwargs.get('direction', 'inbound'),
                          kwargs.get('status', 'pending'), now, now))
                    conn.commit()
                    logger.info(f'创建家校沟通记录: {comm_id}')
                    return {'success': True, 'comm_id': comm_id}
        except Exception as e:
            logger.error(f'创建家校沟通记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def respond_communication(self, comm_id: str, response: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE teacher_parent_communications
                        SET response = ?, response_time = ?, status = 'responded', updated_at = ?
                        WHERE comm_id = ?
                    ''', (response, now, now, comm_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'response_time': now}
                    return {'success': False, 'error': '沟通记录不存在'}
        except Exception as e:
            logger.error(f'回复沟通记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_communications(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM teacher_parent_communications WHERE 1=1'
                params = []
                for key in ['teacher_id', 'parent_id', 'topic', 'channel', 'status', 'direction']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'communications': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取沟通列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家长会 ==========

    def create_parent_meeting(self, meeting_name: str, meeting_type: str, **kwargs) -> Dict[str, Any]:
        try:
            meeting_id = f"hpm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PARENT_MEETING_TYPES.get(meeting_type, {})
            agenda = kwargs.get('agenda', [])
            if isinstance(agenda, (list, tuple)):
                agenda = json.dumps(agenda, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO parent_meetings (
                            meeting_id, meeting_name, meeting_type, organizer_id,
                            organizer_name, target_grade, target_class, meeting_date,
                            start_time, end_time, location, agenda, max_attendees,
                            registered_count, actual_attendees, status, summary,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'scheduled', NULL, ?, ?)
                    ''', (meeting_id, meeting_name, meeting_type,
                          kwargs.get('organizer_id'), kwargs.get('organizer_name'),
                          kwargs.get('target_grade'), kwargs.get('target_class'),
                          kwargs.get('meeting_date'),
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('location'), agenda,
                          kwargs.get('max_attendees', 100), now, now))
                    conn.commit()
                    logger.info(f'创建家长会: {meeting_name} ({meeting_id}) 类型={config.get("name", meeting_type)}')
                    return {'success': True, 'meeting_id': meeting_id}
        except Exception as e:
            logger.error(f'创建家长会失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_meeting(self, meeting_id: str, parent_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_attendees, registered_count, status FROM parent_meetings WHERE meeting_id = ?', (meeting_id,))
                    meeting = cursor.fetchone()
                    if not meeting:
                        return {'success': False, 'error': '家长会不存在'}
                    if meeting[2] not in ('scheduled', 'open'):
                        return {'success': False, 'error': '家长会状态不允许报名'}
                    if meeting[0] and meeting[1] >= meeting[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT INTO meeting_registrations (meeting_id, parent_id, parent_name, student_id, student_name, register_time, attend_status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'registered', ?)
                    ''', (meeting_id, parent_id, kwargs.get('parent_name'),
                          kwargs.get('student_id'), kwargs.get('student_name'), now, now))
                    cursor.execute('UPDATE parent_meetings SET registered_count = registered_count + 1, updated_at = ? WHERE meeting_id = ?', (now, meeting_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'家长会报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_meeting_attendance(self, meeting_id: str, actual_attendees: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE parent_meetings
                        SET actual_attendees = ?, summary = ?, status = 'completed', updated_at = ?
                        WHERE meeting_id = ?
                    ''', (actual_attendees, kwargs.get('summary'), now, meeting_id))
                    if cursor.rowcount > 0:
                        if kwargs.get('attendees'):
                            for parent_id in kwargs['attendees']:
                                cursor.execute('UPDATE meeting_registrations SET attend_status = ? WHERE meeting_id = ? AND parent_id = ?',
                                             ('attended', meeting_id, parent_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '家长会不存在'}
        except Exception as e:
            logger.error(f'记录家长会参会情况失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_parent_meetings(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM parent_meetings WHERE 1=1'
                params = []
                for key in ['meeting_type', 'status', 'target_grade', 'target_class', 'organizer_id']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY meeting_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                meetings = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'meetings': meetings, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取家长会列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家庭教育指导 ==========

    def create_family_education_program(self, program_name: str, program_type: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"fep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = FAMILY_EDUCATION_TYPES.get(program_type, {})
            content = kwargs.get('content', [])
            if isinstance(content, (list, tuple)):
                content = json.dumps(content, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO family_education_programs (
                            program_id, program_name, program_type, target_audience,
                            instructor, description, content, schedule, location,
                            max_participants, enrolled_count, is_free, fee, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'open', ?, ?)
                    ''', (program_id, program_name, program_type,
                          kwargs.get('target_audience', config.get('target_audience')),
                          kwargs.get('instructor'), kwargs.get('description'),
                          content, kwargs.get('schedule'), kwargs.get('location'),
                          kwargs.get('max_participants', 50),
                          1 if kwargs.get('is_free', True) else 0,
                          kwargs.get('fee', 0), now, now))
                    conn.commit()
                    logger.info(f'创建家庭教育项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建家庭教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_program(self, program_id: str, parent_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM family_education_programs WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'open':
                        return {'success': False, 'error': '项目状态不允许报名'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT INTO program_enrollments (program_id, parent_id, parent_name, student_id, enroll_time, attendance_count, completion, feedback, created_at)
                        VALUES (?, ?, ?, ?, ?, 0, 'ongoing', NULL, ?)
                    ''', (program_id, parent_id, kwargs.get('parent_name'),
                          kwargs.get('student_id'), now, now))
                    cursor.execute('UPDATE family_education_programs SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'家庭教育项目报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_programs(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM family_education_programs WHERE 1=1'
                params = []
                for key in ['program_type', 'status', 'target_audience', 'instructor']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取家庭教育项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家长委员会与志愿者 ==========

    def create_committee(self, committee_name: str, committee_type: str,
                         parent_id: str, **kwargs) -> Dict[str, Any]:
        try:
            committee_id = f"hc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO parent_committees (
                            committee_id, committee_name, committee_type, level,
                            parent_id, parent_name, role, term_start, term_end,
                            responsibilities, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (committee_id, committee_name, committee_type,
                          kwargs.get('level'), parent_id, kwargs.get('parent_name'),
                          kwargs.get('role', 'member'),
                          kwargs.get('term_start'), kwargs.get('term_end'),
                          kwargs.get('responsibilities'), now, now))
                    conn.commit()
                    logger.info(f'创建家委会: {committee_name} ({committee_id})')
                    return {'success': True, 'committee_id': committee_id}
        except Exception as e:
            logger.error(f'创建家委会失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_volunteer(self, parent_id: str, **kwargs) -> Dict[str, Any]:
        try:
            volunteer_id = f"hv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            specialties = kwargs.get('specialties', [])
            if isinstance(specialties, (list, tuple)):
                specialties = json.dumps(specialties, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT volunteer_id FROM parent_volunteers WHERE parent_id = ? AND status = "active"', (parent_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该家长已是志愿者'}
                    cursor.execute('''
                        INSERT INTO parent_volunteers (
                            volunteer_id, parent_id, parent_name, student_id,
                            specialties, available_times, total_hours, activity_count,
                            rating, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 'active', ?, ?)
                    ''', (volunteer_id, parent_id, kwargs.get('parent_name'),
                          kwargs.get('student_id'), specialties,
                          kwargs.get('available_times'), now, now))
                    conn.commit()
                    logger.info(f'注册家长志愿者: {parent_id} ({volunteer_id})')
                    return {'success': True, 'volunteer_id': volunteer_id}
        except Exception as e:
            logger.error(f'注册家长志愿者失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_volunteers(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM parent_volunteers WHERE 1=1'
                params = []
                for key in ['status', 'parent_id', 'student_id']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY total_hours DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                volunteers = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'volunteers': volunteers, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取志愿者列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 社区协同 ==========

    def add_community_resource(self, resource_name: str, resource_type: str, **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"cr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO community_resources (
                            resource_id, resource_name, resource_type, provider_name,
                            provider_contact, description, availability, location,
                            cost, is_free, rating, usage_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
                    ''', (resource_id, resource_name, resource_type,
                          kwargs.get('provider_name'), kwargs.get('provider_contact'),
                          kwargs.get('description'), kwargs.get('availability'),
                          kwargs.get('location'), kwargs.get('cost', 0),
                          1 if kwargs.get('is_free', True) else 0, now, now))
                    conn.commit()
                    logger.info(f'添加社区资源: {resource_name} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'添加社区资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_community_activity(self, activity_name: str, activity_type: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"ca_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO community_activities (
                            activity_id, activity_name, activity_type, organizer,
                            description, target_audience, start_date, end_date,
                            location, max_participants, registered_count, status,
                            outcome, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'scheduled', NULL, ?, ?)
                    ''', (activity_id, activity_name, activity_type,
                          kwargs.get('organizer'), kwargs.get('description'),
                          kwargs.get('target_audience'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('location'), kwargs.get('max_participants', 100),
                          now, now))
                    conn.commit()
                    logger.info(f'创建社区活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建社区活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_cooperation(self, project_name: str, partner_organization: str, **kwargs) -> Dict[str, Any]:
        try:
            coop_id = f"cc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            contribution = kwargs.get('contribution', {})
            if isinstance(contribution, (dict, list)):
                contribution = json.dumps(contribution, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO community_cooperations (
                            coop_id, project_name, partner_organization, partner_type,
                            description, objectives, start_date, end_date, status,
                            contribution, outcome, contact_person, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ongoing', ?, NULL, ?, ?, ?)
                    ''', (coop_id, project_name, partner_organization,
                          kwargs.get('partner_type'), kwargs.get('description'),
                          kwargs.get('objectives'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          contribution, kwargs.get('contact_person'), now, now))
                    conn.commit()
                    logger.info(f'创建共建项目: {project_name} ({coop_id})')
                    return {'success': True, 'coop_id': coop_id}
        except Exception as e:
            logger.error(f'创建共建项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_community_resources(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM community_resources WHERE 1=1'
                params = []
                for key in ['resource_type', 'is_free', 'provider_name']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY rating DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社区资源列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_community_activities(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM community_activities WHERE 1=1'
                params = []
                for key in ['activity_type', 'status', 'organizer', 'target_audience']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                activities = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'activities': activities, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社区活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家访管理 ==========

    def plan_home_visit(self, teacher_id: str, student_id: str,
                        visit_type: str, **kwargs) -> Dict[str, Any]:
        try:
            visit_id = f"hvt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = HOME_VISIT_TYPES.get(visit_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO home_visits (
                            visit_id, teacher_id, teacher_name, student_id, student_name,
                            parent_id, parent_name, visit_type, planned_date, actual_date,
                            duration, purpose, family_situation, discussion_content,
                            findings, recommendations, follow_up_plan, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL, NULL, NULL, NULL, NULL, 'planned', ?, ?)
                    ''', (visit_id, teacher_id, kwargs.get('teacher_name'),
                          student_id, kwargs.get('student_name'),
                          kwargs.get('parent_id'), kwargs.get('parent_name'),
                          visit_type, kwargs.get('planned_date'),
                          kwargs.get('purpose'), now, now))
                    conn.commit()
                    logger.info(f'计划家访: {visit_id} 类型={config.get("name", visit_type)}')
                    return {'success': True, 'visit_id': visit_id}
        except Exception as e:
            logger.error(f'计划家访失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_home_visit(self, visit_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            allowed = ['actual_date', 'duration', 'purpose', 'family_situation',
                       'discussion_content', 'findings', 'recommendations',
                       'follow_up_plan', 'status']
            fields = []
            values = []
            for k, v in kwargs.items():
                if k in allowed:
                    fields.append(f'{k} = ?')
                    values.append(v)
            if not fields:
                return {'success': False, 'error': '无可更新字段'}
            if 'status' not in kwargs:
                fields.append('status = ?')
                values.append('completed')
            fields.append('updated_at = ?')
            values.append(now)
            values.append(visit_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE home_visits SET {", ".join(fields)} WHERE visit_id = ?', values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '家访记录不存在'}
        except Exception as e:
            logger.error(f'记录家访失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_home_visits(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM home_visits WHERE 1=1'
                params = []
                for key in ['teacher_id', 'student_id', 'parent_id', 'visit_type', 'status']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY planned_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                visits = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'visits': visits, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取家访列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 协同活动 ==========

    def create_collaborative_activity(self, activity_name: str, activity_type: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"cba_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ACTIVITY_TYPES.get(activity_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO collaborative_activities (
                            activity_id, activity_name, activity_type, organizer,
                            description, target_audience, start_date, end_date,
                            location, max_participants, registered_count,
                            parent_participants, community_participants, status,
                            outcome, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 'scheduled', NULL, ?, ?)
                    ''', (activity_id, activity_name, activity_type,
                          kwargs.get('organizer'), kwargs.get('description'),
                          kwargs.get('target_audience'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('location'), kwargs.get('max_participants', 100),
                          now, now))
                    conn.commit()
                    logger.info(f'创建协同活动: {activity_name} ({activity_id}) 需报名={config.get("requires_registration", True)}')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建协同活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_activity(self, activity_id: str, participant_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM collaborative_activities WHERE activity_id = ?', (activity_id,))
                    activity = cursor.fetchone()
                    if not activity:
                        return {'success': False, 'error': '活动不存在'}
                    if activity[2] != 'scheduled':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if activity[0] and activity[1] >= activity[0]:
                        return {'success': False, 'error': '名额已满'}
                    participant_role = kwargs.get('participant_role', 'parent')
                    cursor.execute('''
                        INSERT INTO activity_registrations (activity_id, activity_type, participant_id, participant_name, participant_role, register_time, attend_status, created_at)
                        VALUES (?, 'collaborative', ?, ?, ?, ?, 'registered', ?)
                    ''', (activity_id, participant_id, kwargs.get('participant_name'),
                          participant_role, now, now))
                    cursor.execute('UPDATE collaborative_activities SET registered_count = registered_count + 1, updated_at = ? WHERE activity_id = ?', (now, activity_id))
                    if participant_role == 'parent':
                        cursor.execute('UPDATE collaborative_activities SET parent_participants = parent_participants + 1 WHERE activity_id = ?', (activity_id,))
                    elif participant_role == 'community':
                        cursor.execute('UPDATE collaborative_activities SET community_participants = community_participants + 1 WHERE activity_id = ?', (activity_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'协同活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_collaborative_activities(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM collaborative_activities WHERE 1=1'
                params = []
                for key in ['activity_type', 'status', 'organizer', 'target_audience']:
                    if filters.get(key):
                        query += f' AND {key} = ?'
                        params.append(filters[key])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                activities = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'activities': activities, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取协同活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家庭教育档案 ==========

    def create_family_profile(self, student_id: str, parent_id: str, **kwargs) -> Dict[str, Any]:
        try:
            profile_id = f"fpr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            needs = kwargs.get('needs', [])
            if isinstance(needs, (list, tuple)):
                needs = json.dumps(needs, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT profile_id FROM family_education_profiles WHERE student_id = ?', (student_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该学生已有家庭教育档案'}
                    cursor.execute('''
                        INSERT INTO family_education_profiles (
                            profile_id, student_id, student_name, parent_id, parent_name,
                            family_structure, education_environment, parent_expectations,
                            communication_frequency, last_communication, needs,
                            risk_factors, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (profile_id, student_id, kwargs.get('student_name'),
                          parent_id, kwargs.get('parent_name'),
                          kwargs.get('family_structure'),
                          kwargs.get('education_environment'),
                          kwargs.get('parent_expectations'),
                          kwargs.get('communication_frequency', 'normal'),
                          kwargs.get('last_communication'), needs,
                          kwargs.get('risk_factors'), now, now))
                    conn.commit()
                    logger.info(f'创建家庭教育档案: {student_id} ({profile_id})')
                    return {'success': True, 'profile_id': profile_id}
        except Exception as e:
            logger.error(f'创建家庭教育档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_family_profile(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            allowed = ['student_name', 'parent_id', 'parent_name', 'family_structure',
                       'education_environment', 'parent_expectations',
                       'communication_frequency', 'last_communication', 'needs',
                       'risk_factors']
            fields = []
            values = []
            for k, v in kwargs.items():
                if k in allowed:
                    if k == 'needs' and isinstance(v, (list, tuple)):
                        v = json.dumps(v, ensure_ascii=False)
                    fields.append(f'{k} = ?')
                    values.append(v)
            if not fields:
                return {'success': False, 'error': '无可更新字段'}
            fields.append('updated_at = ?')
            values.append(now)
            values.append(profile_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE family_education_profiles SET {", ".join(fields)} WHERE profile_id = ?', values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '家庭教育档案不存在'}
        except Exception as e:
            logger.error(f'更新家庭教育档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_family_profile(self, student_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM family_education_profiles WHERE student_id = ?', (student_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '家庭教育档案不存在'}
                profile = dict(row)
                if profile.get('needs'):
                    try:
                        profile['needs'] = json.loads(profile['needs'])
                    except Exception:
                        pass
                return {'success': True, 'profile': profile}
        except Exception as e:
            logger.error(f'获取家庭教育档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats: Dict[str, Any] = {'education_type': education_type}

                # 沟通渠道分布
                cursor.execute('SELECT channel, COUNT(*) as cnt FROM teacher_parent_communications GROUP BY channel')
                channel_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['communication_channels'] = channel_dist

                # 家长会参会率
                cursor.execute('SELECT COUNT(*), SUM(actual_attendees), SUM(registered_count) FROM parent_meetings')
                meeting_row = cursor.fetchone()
                meeting_total = meeting_row[0] or 0
                meeting_actual = meeting_row[1] or 0
                meeting_registered = meeting_row[2] or 0
                attendance_rate = round(meeting_actual / meeting_registered, 4) if meeting_registered > 0 else 0
                stats['parent_meetings'] = {
                    'total': meeting_total,
                    'actual_attendees': meeting_actual,
                    'registered_count': meeting_registered,
                    'attendance_rate': attendance_rate
                }

                # 家庭教育项目参与
                cursor.execute('SELECT COUNT(*), SUM(enrolled_count) FROM family_education_programs')
                program_row = cursor.fetchone()
                stats['family_education_programs'] = {
                    'total': program_row[0] or 0,
                    'total_enrolled': program_row[1] or 0
                }

                # 志愿者时长
                cursor.execute('SELECT COUNT(*), SUM(total_hours), AVG(rating) FROM parent_volunteers WHERE status = "active"')
                volunteer_row = cursor.fetchone()
                stats['parent_volunteers'] = {
                    'total': volunteer_row[0] or 0,
                    'total_hours': round(volunteer_row[1] or 0, 1),
                    'average_rating': round(volunteer_row[2] or 0, 2)
                }

                # 社区资源数量
                cursor.execute('SELECT resource_type, COUNT(*) FROM community_resources GROUP BY resource_type')
                resource_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['community_resources'] = {
                    'total': sum(resource_dist.values()),
                    'by_type': resource_dist
                }

                # 家访完成率
                cursor.execute('SELECT COUNT(*), SUM(CASE WHEN status = "completed" THEN 1 ELSE 0 END) FROM home_visits')
                visit_row = cursor.fetchone()
                visit_total = visit_row[0] or 0
                visit_completed = visit_row[1] or 0
                visit_rate = round(visit_completed / visit_total, 4) if visit_total > 0 else 0
                stats['home_visits'] = {
                    'total': visit_total,
                    'completed': visit_completed,
                    'completion_rate': visit_rate
                }

                # 协同活动参与度
                cursor.execute('SELECT COUNT(*), SUM(registered_count), SUM(parent_participants), SUM(community_participants) FROM collaborative_activities')
                activity_row = cursor.fetchone()
                stats['collaborative_activities'] = {
                    'total': activity_row[0] or 0,
                    'registered_count': activity_row[1] or 0,
                    'parent_participants': activity_row[2] or 0,
                    'community_participants': activity_row[3] or 0
                }

                # 家长档案总数
                cursor.execute('SELECT COUNT(*) FROM parent_profiles')
                stats['parent_count'] = cursor.fetchone()[0] or 0

                # 教育类型差异化说明
                if education_type == 'adult':
                    stats['note'] = '成人教育家庭支持：侧重家庭学习环境、家庭成员协同、家庭教育档案'
                elif education_type == 'k12':
                    stats['note'] = 'K12家校协同：侧重家校沟通、家长会、家访、家长委员会'
                else:
                    stats['note'] = '综合统计：涵盖成人教育与K12家校社协同全场景'

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = HomeSchoolCommunityService()
    print('家校社协同育人服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
