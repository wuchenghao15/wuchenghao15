#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学生社团管理服务 (v15.10.0)
=====================================
提供学生社团的创建审核、成员招新、活动组织、经费管理、评价考核等综合管理服务。
支持成人教育兴趣社团与K12学生社团的差异化需求。

核心能力：
1. 社团管理 - 社团创建、分类、审核、状态管理
2. 成员管理 - 招新、入退社、职位、出勤
3. 活动管理 - 社团活动、场地预约、活动记录
4. 经费管理 - 经费预算、收支记录、财务报告
5. 社团评价 - 社团评级、成员评价、活动评价
6. 成果展示 - 社团作品、比赛获奖、展示活动
7. 指导教师 - 指导教师分配、考核
8. K12学生社团与成人兴趣社团差异化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'student_club_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('StudentClub')


# ========== 社团配置 ==========

# 社团类别
CLUB_CATEGORIES = {
    'academic': {'name': '学术类', 'description': '学术研究、学科拓展类社团'},
    'art_art': {'name': '艺术类', 'description': '音乐、舞蹈、美术等艺术类社团'},
    'sports': {'name': '体育类', 'description': '体育竞技、健身运动类社团'},
    'technology': {'name': '科技类', 'description': '科技创新、编程机器人等社团'},
    'service': {'name': '服务类', 'description': '志愿服务、公益类社团'},
    'culture': {'name': '文化类', 'description': '传统文化、文化交流类社团'},
    'practice': {'name': '实践类', 'description': '社会实践、技能实践类社团'},
    'recreation': {'name': '休闲类', 'description': '兴趣爱好、休闲娱乐类社团'}
}

# 社团状态
CLUB_STATUS = {
    'pending': {'name': '待审核', 'color': '#999999'},
    'active': {'name': '活跃', 'color': '#52c41a'},
    'suspended': {'name': '暂停', 'color': '#faad14'},
    'dissolved': {'name': '解散', 'color': '#ff4d4f'},
    'inactive': {'name': '不活跃', 'color': '#bfbfbf'}
}

# 成员角色
MEMBER_ROLES = {
    'president': {'name': '社长', 'level': 1},
    'vice_president': {'name': '副社长', 'level': 2},
    'secretary': {'name': '秘书长', 'level': 3},
    'minister': {'name': '部长', 'level': 4},
    'member': {'name': '社员', 'level': 9},
    'instructor': {'name': '指导教师', 'level': 0}
}

# 成员状态
MEMBER_STATUS = {
    'active': {'name': '在职'},
    'transferred': {'name': '转出'},
    'resigned': {'name': '已退社'},
    'expelled': {'name': '开除'},
    'graduated': {'name': '毕业'}
}

# 活动类型
ACTIVITY_TYPES = {
    'regular': {'name': '常规活动', 'requires_approval': False},
    'special': {'name': '特别活动', 'requires_approval': True},
    'competition': {'name': '竞赛', 'requires_approval': True},
    'exhibition': {'name': '展示', 'requires_approval': True},
    'training': {'name': '培训', 'requires_approval': False},
    'exchange': {'name': '交流', 'requires_approval': True},
    'social': {'name': '社交', 'requires_approval': False},
    'community_service': {'name': '社区服务', 'requires_approval': False}
}

# 活动状态
ACTIVITY_STATUS = {
    'planning': {'name': '策划中'},
    'approved': {'name': '已批准'},
    'scheduled': {'name': '已安排'},
    'in_progress': {'name': '进行中'},
    'completed': {'name': '已完成'},
    'cancelled': {'name': '已取消'}
}

# 经费类型
FUND_TYPES = {
    'membership_fee': {'name': '会费', 'is_income': True},
    'school_funding': {'name': '学校拨款', 'is_income': True},
    'donation': {'name': '赞助', 'is_income': True},
    'competition_award': {'name': '竞赛奖金', 'is_income': True},
    'activity_fee': {'name': '活动收费', 'is_income': True},
    'other': {'name': '其他', 'is_income': False}
}

# 支出类别
EXPENSE_CATEGORIES = {
    'equipment': {'name': '设备'},
    'materials': {'name': '耗材'},
    'venue': {'name': '场地'},
    'activity_activity': {'name': '活动经费'},
    'competition': {'name': '竞赛'},
    'prize': {'name': '奖品'},
    'publicity': {'name': '宣传'},
    'other': {'name': '其他'}
}

# 评价维度（权重之和为100）
EVALUATION_DIMENSIONS = {
    'organization': {'name': '组织管理', 'weight': 20},
    'activity_quality': {'name': '活动质量', 'weight': 20},
    'member_participation': {'name': '成员参与', 'weight': 15},
    'achievement': {'name': '成果展示', 'weight': 20},
    'social_impact': {'name': '社会影响', 'weight': 10},
    'innovation': {'name': '创新发展', 'weight': 15}
}

# 社团等级
CLUB_LEVELS = {
    'star1': {'name': '一星', 'min_score': 50},
    'star2': {'name': '二星', 'min_score': 60},
    'star3': {'name': '三星', 'min_score': 70},
    'star4': {'name': '四星', 'min_score': 80},
    'star5': {'name': '五星', 'min_score': 90},
    'excellent': {'name': '优秀社团', 'min_score': 95},
    'model': {'name': '示范社团', 'min_score': 98}
}


