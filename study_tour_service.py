#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 研学旅行服务 (v15.10.0)
====================================
提供研学基地、研学线路、研学活动、课程任务、安全管理、成果评价、师资队伍等
综合管理服务。本模块同时支持成人教育（游学研修）与 K12 教育（研学旅行）的差异化需求。

核心能力：
1. 研学基地 - 基地管理、资质认证、课程资源
2. 研学线路 - 线路设计、主题分类、行程安排
3. 研学活动 - 活动组织、报名管理、行程执行
4. 课程任务 - 研学课程、学习任务、探究课题
5. 安全管理 - 安全预案、保险、应急处理、安全检查
6. 成果评价 - 研学成果、学习报告、评价反馈
7. 师资队伍 - 研学导师、培训、资质
8. K12研学旅行与成人游学研修差异化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'study_tour_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('StudyTour')


# ========== 研学配置 ==========

# 研学类型
TOUR_TYPES = {
    'history_history': {'name': '历史人文', 'typical_duration': '3-5天'},
    'nature_science': {'name': '自然科技', 'typical_duration': '2-4天'},
    'red_education': {'name': '红色教育', 'typical_duration': '2-3天'},
    'culture_art': {'name': '文化艺术', 'typical_duration': '3-5天'},
    'vocational_experience': {'name': '职业体验', 'typical_duration': '1-3天'},
    'military_training': {'name': '军事训练', 'typical_duration': '5-7天'},
    'international_exchange': {'name': '国际交流', 'typical_duration': '7-15天'},
    'ecology_environment': {'name': '生态环境', 'typical_duration': '2-4天'}
}

# 基地类型
BASE_TYPES = {
    'museum': {'name': '博物馆', 'certification_required': True},
    'memorial': {'name': '纪念馆', 'certification_required': True},
    'science_museum': {'name': '科技馆', 'certification_required': True},
    'historical_site': {'name': '历史遗址', 'certification_required': True},
    'nature_reserve': {'name': '自然保护区', 'certification_required': True},
    'enterprise': {'name': '企业', 'certification_required': False},
    'farm': {'name': '农庄', 'certification_required': False},
    'military': {'name': '军事', 'certification_required': True},
    'base_camp': {'name': '营地', 'certification_required': True},
    'university': {'name': '高校', 'certification_required': False}
}

# 研学活动状态
TOUR_STATUS = {
    'planning': {'name': '规划中'},
    'recruitment': {'name': '招募中'},
    'full': {'name': '名额已满'},
    'in_progress': {'name': '进行中'},
    'completed': {'name': '已完成'},
    'cancelled': {'name': '已取消'}
}

# 任务类型
TASK_TYPES = {
    'observation': {'name': '观察', 'deliverable': '观察记录'},
    'interview': {'name': '访谈', 'deliverable': '访谈报告'},
    'research': {'name': '调研', 'deliverable': '调研报告'},
    'experiment': {'name': '实验', 'deliverable': '实验报告'},
    'creation': {'name': '创作', 'deliverable': '作品'},
    'presentation': {'name': '汇报', 'deliverable': '汇报材料'},
    'reflection': {'name': '反思', 'deliverable': '反思日记'}
}

# 安全等级
SAFETY_LEVELS = {
    'low': {'name': '低风险', 'requires_approval': False},
    'medium': {'name': '中风险', 'requires_approval': False},
    'high': {'name': '高风险', 'requires_approval': True},
    'extreme': {'name': '极高风险', 'requires_approval': True}
}

# 保险类型
INSURANCE_TYPES = {
    'basic': {'name': '基础', 'coverage_amount': 100000},
    'comprehensive': {'name': '综合', 'coverage_amount': 300000},
    'premium': {'name': '高端', 'coverage_amount': 500000},
    'international': {'name': '国际', 'coverage_amount': 1000000}
}

# 紧急事件类型
EMERGENCY_TYPES = {
    'medical': {'name': '医疗', 'response_level': 'high'},
    'injury': {'name': '受伤', 'response_level': 'high'},
    'lost': {'name': '走失', 'response_level': 'extreme'},
    'weather': {'name': '天气', 'response_level': 'medium'},
    'natural_disaster': {'name': '自然灾害', 'response_level': 'extreme'},
    'traffic': {'name': '交通', 'response_level': 'high'},
    'security': {'name': '治安', 'response_level': 'extreme'},
    'other': {'name': '其他', 'response_level': 'low'}
}