class StudentClubService:
    """学生社团管理服务"""

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
                # 社团表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clubs (
                        club_id TEXT PRIMARY KEY,
                        club_name TEXT NOT NULL,
                        category TEXT,
                        description TEXT,
                        logo TEXT,
                        education_type TEXT,
                        founder_id TEXT,
                        founder_name TEXT,
                        president_id TEXT,
                        president_name TEXT,
                        instructor_id TEXT,
                        instructor_name TEXT,
                        established_date TEXT,
                        member_count INTEGER DEFAULT 0,
                        max_members INTEGER DEFAULT 50,
                        meeting_schedule TEXT,
                        location TEXT,
                        contact_info TEXT,
                        status TEXT DEFAULT 'pending',
                        level TEXT,
                        total_score REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 社团成员表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        club_id TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        student_name TEXT,
                        role TEXT DEFAULT 'member',
                        join_date TEXT,
                        status TEXT DEFAULT 'active',
                        attendance_rate REAL DEFAULT 0,
                        contribution_score REAL DEFAULT 0,
                        total_activities INTEGER DEFAULT 0,
                        leave_reason TEXT,
                        left_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 社团活动表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_activities (
                        activity_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        activity_name TEXT NOT NULL,
                        activity_type TEXT,
                        description TEXT,
                        objectives TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        location TEXT,
                        venue_booking_id TEXT,
                        max_participants INTEGER DEFAULT 50,
                        registered_count INTEGER DEFAULT 0,
                        actual_participants INTEGER DEFAULT 0,
                        budget REAL DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        approval_status TEXT DEFAULT 'pending',
                        approved_by TEXT,
                        approved_at TEXT,
                        outcome TEXT,
                        summary TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 活动报名表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id TEXT NOT NULL,
                        club_id TEXT,
                        student_id TEXT NOT NULL,
                        student_name TEXT,
                        register_time TEXT,
                        attend_status TEXT DEFAULT 'registered',
                        role_in_activity TEXT,
                        created_at TEXT
                    )
                ''')
                # 社团经费表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_funds (
                        fund_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        fund_type TEXT,
                        amount REAL DEFAULT 0,
                        direction TEXT,
                        category TEXT,
                        description TEXT,
                        transaction_date TEXT,
                        operator_id TEXT,
                        operator_name TEXT,
                        balance_after REAL DEFAULT 0,
                        receipt_url TEXT,
                        status TEXT DEFAULT 'confirmed',
                        created_at TEXT
                    )
                ''')
                # 经费预算表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fund_budgets (
                        budget_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        fiscal_year INTEGER,
                        fiscal_semester TEXT,
                        total_budget REAL DEFAULT 0,
                        total_income REAL DEFAULT 0,
                        total_expense REAL DEFAULT 0,
                        category_budgets TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 社团成果表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_achievements (
                        achievement_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        achievement_type TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        file_url TEXT,
                        event_name TEXT,
                        event_date TEXT,
                        achievement_date TEXT,
                        participants TEXT,
                        rating REAL DEFAULT 0,
                        is_public INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                # 社团评价表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        evaluator_id TEXT,
                        evaluator_name TEXT,
                        evaluator_type TEXT,
                        evaluation_period TEXT,
                        dimension_scores TEXT,
                        total_score REAL DEFAULT 0,
                        level TEXT,
                        comment TEXT,
                        suggestions TEXT,
                        created_at TEXT
                    )
                ''')
                # 成员评价表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS member_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        member_id TEXT NOT NULL,
                        member_name TEXT,
                        evaluator_id TEXT,
                        evaluator_name TEXT,
                        evaluator_type TEXT,
                        evaluation_period TEXT,
                        attendance_score REAL DEFAULT 0,
                        contribution_score REAL DEFAULT 0,
                        skill_score REAL DEFAULT 0,
                        attitude_score REAL DEFAULT 0,
                        total_score REAL DEFAULT 0,
                        comment TEXT,
                        created_at TEXT
                    )
                ''')
                # 活动评价表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        activity_id TEXT NOT NULL,
                        club_id TEXT,
                        evaluator_id TEXT,
                        evaluator_name TEXT,
                        evaluator_type TEXT,
                        organization_score REAL DEFAULT 0,
                        content_score REAL DEFAULT 0,
                        satisfaction_score REAL DEFAULT 0,
                        total_score REAL DEFAULT 0,
                        comment TEXT,
                        suggestions TEXT,
                        created_at TEXT
                    )
                ''')
                # 指导教师表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_instructors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        club_id TEXT NOT NULL,
                        instructor_id TEXT,
                        instructor_name TEXT,
                        assigned_date TEXT,
                        end_date TEXT,
                        responsibilities TEXT,
                        guidance_hours REAL DEFAULT 0,
                        evaluation_score REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                # 招新活动表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_recruitments (
                        recruitment_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        recruitment_name TEXT NOT NULL,
                        academic_year TEXT,
                        semester TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        target_audience TEXT,
                        description TEXT,
                        requirements TEXT,
                        quota INTEGER DEFAULT 30,
                        applied_count INTEGER DEFAULT 0,
                        accepted_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 招新报名表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recruitment_applications (
                        application_id TEXT PRIMARY KEY,
                        recruitment_id TEXT NOT NULL,
                        club_id TEXT,
                        student_id TEXT NOT NULL,
                        student_name TEXT,
                        grade TEXT,
                        apply_date TEXT,
                        self_intro TEXT,
                        skills TEXT,
                        interview_score REAL,
                        interview_notes TEXT,
                        status TEXT DEFAULT 'pending',
                        accepted_at TEXT,
                        created_at TEXT
                    )
                ''')
                # 社团场地表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_venues (
                        venue_id TEXT PRIMARY KEY,
                        venue_name TEXT NOT NULL,
                        location TEXT,
                        capacity INTEGER DEFAULT 50,
                        facilities TEXT,
                        available_times TEXT,
                        manager_id TEXT,
                        manager_name TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 场地预约表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS venue_bookings (
                        booking_id TEXT PRIMARY KEY,
                        venue_id TEXT NOT NULL,
                        club_id TEXT,
                        activity_id TEXT,
                        booker_id TEXT,
                        booker_name TEXT,
                        booking_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        purpose TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('学生社团管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 社团管理 ==========

    def create_club(self, club_name: str, category: str, **kwargs) -> Dict[str, Any]:
        try:
            club_id = f"sc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO clubs (
                            club_id, club_name, category, description, logo,
                            education_type, founder_id, founder_name,
                            president_id, president_name, instructor_id,
                            instructor_name, established_date, member_count,
                            max_members, meeting_schedule, location, contact_info,
                            status, level, total_score, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 'pending', NULL, 0, ?, ?)
                    ''', (club_id, club_name, category,
                          kwargs.get('description'), kwargs.get('logo'),
                          kwargs.get('education_type', 'common'),
                          kwargs.get('founder_id'), kwargs.get('founder_name'),
                          kwargs.get('president_id'), kwargs.get('president_name'),
                          kwargs.get('instructor_id'), kwargs.get('instructor_name'),
                          kwargs.get('established_date', now[:10]),
                          kwargs.get('max_members', 50),
                          kwargs.get('meeting_schedule'), kwargs.get('location'),
                          kwargs.get('contact_info'), now, now))
                    conn.commit()
                    logger.info(f'创建社团: {club_name} ({club_id})')
                    return {'success': True, 'club_id': club_id}
        except Exception as e:
            logger.error(f'创建社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_club(self, club_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE clubs SET status = ?, updated_at = ? WHERE club_id = ? AND status = ?',
                                 ('active', now, club_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'社团审核通过: {club_id}')
                        return {'success': True, 'status': 'active'}
                    return {'success': False, 'error': '社团不存在或状态不允许审核'}
        except Exception as e:
            logger.error(f'审核社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_club(self, club_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            allowed = ['club_name', 'category', 'description', 'logo', 'education_type',
                       'president_id', 'president_name', 'instructor_id', 'instructor_name',
                       'max_members', 'meeting_schedule', 'location', 'contact_info', 'status']
            updates = []
            params = []
            for k, v in kwargs.items():
                if k in allowed:
                    updates.append(f'{k} = ?')
                    params.append(v)
            if not updates:
                return {'success': False, 'error': '没有可更新字段'}
            updates.append('updated_at = ?')
            params.append(now)
            params.append(club_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE clubs SET {", ".join(updates)} WHERE club_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '社团不存在'}
        except Exception as e:
            logger.error(f'更新社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def dissolve_club(self, club_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE clubs SET status = ?, updated_at = ? WHERE club_id = ?',
                                 ('dissolved', now, club_id))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE club_members SET status = ?, left_date = ?, updated_at = ? WHERE club_id = ? AND status = ?',
                                     ('transferred', now[:10], now, club_id, 'active'))
                        conn.commit()
                        logger.info(f'社团解散: {club_id}')
                        return {'success': True}
                    return {'success': False, 'error': '社团不存在'}
        except Exception as e:
            logger.error(f'解散社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_club(self, club_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM clubs WHERE club_id = ?', (club_id,))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'club': dict(row)}
                return {'success': False, 'error': '社团不存在'}
        except Exception as e:
            logger.error(f'获取社团详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_clubs(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM clubs WHERE 1=1'
                params = []
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                clubs = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'clubs': clubs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社团列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成员管理 ==========

    def join_club(self, club_id: str, student_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT member_count, max_members, status FROM clubs WHERE club_id = ?', (club_id,))
                    club = cursor.fetchone()
                    if not club:
                        return {'success': False, 'error': '社团不存在'}
                    if club[2] != 'active':
                        return {'success': False, 'error': '社团状态不允许加入'}
                    if club[1] and club[0] >= club[1]:
                        return {'success': False, 'error': '社团人数已满'}
                    cursor.execute('SELECT id FROM club_members WHERE club_id = ? AND student_id = ? AND status = ?',
                                 (club_id, student_id, 'active'))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已是社团成员'}
                    cursor.execute('''
                        INSERT INTO club_members (club_id, student_id, student_name, role, join_date, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (club_id, student_id, kwargs.get('student_name'),
                          kwargs.get('role', 'member'), now[:10], now, now))
                    cursor.execute('UPDATE clubs SET member_count = member_count + 1, updated_at = ? WHERE club_id = ?', (now, club_id))
                    conn.commit()
                    logger.info(f'加入社团: {student_id} -> {club_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'加入社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def leave_club(self, club_id: str, student_id: str, reason: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE club_members SET status = ?, leave_reason = ?, left_date = ?, updated_at = ? WHERE club_id = ? AND student_id = ? AND status = ?',
                                 ('resigned', reason, now[:10], now, club_id, student_id, 'active'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE clubs SET member_count = MAX(member_count - 1, 0), updated_at = ? WHERE club_id = ?', (now, club_id))
                        conn.commit()
                        logger.info(f'退社: {student_id} <- {club_id}')
                        return {'success': True}
                    return {'success': False, 'error': '成员不存在或已离社'}
        except Exception as e:
            logger.error(f'退社失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_member_role(self, club_id: str, student_id: str, role: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            if role not in MEMBER_ROLES:
                return {'success': False, 'error': '无效的角色'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE club_members SET role = ?, updated_at = ? WHERE club_id = ? AND student_id = ? AND status = ?',
                                 (role, now, club_id, student_id, 'active'))
                    if cursor.rowcount > 0:
                        if role == 'president':
                            cursor.execute('UPDATE clubs SET president_id = ?, president_name = ?, updated_at = ? WHERE club_id = ?',
                                         (student_id, kwargs.get('student_name'), now, club_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员不存在'}
        except Exception as e:
            logger.error(f'更新成员职位失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_members(self, club_id: str, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_members WHERE club_id = ?'
                params = [club_id]
                if filters.get('role'):
                    query += ' AND role = ?'
                    params.append(filters['role'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY join_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                members = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'members': members, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取成员列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_member_info(self, club_id: str, student_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM club_members WHERE club_id = ? AND student_id = ?', (club_id, student_id))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'member': dict(row)}
                return {'success': False, 'error': '成员不存在'}
        except Exception as e:
            logger.error(f'获取成员详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 招新管理 ==========

    def create_recruitment(self, club_id: str, recruitment_name: str, **kwargs) -> Dict[str, Any]:
        try:
            recruitment_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO club_recruitments (
                            recruitment_id, club_id, recruitment_name, academic_year,
                            semester, start_date, end_date, target_audience, description,
                            requirements, quota, applied_count, accepted_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'open', ?, ?)
                    ''', (recruitment_id, club_id, recruitment_name,
                          kwargs.get('academic_year'), kwargs.get('semester'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('target_audience'), kwargs.get('description'),
                          kwargs.get('requirements'), kwargs.get('quota', 30), now, now))
                    conn.commit()
                    logger.info(f'创建招新活动: {recruitment_name} ({recruitment_id})')
                    return {'success': True, 'recruitment_id': recruitment_id}
        except Exception as e:
            logger.error(f'创建招新活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_recruitment(self, recruitment_id: str, student_id: str, **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"app_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT club_id, quota, applied_count, status FROM club_recruitments WHERE recruitment_id = ?', (recruitment_id,))
                    rec = cursor.fetchone()
                    if not rec:
                        return {'success': False, 'error': '招新活动不存在'}
                    if rec[3] != 'open':
                        return {'success': False, 'error': '招新活动已结束'}
                    if rec[1] and rec[2] >= rec[1]:
                        return {'success': False, 'error': '报名名额已满'}
                    cursor.execute('SELECT application_id FROM recruitment_applications WHERE recruitment_id = ? AND student_id = ?', (recruitment_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该招新'}
                    cursor.execute('''
                        INSERT INTO recruitment_applications (
                            application_id, recruitment_id, club_id, student_id, student_name,
                            grade, apply_date, self_intro, skills, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (application_id, recruitment_id, rec[0], student_id,
                          kwargs.get('student_name'), kwargs.get('grade'), now[:10],
                          kwargs.get('self_intro'), kwargs.get('skills'), now))
                    cursor.execute('UPDATE club_recruitments SET applied_count = applied_count + 1, updated_at = ? WHERE recruitment_id = ?', (now, recruitment_id))
                    conn.commit()
                    logger.info(f'招新报名: {student_id} -> {recruitment_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'招新报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def interview_applicant(self, application_id: str, score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE recruitment_applications SET interview_score = ?, interview_notes = ?, status = ? WHERE application_id = ? AND status = ?',
                                 (score, kwargs.get('interview_notes'), 'interviewed', application_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在或状态不允许'}
        except Exception as e:
            logger.error(f'面试记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def accept_applicant(self, application_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT recruitment_id, club_id, student_id, student_name FROM recruitment_applications WHERE application_id = ? AND status = ?',
                                 (application_id, 'interviewed'))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '报名记录不存在或未面试'}
                    cursor.execute('UPDATE recruitment_applications SET status = ?, accepted_at = ? WHERE application_id = ?',
                                 ('accepted', now[:10], application_id))
                    cursor.execute('UPDATE club_recruitments SET accepted_count = accepted_count + 1, updated_at = ? WHERE recruitment_id = ?', (now, app[0]))
                    # 自动加入社团
                    cursor.execute('SELECT id FROM club_members WHERE club_id = ? AND student_id = ?', (app[1], app[2]))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO club_members (club_id, student_id, student_name, role, join_date, status, created_at, updated_at)
                            VALUES (?, ?, ?, 'member', ?, 'active', ?, ?)
                        ''', (app[1], app[2], app[3], now[:10], now, now))
                        cursor.execute('UPDATE clubs SET member_count = member_count + 1, updated_at = ? WHERE club_id = ?', (now, app[1]))
                    conn.commit()
                    logger.info(f'录取: {application_id} -> {app[1]}')
                    return {'success': True, 'club_id': app[1]}
        except Exception as e:
            logger.error(f'录取失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_recruitments(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_recruitments WHERE 1=1'
                params = []
                if filters.get('club_id'):
                    query += ' AND club_id = ?'
                    params.append(filters['club_id'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                recruitments = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'recruitments': recruitments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取招新列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 活动管理 ==========

    def create_activity(self, club_id: str, activity_name: str, activity_type: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"act_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ACTIVITY_TYPES.get(activity_type, {})
            approval_status = 'pending' if config.get('requires_approval') else 'approved'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO club_activities (
                            activity_id, club_id, activity_name, activity_type, description,
                            objectives, start_date, end_date, start_time, end_time, location,
                            venue_booking_id, max_participants, registered_count, actual_participants,
                            budget, status, approval_status, approved_by, approved_at, outcome, summary,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 0, 0, ?, 'planning', ?, NULL, NULL, NULL, NULL, ?, ?)
                    ''', (activity_id, club_id, activity_name, activity_type,
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('location'), kwargs.get('max_participants', 50),
                          kwargs.get('budget', 0), approval_status, now, now))
                    conn.commit()
                    logger.info(f'创建社团活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_activity(self, activity_id: str, approved_by: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            approved = kwargs.get('approved', True)
            status = 'approved' if approved else 'rejected'
            act_status = 'approved' if approved else 'cancelled'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE club_activities SET approval_status = ?, approved_by = ?, approved_at = ?, status = ?, updated_at = ? WHERE activity_id = ? AND approval_status = ?',
                                 (status, approved_by, now, act_status, now, activity_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'approval_status': status}
                    return {'success': False, 'error': '活动不存在或状态不允许审批'}
        except Exception as e:
            logger.error(f'审批活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_activity(self, activity_id: str, student_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT club_id, max_participants, registered_count, status FROM club_activities WHERE activity_id = ?', (activity_id,))
                    act = cursor.fetchone()
                    if not act:
                        return {'success': False, 'error': '活动不存在'}
                    if act[3] not in ('approved', 'scheduled', 'in_progress'):
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if act[1] and act[2] >= act[1]:
                        return {'success': False, 'error': '活动名额已满'}
                    cursor.execute('SELECT id FROM activity_registrations WHERE activity_id = ? AND student_id = ?', (activity_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该活动'}
                    cursor.execute('''
                        INSERT INTO activity_registrations (activity_id, club_id, student_id, student_name, register_time, attend_status, role_in_activity, created_at)
                        VALUES (?, ?, ?, ?, ?, 'registered', ?, ?)
                    ''', (activity_id, act[0], student_id, kwargs.get('student_name'),
                          now, kwargs.get('role_in_activity'), now))
                    cursor.execute('UPDATE club_activities SET registered_count = registered_count + 1, updated_at = ? WHERE activity_id = ?', (now, activity_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_activity_outcome(self, activity_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE club_activities SET outcome = ?, summary = ?, actual_participants = ?, status = ?, updated_at = ? WHERE activity_id = ?',
                                 (kwargs.get('outcome'), kwargs.get('summary'),
                                  kwargs.get('actual_participants', 0), 'completed', now, activity_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '活动不存在'}
        except Exception as e:
            logger.error(f'记录活动成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_activities(self, club_id: str = None, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_activities WHERE 1=1'
                params = []
                if club_id:
                    query += ' AND club_id = ?'
                    params.append(club_id)
                if filters.get('activity_type'):
                    query += ' AND activity_type = ?'
                    params.append(filters['activity_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                activities = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'activities': activities, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 场地预约 ==========

    def register_venue(self, venue_name: str, **kwargs) -> Dict[str, Any]:
        try:
            venue_id = f"ven_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            facilities = kwargs.get('facilities', [])
            available_times = kwargs.get('available_times', [])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO club_venues (
                            venue_id, venue_name, location, capacity, facilities,
                            available_times, manager_id, manager_name, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (venue_id, venue_name, kwargs.get('location'),
                          kwargs.get('capacity', 50),
                          json.dumps(facilities, ensure_ascii=False),
                          json.dumps(available_times, ensure_ascii=False),
                          kwargs.get('manager_id'), kwargs.get('manager_name'), now, now))
                    conn.commit()
                    logger.info(f'注册场地: {venue_name} ({venue_id})')
                    return {'success': True, 'venue_id': venue_id}
        except Exception as e:
            logger.error(f'注册场地失败: {e}')
            return {'success': False, 'error': str(e)}

    def book_venue(self, venue_id: str, club_id: str, **kwargs) -> Dict[str, Any]:
        try:
            booking_id = f"vb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            booking_date = kwargs.get('booking_date', now[:10])
            start_time = kwargs.get('start_time')
            end_time = kwargs.get('end_time')
            if not start_time or not end_time:
                return {'success': False, 'error': '必须提供开始和结束时间'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM club_venues WHERE venue_id = ?', (venue_id,))
                    venue = cursor.fetchone()
                    if not venue:
                        return {'success': False, 'error': '场地不存在'}
                    if not venue[0]:
                        return {'success': False, 'error': '场地不可用'}
                    # 时段冲突检测：同一场地同一日期存在预约与新预约时间区间重叠
                    cursor.execute('''
                        SELECT booking_id FROM venue_bookings
                        WHERE venue_id = ? AND booking_date = ? AND status != ?
                        AND start_time < ? AND end_time > ?
                    ''', (venue_id, booking_date, 'cancelled', end_time, start_time))
                    if cursor.fetchone():
                        return {'success': False, 'error': '场地该时段已被预约'}
                    cursor.execute('''
                        INSERT INTO venue_bookings (
                            booking_id, venue_id, club_id, activity_id, booker_id, booker_name,
                            booking_date, start_time, end_time, purpose, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', ?)
                    ''', (booking_id, venue_id, club_id, kwargs.get('activity_id'),
                          kwargs.get('booker_id'), kwargs.get('booker_name'),
                          booking_date, start_time, end_time, kwargs.get('purpose'), now))
                    conn.commit()
                    logger.info(f'预约场地: {venue_id} ({booking_id})')
                    return {'success': True, 'booking_id': booking_id}
        except Exception as e:
            logger.error(f'预约场地失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_venues(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_venues WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})')
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                venues = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'venues': venues, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取场地列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_venue_bookings(self, venue_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM venue_bookings WHERE 1=1'
                params = []
                if venue_id:
                    query += ' AND venue_id = ?'
                    params.append(venue_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY booking_date DESC, start_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                bookings = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'bookings': bookings, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预约列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 经费管理 ==========

    def record_fund(self, club_id: str, fund_type: str, amount: float, direction: str, **kwargs) -> Dict[str, Any]:
        try:
            fund_id = f"fun_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 获取当前余额
                    cursor.execute('SELECT balance_after FROM club_funds WHERE club_id = ? ORDER BY created_at DESC LIMIT 1', (club_id,))
                    row = cursor.fetchone()
                    current_balance = row[0] if row else 0.0
                    if direction == 'income':
                        new_balance = current_balance + amount
                    else:
                        new_balance = current_balance - amount
                    cursor.execute('''
                        INSERT INTO club_funds (
                            fund_id, club_id, fund_type, amount, direction, category, description,
                            transaction_date, operator_id, operator_name, balance_after, receipt_url, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', ?)
                    ''', (fund_id, club_id, fund_type, amount, direction,
                          kwargs.get('category'), kwargs.get('description'),
                          kwargs.get('transaction_date', now[:10]),
                          kwargs.get('operator_id'), kwargs.get('operator_name'),
                          new_balance, kwargs.get('receipt_url'), now))
                    conn.commit()
                    logger.info(f'记录经费: {club_id} {direction} {amount}')
                    return {'success': True, 'fund_id': fund_id, 'balance': new_balance}
        except Exception as e:
            logger.error(f'记录经费失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_budget(self, club_id: str, fiscal_year: int, **kwargs) -> Dict[str, Any]:
        try:
            budget_id = f"bud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            category_budgets = kwargs.get('category_budgets', {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO fund_budgets (
                            budget_id, club_id, fiscal_year, fiscal_semester, total_budget,
                            total_income, total_expense, category_budgets, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, 'draft', ?, ?)
                    ''', (budget_id, club_id, fiscal_year, kwargs.get('fiscal_semester'),
                          kwargs.get('total_budget', 0),
                          json.dumps(category_budgets, ensure_ascii=False), now, now))
                    conn.commit()
                    logger.info(f'创建预算: {club_id} {fiscal_year} ({budget_id})')
                    return {'success': True, 'budget_id': budget_id}
        except Exception as e:
            logger.error(f'创建预算失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_fund_balance(self, club_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT balance_after FROM club_funds WHERE club_id = ? ORDER BY created_at DESC LIMIT 1', (club_id,))
                row = cursor.fetchone()
                balance = row[0] if row else 0.0
                return {'success': True, 'balance': balance}
        except Exception as e:
            logger.error(f'获取余额失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_funds(self, club_id: str, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_funds WHERE club_id = ?'
                params = [club_id]
                if filters.get('direction'):
                    query += ' AND direction = ?'
                    params.append(filters['direction'])
                if filters.get('fund_type'):
                    query += ' AND fund_type = ?'
                    params.append(filters['fund_type'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                funds = [dict(f) for f in cursor.fetchall()]
                return {'success': True, 'funds': funds, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取经费记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成果与评价 ==========

    def record_achievement(self, club_id: str, achievement_type: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            achievement_id = f"ach_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            participants = kwargs.get('participants', [])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO club_achievements (
                            achievement_id, club_id, achievement_type, title, description, file_url,
                            event_name, event_date, achievement_date, participants, rating, is_public, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (achievement_id, club_id, achievement_type, title,
                          kwargs.get('description'), kwargs.get('file_url'),
                          kwargs.get('event_name'), kwargs.get('event_date'),
                          kwargs.get('achievement_date', now[:10]),
                          json.dumps(participants, ensure_ascii=False),
                          kwargs.get('rating', 0),
                          1 if kwargs.get('is_public', True) else 0, now))
                    conn.commit()
                    logger.info(f'记录成果: {title} ({achievement_id})')
                    return {'success': True, 'achievement_id': achievement_id}
        except Exception as e:
            logger.error(f'记录成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_club(self, club_id: str, evaluator_id: str, dimension_scores: dict, **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"cev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            # 加权计算总分
            total_score = 0.0
            for dim, score in dimension_scores.items():
                weight = EVALUATION_DIMENSIONS.get(dim, {}).get('weight', 0)
                total_score += score * weight / 100
            # 等级判定
            if total_score >= 98:
                level = 'model'
            elif total_score >= 95:
                level = 'excellent'
            elif total_score >= 90:
                level = 'star5'
            elif total_score >= 80:
                level = 'star4'
            elif total_score >= 70:
                level = 'star3'
            elif total_score >= 60:
                level = 'star2'
            elif total_score >= 50:
                level = 'star1'
            else:
                level = None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO club_evaluations (
                            evaluation_id, club_id, evaluator_id, evaluator_name, evaluator_type,
                            evaluation_period, dimension_scores, total_score, level, comment, suggestions, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (evaluation_id, club_id, evaluator_id,
                          kwargs.get('evaluator_name'), kwargs.get('evaluator_type'),
                          kwargs.get('evaluation_period'),
                          json.dumps(dimension_scores, ensure_ascii=False),
                          total_score, level, kwargs.get('comment'),
                          kwargs.get('suggestions'), now))
                    cursor.execute('UPDATE clubs SET total_score = ?, level = ?, updated_at = ? WHERE club_id = ?',
                                 (total_score, level, now, club_id))
                    conn.commit()
                    logger.info(f'评价社团: {club_id} 总分 {total_score} 等级 {level}')
                    return {'success': True, 'evaluation_id': evaluation_id, 'total_score': total_score, 'level': level}
        except Exception as e:
            logger.error(f'评价社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_member(self, club_id: str, member_id: str, evaluator_id: str, **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"mev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            attendance_score = kwargs.get('attendance_score', 0)
            contribution_score = kwargs.get('contribution_score', 0)
            skill_score = kwargs.get('skill_score', 0)
            attitude_score = kwargs.get('attitude_score', 0)
            total_score = (attendance_score + contribution_score + skill_score + attitude_score) / 4
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO member_evaluations (
                            evaluation_id, club_id, member_id, member_name, evaluator_id, evaluator_name,
                            evaluator_type, evaluation_period, attendance_score, contribution_score,
                            skill_score, attitude_score, total_score, comment, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (evaluation_id, club_id, member_id, kwargs.get('member_name'),
                          evaluator_id, kwargs.get('evaluator_name'), kwargs.get('evaluator_type'),
                          kwargs.get('evaluation_period'), attendance_score, contribution_score,
                          skill_score, attitude_score, total_score, kwargs.get('comment'), now))
                    cursor.execute('UPDATE club_members SET attendance_rate = ?, contribution_score = ?, updated_at = ? WHERE club_id = ? AND student_id = ? AND status = ?',
                                 (attendance_score, contribution_score, now, club_id, member_id, 'active'))
                    conn.commit()
                    return {'success': True, 'evaluation_id': evaluation_id, 'total_score': total_score}
        except Exception as e:
            logger.error(f'评价成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_activity(self, activity_id: str, evaluator_id: str, **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"aev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            organization_score = kwargs.get('organization_score', 0)
            content_score = kwargs.get('content_score', 0)
            satisfaction_score = kwargs.get('satisfaction_score', 0)
            total_score = (organization_score + content_score + satisfaction_score) / 3
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT club_id FROM club_activities WHERE activity_id = ?', (activity_id,))
                    act = cursor.fetchone()
                    club_id = act[0] if act else None
                    cursor.execute('''
                        INSERT INTO activity_evaluations (
                            evaluation_id, activity_id, club_id, evaluator_id, evaluator_name, evaluator_type,
                            organization_score, content_score, satisfaction_score, total_score, comment, suggestions, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (evaluation_id, activity_id, club_id, evaluator_id,
                          kwargs.get('evaluator_name'), kwargs.get('evaluator_type'),
                          organization_score, content_score, satisfaction_score,
                          total_score, kwargs.get('comment'), kwargs.get('suggestions'), now))
                    conn.commit()
                    return {'success': True, 'evaluation_id': evaluation_id, 'total_score': total_score}
        except Exception as e:
            logger.error(f'评价活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_achievements(self, club_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_achievements WHERE 1=1'
                params = []
                if club_id:
                    query += ' AND club_id = ?'
                    params.append(club_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                achievements = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'achievements': achievements, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取成果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_evaluations(self, club_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_evaluations WHERE 1=1'
                params = []
                if club_id:
                    query += ' AND club_id = ?'
                    params.append(club_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                evaluations = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'evaluations': evaluations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 指导教师 ==========

    def assign_instructor(self, club_id: str, instructor_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO club_instructors (
                            club_id, instructor_id, instructor_name, assigned_date, end_date,
                            responsibilities, guidance_hours, evaluation_score, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'active', ?)
                    ''', (club_id, instructor_id, kwargs.get('instructor_name'),
                          kwargs.get('assigned_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('responsibilities'), now))
                    cursor.execute('UPDATE clubs SET instructor_id = ?, instructor_name = ?, updated_at = ? WHERE club_id = ?',
                                 (instructor_id, kwargs.get('instructor_name'), now, club_id))
                    conn.commit()
                    logger.info(f'分配指导教师: {instructor_id} -> {club_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配指导教师失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_instructors(self, club_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM club_instructors WHERE 1=1'
                params = []
                if club_id:
                    query += ' AND club_id = ?'
                    params.append(club_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY assigned_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                instructors = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'instructors': instructors, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取指导教师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # 基础查询条件
                club_cond = ' WHERE education_type = ?' if education_type else ''
                club_params = [education_type] if education_type else []
                # 社团总数
                cursor.execute(f'SELECT COUNT(*) as cnt FROM clubs{club_cond}', club_params)
                total_clubs = cursor.fetchone()['cnt']
                # 社团类别分布
                cursor.execute(f'SELECT category, COUNT(*) as cnt FROM clubs{club_cond} GROUP BY category', club_params)
                category_dist = {r['category']: r['cnt'] for r in cursor.fetchall()}
                # 社团状态分布
                cursor.execute(f'SELECT status, COUNT(*) as cnt FROM clubs{club_cond} GROUP BY status', club_params)
                status_dist = {r['status']: r['cnt'] for r in cursor.fetchall()}
                # 社团等级分布
                level_cond = ' WHERE education_type = ? AND level IS NOT NULL' if education_type else ' WHERE level IS NOT NULL'
                cursor.execute(f'SELECT level, COUNT(*) as cnt FROM clubs{level_cond} GROUP BY level', club_params)
                level_dist = {r['level']: r['cnt'] for r in cursor.fetchall()}
                # 成员人数分布（按社团类别）
                if education_type:
                    cursor.execute('''
                        SELECT c.category, COUNT(m.id) as cnt
                        FROM club_members m JOIN clubs c ON m.club_id = c.club_id
                        WHERE m.status = 'active' AND c.education_type = ?
                        GROUP BY c.category
                    ''', [education_type])
                else:
                    cursor.execute('''
                        SELECT c.category, COUNT(m.id) as cnt
                        FROM club_members m JOIN clubs c ON m.club_id = c.club_id
                        WHERE m.status = 'active'
                        GROUP BY c.category
                    ''')
                member_dist = {r['category']: r['cnt'] for r in cursor.fetchall()}
                # 活动统计
                act_cond = ' AND c.education_type = ?' if education_type else ''
                act_params = [education_type] if education_type else []
                cursor.execute(f'''
                    SELECT COUNT(DISTINCT a.activity_id) as total,
                           SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed,
                           SUM(CASE WHEN a.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                           SUM(a.registered_count) as registered
                    FROM club_activities a JOIN clubs c ON a.club_id = c.club_id
                    WHERE 1=1{act_cond}
                ''', act_params)
                act_row = cursor.fetchone()
                activity_stats = {
                    'total': act_row['total'] or 0,
                    'completed': act_row['completed'] or 0,
                    'in_progress': act_row['in_progress'] or 0,
                    'total_registered': act_row['registered'] or 0
                }
                # 经费收支统计
                cursor.execute(f'''
                    SELECT f.direction, SUM(f.amount) as total
                    FROM club_funds f JOIN clubs c ON f.club_id = c.club_id
                    WHERE 1=1{act_cond}
                    GROUP BY f.direction
                ''', act_params)
                fund_stats = {'income': 0, 'expense': 0}
                for r in cursor.fetchall():
                    fund_stats[r['direction']] = r['total'] or 0
                return {
                    'success': True,
                    'total_clubs': total_clubs,
                    'category_distribution': category_dist,
                    'status_distribution': status_dist,
                    'level_distribution': level_dist,
                    'member_distribution': member_dist,
                    'activity_statistics': activity_stats,
                    'fund_statistics': fund_stats
                }
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = StudentClubService()
    print('学生社团管理服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')