# 评价维度（权重总和为 1.0）
EVALUATION_DIMENSIONS = {
    'participation': {'name': '参与度', 'weight': 0.15},
    'learning_gain': {'name': '学习收获', 'weight': 0.30},
    'teamwork': {'name': '团队合作', 'weight': 0.15},
    'discipline': {'name': '纪律', 'weight': 0.15},
    'safety_awareness': {'name': '安全意识', 'weight': 0.15},
    'innovation': {'name': '创新表现', 'weight': 0.10}
}

# 成果类型
ACHIEVEMENT_TYPES = {
    'report': {'name': '研究报告'},
    'works': {'name': '作品'},
    'presentation': {'name': '汇报'},
    'video': {'name': '视频'},
    'photo': {'name': '照片'},
    'group_project': {'name': '团队成果'}
}


class StudyTourService:
    """研学旅行服务"""

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
                    CREATE TABLE IF NOT EXISTS study_bases (
                        base_id TEXT PRIMARY KEY,
                        base_name TEXT NOT NULL,
                        base_type TEXT NOT NULL,
                        organization TEXT,
                        address TEXT,
                        city TEXT,
                        contact_person TEXT,
                        contact_phone TEXT,
                        capacity INTEGER DEFAULT 50,
                        facilities TEXT,
                        courses TEXT,
                        certification TEXT,
                        certification_date TEXT,
                        rating REAL DEFAULT 0,
                        review_count INTEGER DEFAULT 0,
                        introduction TEXT,
                        photos TEXT,
                        is_approved INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_routes (
                        route_id TEXT PRIMARY KEY,
                        route_name TEXT NOT NULL,
                        tour_type TEXT NOT NULL,
                        base_ids TEXT,
                        theme TEXT,
                        description TEXT,
                        duration_days INTEGER DEFAULT 3,
                        difficulty TEXT DEFAULT 'medium',
                        target_age TEXT,
                        target_grade TEXT,
                        price REAL DEFAULT 0,
                        itinerary TEXT,
                        learning_objectives TEXT,
                        included_services TEXT,
                        excluded_services TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_tours (
                        tour_id TEXT PRIMARY KEY,
                        tour_name TEXT NOT NULL,
                        route_id TEXT,
                        tour_type TEXT NOT NULL,
                        organizer_id INTEGER,
                        organizer_name TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        gathering_place TEXT,
                        gathering_time TEXT,
                        max_participants INTEGER DEFAULT 50,
                        min_participants INTEGER DEFAULT 10,
                        registered_count INTEGER DEFAULT 0,
                        price REAL DEFAULT 0,
                        registration_deadline TEXT,
                        status TEXT DEFAULT 'planning',
                        description TEXT,
                        requirements TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tour_registrations (
                        registration_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        grade TEXT,
                        parent_id INTEGER,
                        parent_name TEXT,
                        emergency_contact TEXT,
                        emergency_phone TEXT,
                        health_condition TEXT,
                        special_needs TEXT,
                        register_time TEXT,
                        fee_paid REAL DEFAULT 0,
                        paid_time TEXT,
                        status TEXT DEFAULT 'registered',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tour_courses (
                        course_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        base_id TEXT,
                        course_name TEXT NOT NULL,
                        course_type TEXT,
                        description TEXT,
                        objectives TEXT,
                        content TEXT,
                        duration_hours REAL DEFAULT 2,
                        instructor_id INTEGER,
                        instructor_name TEXT,
                        materials TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_tasks (
                        task_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        tour_id TEXT NOT NULL,
                        task_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        description TEXT,
                        requirements TEXT,
                        deliverable_format TEXT,
                        deadline TEXT,
                        difficulty TEXT DEFAULT 'medium',
                        is_group_work INTEGER DEFAULT 0,
                        group_size INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_submissions (
                        submission_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        group_members TEXT,
                        content TEXT,
                        file_url TEXT,
                        submit_time TEXT,
                        score REAL,
                        feedback TEXT,
                        graded_by INTEGER,
                        graded_at TEXT,
                        status TEXT DEFAULT 'submitted',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tour_safety_plans (
                        plan_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        safety_level TEXT NOT NULL,
                        risk_assessment TEXT,
                        prevention_measures TEXT,
                        emergency_procedures TEXT,
                        emergency_contacts TEXT,
                        medical_arrangements TEXT,
                        evacuation_plan TEXT,
                        prepared_by INTEGER,
                        prepared_at TEXT,
                        approved_by INTEGER,
                        approved_at TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tour_insurances (
                        insurance_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        registration_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        insurance_type TEXT NOT NULL,
                        provider TEXT,
                        policy_number TEXT,
                        coverage_amount REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        premium REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS safety_inspections (
                        inspection_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        inspector_id INTEGER,
                        inspector_name TEXT,
                        inspection_date TEXT,
                        inspection_items TEXT,
                        issues_found TEXT,
                        risk_level TEXT,
                        suggestions TEXT,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS emergency_events (
                        event_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        occurred_at TEXT,
                        location TEXT,
                        description TEXT,
                        involved_students TEXT,
                        severity TEXT,
                        response_actions TEXT,
                        handled_by INTEGER,
                        handled_at TEXT,
                        outcome TEXT,
                        reported_to_parent INTEGER DEFAULT 0,
                        follow_up TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tour_achievements (
                        achievement_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        achievement_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        file_url TEXT,
                        group_members TEXT,
                        rating REAL DEFAULT 0,
                        evaluated_by INTEGER,
                        evaluated_at TEXT,
                        is_excellent INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tour_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        evaluator_type TEXT NOT NULL,
                        dimension_scores TEXT,
                        total_score REAL DEFAULT 0,
                        grade TEXT,
                        comment TEXT,
                        suggestions TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_instructors (
                        instructor_id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        name TEXT NOT NULL,
                        title TEXT,
                        specialties TEXT,
                        certifications TEXT,
                        base_affiliation TEXT,
                        tour_count INTEGER DEFAULT 0,
                        total_students INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0,
                        rating_count INTEGER DEFAULT 0,
                        training_hours REAL DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tour_reflections (
                        reflection_id TEXT PRIMARY KEY,
                        tour_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        reflection_type TEXT DEFAULT 'daily',
                        content TEXT NOT NULL,
                        mood TEXT,
                        gains TEXT,
                        improvements TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('研学旅行服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 研学基地 ==========

    def register_study_base(self, base_name: str, base_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            base_id = f"stb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_bases (
                            base_id, base_name, base_type, organization,
                            address, city, contact_person, contact_phone,
                            capacity, facilities, courses, certification,
                            certification_date, rating, review_count,
                            introduction, photos, is_approved, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, 0, ?, ?)
                    ''', (base_id, base_name, base_type,
                          kwargs.get('organization'), kwargs.get('address'),
                          kwargs.get('city'), kwargs.get('contact_person'),
                          kwargs.get('contact_phone'), kwargs.get('capacity', 50),
                          json.dumps(kwargs.get('facilities', []), ensure_ascii=False),
                          json.dumps(kwargs.get('courses', []), ensure_ascii=False),
                          kwargs.get('certification'), kwargs.get('certification_date'),
                          kwargs.get('introduction'), kwargs.get('photos'),
                          now, now))
                    conn.commit()
                    logger.info(f'注册研学基地: {base_name} ({base_id})')
                    return {'success': True, 'base_id': base_id}
        except Exception as e:
            logger.error(f'注册研学基地失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_study_base(self, base_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            is_approved = 1 if kwargs.get('approved', True) else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE study_bases SET
                            is_approved = ?, certification = ?,
                            certification_date = ?, updated_at = ?
                        WHERE base_id = ?
                    ''', (is_approved, kwargs.get('certification'),
                          kwargs.get('certification_date', now[:10]), now, base_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审核研学基地: {base_id} (通过={is_approved})')
                        return {'success': True, 'is_approved': is_approved}
                    return {'success': False, 'error': '基地不存在'}
        except Exception as e:
            logger.error(f'审核研学基地失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_study_base(self, base_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM study_bases WHERE base_id = ?', (base_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '基地不存在'}
                base = dict(row)
                for field in ['facilities', 'courses']:
                    if base.get(field):
                        try:
                            base[field] = json.loads(base[field])
                        except (ValueError, TypeError):
                            pass
                return {'success': True, 'base': base}
        except Exception as e:
            logger.error(f'获取研学基地失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_study_bases(self, page: int = 1, page_size: int = 20,
                         **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM study_bases WHERE 1=1'
                params = []
                if filters.get('base_type'):
                    query += ' AND base_type = ?'
                    params.append(filters['base_type'])
                if filters.get('city'):
                    query += ' AND city = ?'
                    params.append(filters['city'])
                if filters.get('is_approved') is not None:
                    query += ' AND is_approved = ?'
                    params.append(1 if filters['is_approved'] else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                bases = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'bases': bases, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取研学基地列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 研学线路 ==========

    def create_study_route(self, route_name: str, tour_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            route_id = f"str_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_routes (
                            route_id, route_name, tour_type, base_ids, theme,
                            description, duration_days, difficulty, target_age,
                            target_grade, price, itinerary, learning_objectives,
                            included_services, excluded_services, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (route_id, route_name, tour_type,
                          json.dumps(kwargs.get('base_ids', []), ensure_ascii=False),
                          kwargs.get('theme'), kwargs.get('description'),
                          kwargs.get('duration_days', 3), kwargs.get('difficulty', 'medium'),
                          kwargs.get('target_age'), kwargs.get('target_grade'),
                          kwargs.get('price', 0),
                          json.dumps(kwargs.get('itinerary', []), ensure_ascii=False),
                          json.dumps(kwargs.get('learning_objectives', []), ensure_ascii=False),
                          json.dumps(kwargs.get('included_services', []), ensure_ascii=False),
                          json.dumps(kwargs.get('excluded_services', []), ensure_ascii=False),
                          kwargs.get('status', 'draft'), now, now))
                    conn.commit()
                    logger.info(f'创建研学线路: {route_name} ({route_id})')
                    return {'success': True, 'route_id': route_id}
        except Exception as e:
            logger.error(f'创建研学线路失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_study_route(self, route_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM study_routes WHERE route_id = ?', (route_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '线路不存在'}
                route = dict(row)
                for field in ['base_ids', 'itinerary', 'learning_objectives',
                              'included_services', 'excluded_services']:
                    if route.get(field):
                        try:
                            route[field] = json.loads(route[field])
                        except (ValueError, TypeError):
                            pass
                return {'success': True, 'route': route}
        except Exception as e:
            logger.error(f'获取研学线路失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_study_routes(self, page: int = 1, page_size: int = 20,
                          **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM study_routes WHERE 1=1'
                params = []
                if filters.get('tour_type'):
                    query += ' AND tour_type = ?'
                    params.append(filters['tour_type'])
                if filters.get('difficulty'):
                    query += ' AND difficulty = ?'
                    params.append(filters['difficulty'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                routes = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'routes': routes, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取研学线路列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 研学活动 ==========

    def create_study_tour(self, tour_name: str, route_id: str,
                          tour_type: str, **kwargs) -> Dict[str, Any]:
        try:
            tour_id = f"stu_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_tours (
                            tour_id, tour_name, route_id, tour_type,
                            organizer_id, organizer_name, start_date, end_date,
                            gathering_place, gathering_time, max_participants,
                            min_participants, registered_count, price,
                            registration_deadline, status, description,
                            requirements, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                    ''', (tour_id, tour_name, route_id, tour_type,
                          kwargs.get('organizer_id'), kwargs.get('organizer_name'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('gathering_place'), kwargs.get('gathering_time'),
                          kwargs.get('max_participants', 50),
                          kwargs.get('min_participants', 10),
                          kwargs.get('price', 0),
                          kwargs.get('registration_deadline'),
                          kwargs.get('status', 'planning'),
                          kwargs.get('description'), kwargs.get('requirements'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建研学活动: {tour_name} ({tour_id})')
                    return {'success': True, 'tour_id': tour_id}
        except Exception as e:
            logger.error(f'创建研学活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_tour(self, tour_id: str, student_id: int,
                      **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT max_participants, registered_count, status,
                               registration_deadline, price
                        FROM study_tours WHERE tour_id = ?
                    ''', (tour_id,))
                    tour = cursor.fetchone()
                    if not tour:
                        return {'success': False, 'error': '研学活动不存在'}
                    max_p, reg_count, status, deadline, price = tour
                    if status not in ('recruitment', 'planning'):
                        return {'success': False, 'error': '活动当前状态不允许报名'}
                    if max_p and reg_count >= max_p:
                        return {'success': False, 'error': '名额已满'}
                    if deadline and now > deadline:
                        return {'success': False, 'error': '报名已截止'}
                    cursor.execute('''
                        SELECT registration_id FROM tour_registrations
                        WHERE tour_id = ? AND student_id = ? AND status != 'cancelled'
                    ''', (tour_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该活动'}
                    registration_id = f"reg_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO tour_registrations (
                            registration_id, tour_id, student_id, student_name,
                            grade, parent_id, parent_name, emergency_contact,
                            emergency_phone, health_condition, special_needs,
                            register_time, fee_paid, paid_time, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'registered', ?, ?)
                    ''', (registration_id, tour_id, student_id,
                          kwargs.get('student_name'), kwargs.get('grade'),
                          kwargs.get('parent_id'), kwargs.get('parent_name'),
                          kwargs.get('emergency_contact'), kwargs.get('emergency_phone'),
                          kwargs.get('health_condition'), kwargs.get('special_needs'),
                          now, kwargs.get('fee_paid', price),
                          kwargs.get('paid_time'), now, now))
                    new_count = reg_count + 1
                    new_status = 'full' if max_p and new_count >= max_p else status
                    cursor.execute('UPDATE study_tours SET registered_count = ?, status = ?, updated_at = ? WHERE tour_id = ?',
                                 (new_count, new_status, now, tour_id))
                    conn.commit()
                    logger.info(f'研学报名: 学生{student_id} -> 活动{tour_id} ({registration_id})')
                    return {'success': True, 'registration_id': registration_id}
        except Exception as e:
            logger.error(f'研学报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def cancel_registration(self, registration_id: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT tour_id, status FROM tour_registrations WHERE registration_id = ?',
                                 (registration_id,))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '报名记录不存在'}
                    if reg[1] == 'cancelled':
                        return {'success': False, 'error': '该报名已取消'}
                    cursor.execute('UPDATE tour_registrations SET status = \'cancelled\', updated_at = ? WHERE registration_id = ?',
                                 (now, registration_id))
                    cursor.execute('UPDATE study_tours SET registered_count = MAX(registered_count - 1, 0), updated_at = ? WHERE tour_id = ?',
                                 (now, reg[0]))
                    conn.commit()
                    logger.info(f'取消研学报名: {registration_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'取消研学报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_study_tour(self, tour_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM study_tours WHERE tour_id = ?', (tour_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '研学活动不存在'}
                return {'success': True, 'tour': dict(row)}
        except Exception as e:
            logger.error(f'获取研学活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_study_tours(self, page: int = 1, page_size: int = 20,
                         **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM study_tours WHERE 1=1'
                params = []
                if filters.get('tour_type'):
                    query += ' AND tour_type = ?'
                    params.append(filters['tour_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tours = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tours': tours, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取研学活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 课程与任务 ==========

    def add_tour_course(self, tour_id: str, course_name: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"tc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tour_courses (
                            course_id, tour_id, base_id, course_name,
                            course_type, description, objectives, content,
                            duration_hours, instructor_id, instructor_name,
                            materials, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (course_id, tour_id, kwargs.get('base_id'),
                          course_name, kwargs.get('course_type'),
                          kwargs.get('description'),
                          json.dumps(kwargs.get('objectives', []), ensure_ascii=False),
                          kwargs.get('content'), kwargs.get('duration_hours', 2),
                          kwargs.get('instructor_id'), kwargs.get('instructor_name'),
                          kwargs.get('materials'), now))
                    conn.commit()
                    logger.info(f'添加研学课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'添加研学课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_study_task(self, course_id: str, task_name: str,
                          task_type: str, **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"tk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TASK_TYPES.get(task_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_tasks (
                            task_id, course_id, tour_id, task_name, task_type,
                            description, requirements, deliverable_format,
                            deadline, difficulty, is_group_work, group_size,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (task_id, course_id, kwargs.get('tour_id'),
                          task_name, task_type, kwargs.get('description'),
                          kwargs.get('requirements'),
                          kwargs.get('deliverable_format', config.get('deliverable')),
                          kwargs.get('deadline'), kwargs.get('difficulty', 'medium'),
                          1 if kwargs.get('is_group_work') else 0,
                          kwargs.get('group_size', 1), now, now))
                    conn.commit()
                    logger.info(f'创建学习任务: {task_name} ({task_id})')
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'创建学习任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_task(self, task_id: str, student_id: int,
                    **kwargs) -> Dict[str, Any]:
        try:
            submission_id = f"sub_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT tour_id FROM study_tasks WHERE task_id = ?', (task_id,))
                    task = cursor.fetchone()
                    if not task:
                        return {'success': False, 'error': '任务不存在'}
                    cursor.execute('''
                        INSERT INTO task_submissions (
                            submission_id, task_id, student_id, student_name,
                            group_members, content, file_url, submit_time,
                            score, feedback, graded_by, graded_at, status,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, 'submitted', ?)
                    ''', (submission_id, task_id, student_id,
                          kwargs.get('student_name'),
                          json.dumps(kwargs.get('group_members', []), ensure_ascii=False),
                          kwargs.get('content'), kwargs.get('file_url'),
                          now, now))
                    conn.commit()
                    logger.info(f'提交任务: 学生{student_id} -> 任务{task_id} ({submission_id})')
                    return {'success': True, 'submission_id': submission_id}
        except Exception as e:
            logger.error(f'提交任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def grade_task(self, submission_id: str, score: float,
                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE task_submissions SET
                            score = ?, feedback = ?, graded_by = ?,
                            graded_at = ?, status = 'graded'
                        WHERE submission_id = ? AND status = 'submitted'
                    ''', (score, kwargs.get('feedback'),
                          kwargs.get('graded_by'), now, submission_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'批改任务: {submission_id} 分数={score}')
                        return {'success': True, 'score': score}
                    return {'success': False, 'error': '提交记录不存在或已批改'}
        except Exception as e:
            logger.error(f'批改任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_tasks(self, tour_id: str = None, page: int = 1,
                   page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM study_tasks WHERE 1=1'
                params = []
                if tour_id:
                    query += ' AND tour_id = ?'
                    params.append(tour_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tasks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tasks': tasks, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全管理 ==========

    def create_safety_plan(self, tour_id: str, safety_level: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"sp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tour_safety_plans (
                            plan_id, tour_id, safety_level, risk_assessment,
                            prevention_measures, emergency_procedures,
                            emergency_contacts, medical_arrangements,
                            evacuation_plan, prepared_by, prepared_at,
                            approved_by, approved_at, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 'draft', ?, ?)
                    ''', (plan_id, tour_id, safety_level,
                          json.dumps(kwargs.get('risk_assessment', []), ensure_ascii=False),
                          json.dumps(kwargs.get('prevention_measures', []), ensure_ascii=False),
                          json.dumps(kwargs.get('emergency_procedures', []), ensure_ascii=False),
                          json.dumps(kwargs.get('emergency_contacts', []), ensure_ascii=False),
                          kwargs.get('medical_arrangements'),
                          kwargs.get('evacuation_plan'),
                          kwargs.get('prepared_by'), now, now, now))
                    conn.commit()
                    logger.info(f'创建安全预案: 活动{tour_id} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建安全预案失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_safety_plan(self, plan_id: str, approved_by: int,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            approved = kwargs.get('approved', True)
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE tour_safety_plans SET
                            approved_by = ?, approved_at = ?, status = ?, updated_at = ?
                        WHERE plan_id = ? AND status = 'draft'
                    ''', (approved_by, now, status, now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审核安全预案: {plan_id} ({status})')
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '预案不存在或状态不允许审核'}
        except Exception as e:
            logger.error(f'审核安全预案失败: {e}')
            return {'success': False, 'error': str(e)}

    def purchase_insurance(self, tour_id: str, registration_id: str,
                           insurance_type: str, **kwargs) -> Dict[str, Any]:
        try:
            insurance_id = f"ins_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INSURANCE_TYPES.get(insurance_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, student_name FROM tour_registrations WHERE registration_id = ?',
                                 (registration_id,))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '报名记录不存在'}
                    policy_number = f"POL{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
                    cursor.execute('''
                        INSERT INTO tour_insurances (
                            insurance_id, tour_id, registration_id, student_id,
                            student_name, insurance_type, provider, policy_number,
                            coverage_amount, start_date, end_date, premium,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (insurance_id, tour_id, registration_id, reg[0], reg[1],
                          insurance_type, kwargs.get('provider', '中国人保'),
                          policy_number,
                          kwargs.get('coverage_amount', config.get('coverage_amount', 0)),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('premium', 0), now))
                    conn.commit()
                    logger.info(f'购买保险: {policy_number} ({insurance_id})')
                    return {'success': True, 'insurance_id': insurance_id,
                            'policy_number': policy_number}
        except Exception as e:
            logger.error(f'购买保险失败: {e}')
            return {'success': False, 'error': str(e)}

    def conduct_safety_inspection(self, tour_id: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            inspection_id = f"si_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO safety_inspections (
                            inspection_id, tour_id, inspector_id, inspector_name,
                            inspection_date, inspection_items, issues_found,
                            risk_level, suggestions, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (inspection_id, tour_id, kwargs.get('inspector_id'),
                          kwargs.get('inspector_name'),
                          kwargs.get('inspection_date', now[:10]),
                          json.dumps(kwargs.get('inspection_items', []), ensure_ascii=False),
                          kwargs.get('issues_found'), kwargs.get('risk_level', 'low'),
                          kwargs.get('suggestions'),
                          kwargs.get('status', 'completed'), now))
                    conn.commit()
                    logger.info(f'安全检查: 活动{tour_id} ({inspection_id})')
                    return {'success': True, 'inspection_id': inspection_id}
        except Exception as e:
            logger.error(f'安全检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def report_emergency(self, tour_id: str, event_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"emg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EMERGENCY_TYPES.get(event_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO emergency_events (
                            event_id, tour_id, event_type, occurred_at,
                            location, description, involved_students, severity,
                            response_actions, handled_by, handled_at, outcome,
                            reported_to_parent, follow_up, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, NULL, 'open', ?, ?)
                    ''', (event_id, tour_id, event_type,
                          kwargs.get('occurred_at', now),
                          kwargs.get('location'), kwargs.get('description'),
                          json.dumps(kwargs.get('involved_students', []), ensure_ascii=False),
                          kwargs.get('severity', config.get('response_level', 'medium')),
                          json.dumps(kwargs.get('response_actions', []), ensure_ascii=False),
                          1 if kwargs.get('reported_to_parent') else 0,
                          now, now))
                    conn.commit()
                    logger.info(f'报告紧急事件: 活动{tour_id} 类型{event_type} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'报告紧急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def handle_emergency(self, event_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE emergency_events SET
                            response_actions = ?, handled_by = ?, handled_at = ?,
                            outcome = ?, reported_to_parent = ?, follow_up = ?,
                            status = 'resolved', updated_at = ?
                        WHERE event_id = ? AND status = 'open'
                    ''', (json.dumps(kwargs.get('response_actions', []), ensure_ascii=False),
                          kwargs.get('handled_by'), now, kwargs.get('outcome'),
                          1 if kwargs.get('reported_to_parent') else 0,
                          kwargs.get('follow_up'), now, event_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'处理紧急事件: {event_id}')
                        return {'success': True, 'status': 'resolved'}
                    return {'success': False, 'error': '事件不存在或已处理'}
        except Exception as e:
            logger.error(f'处理紧急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_emergency_events(self, page: int = 1, page_size: int = 20,
                              **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM emergency_events WHERE 1=1'
                params = []
                if filters.get('tour_id'):
                    query += ' AND tour_id = ?'
                    params.append(filters['tour_id'])
                if filters.get('event_type'):
                    query += ' AND event_type = ?'
                    params.append(filters['event_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY occurred_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                events = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'events': events, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取紧急事件列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成果与评价 ==========

    def record_achievement(self, tour_id: str, student_id: int,
                           achievement_type: str, title: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            achievement_id = f"ach_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tour_achievements (
                            achievement_id, tour_id, student_id, student_name,
                            achievement_type, title, description, file_url,
                            group_members, rating, evaluated_by, evaluated_at,
                            is_excellent, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (achievement_id, tour_id, student_id,
                          kwargs.get('student_name'), achievement_type, title,
                          kwargs.get('description'), kwargs.get('file_url'),
                          json.dumps(kwargs.get('group_members', []), ensure_ascii=False),
                          kwargs.get('rating', 0), kwargs.get('evaluated_by'),
                          kwargs.get('evaluated_at'), 0, now))
                    conn.commit()
                    logger.info(f'记录研学成果: {title} ({achievement_id})')
                    return {'success': True, 'achievement_id': achievement_id}
        except Exception as e:
            logger.error(f'记录研学成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_evaluation(self, tour_id: str, student_id: int,
                          evaluator_type: str, dimension_scores: Dict[str, float],
                          **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"evl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            # 按权重加权计算总分
            total_score = 0.0
            for dim, score in dimension_scores.items():
                weight = EVALUATION_DIMENSIONS.get(dim, {}).get('weight', 0)
                total_score += float(score) * weight
            total_score = round(total_score, 1)
            # 等级判定
            if total_score >= 90:
                grade = '优秀'
            elif total_score >= 80:
                grade = '良好'
            elif total_score >= 70:
                grade = '中等'
            elif total_score >= 60:
                grade = '合格'
            else:
                grade = '需努力'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tour_evaluations (
                            evaluation_id, tour_id, student_id, student_name,
                            evaluator_type, dimension_scores, total_score, grade,
                            comment, suggestions, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (evaluation_id, tour_id, student_id,
                          kwargs.get('student_name'), evaluator_type,
                          json.dumps(dimension_scores, ensure_ascii=False),
                          total_score, grade, kwargs.get('comment'),
                          kwargs.get('suggestions'), now))
                    conn.commit()
                    logger.info(f'创建评价: 学生{student_id} 总分{total_score} 等级{grade} ({evaluation_id})')
                    return {'success': True, 'evaluation_id': evaluation_id,
                            'total_score': total_score, 'grade': grade}
        except Exception as e:
            logger.error(f'创建评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_reflection(self, tour_id: str, student_id: int,
                       content: str, **kwargs) -> Dict[str, Any]:
        try:
            reflection_id = f"rfl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tour_reflections (
                            reflection_id, tour_id, student_id, student_name,
                            reflection_type, content, mood, gains, improvements, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (reflection_id, tour_id, student_id,
                          kwargs.get('student_name'),
                          kwargs.get('reflection_type', 'daily'),
                          content, kwargs.get('mood'),
                          json.dumps(kwargs.get('gains', []), ensure_ascii=False),
                          kwargs.get('improvements'), now))
                    conn.commit()
                    logger.info(f'添加研学反思: 学生{student_id} 活动{tour_id} ({reflection_id})')
                    return {'success': True, 'reflection_id': reflection_id}
        except Exception as e:
            logger.error(f'添加研学反思失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_achievements(self, tour_id: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM tour_achievements WHERE 1=1'
                params = []
                if tour_id:
                    query += ' AND tour_id = ?'
                    params.append(tour_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                achievements = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'achievements': achievements,
                        'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取成果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_evaluations(self, tour_id: str = None, page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM tour_evaluations WHERE 1=1'
                params = []
                if tour_id:
                    query += ' AND tour_id = ?'
                    params.append(tour_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                evaluations = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'evaluations': evaluations,
                        'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 研学导师 ==========

    def register_instructor(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            instructor_id = f"ins_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_instructors (
                            instructor_id, user_id, name, title, specialties,
                            certifications, base_affiliation, tour_count,
                            total_students, rating, rating_count, training_hours,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?, 1, ?, ?)
                    ''', (instructor_id, kwargs.get('user_id'), name,
                          kwargs.get('title'),
                          json.dumps(kwargs.get('specialties', []), ensure_ascii=False),
                          json.dumps(kwargs.get('certifications', []), ensure_ascii=False),
                          kwargs.get('base_affiliation'),
                          kwargs.get('training_hours', 0), now, now))
                    conn.commit()
                    logger.info(f'注册研学导师: {name} ({instructor_id})')
                    return {'success': True, 'instructor_id': instructor_id}
        except Exception as e:
            logger.error(f'注册研学导师失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_instructors(self, page: int = 1, page_size: int = 20,
                         **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM study_instructors WHERE 1=1'
                params = []
                if filters.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if filters['is_active'] else 0)
                if filters.get('base_affiliation'):
                    query += ' AND base_affiliation = ?'
                    params.append(filters['base_affiliation'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                instructors = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'instructors': instructors,
                        'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取导师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats: Dict[str, Any] = {'success': True, 'education_type': education_type}

                # 活动类型分布
                cursor.execute('SELECT tour_type, COUNT(*) as cnt FROM study_tours GROUP BY tour_type')
                tour_type_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['tour_type_distribution'] = tour_type_dist

                # 基地类型分布
                cursor.execute('SELECT base_type, COUNT(*) as cnt FROM study_bases GROUP BY base_type')
                base_type_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['base_type_distribution'] = base_type_dist

                # 报名统计
                cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN status=\'registered\' THEN 1 ELSE 0 END) as active, SUM(CASE WHEN status=\'cancelled\' THEN 1 ELSE 0 END) as cancelled FROM tour_registrations')
                reg_row = cursor.fetchone()
                stats['registration_statistics'] = {
                    'total': reg_row[0] or 0,
                    'active': reg_row[1] or 0,
                    'cancelled': reg_row[2] or 0
                }

                # 安全事件统计
                cursor.execute('SELECT event_type, COUNT(*) as cnt FROM emergency_events GROUP BY event_type')
                emergency_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['emergency_statistics'] = emergency_dist
                cursor.execute('SELECT COUNT(*) FROM emergency_events WHERE status = \'open\'')
                stats['open_emergencies'] = cursor.fetchone()[0] or 0

                # 成果类型分布
                cursor.execute('SELECT achievement_type, COUNT(*) as cnt FROM tour_achievements GROUP BY achievement_type')
                achievement_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['achievement_type_distribution'] = achievement_dist

                # 评价等级分布
                cursor.execute('SELECT grade, COUNT(*) as cnt FROM tour_evaluations GROUP BY grade')
                grade_dist = {row[0]: row[1] for row in cursor.fetchall()}
                stats['evaluation_grade_distribution'] = grade_dist

                # 活动总数与基地总数
                cursor.execute('SELECT COUNT(*) FROM study_tours')
                stats['total_tours'] = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM study_bases WHERE is_approved = 1')
                stats['approved_bases'] = cursor.fetchone()[0] or 0

                logger.info(f'获取统计: 活动{stats["total_tours"]} 基地{stats["approved_bases"]}')
                return stats
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = StudyTourService()
    print('研学旅行服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
