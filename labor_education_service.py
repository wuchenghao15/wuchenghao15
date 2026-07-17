#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 劳动教育服务 (v15.9.0)
====================================
提供劳动课程、劳动实践、劳动技能、劳动评价、实践基地、勤工助学、
劳动档案等综合管理服务，支持成人教育和K12教育的差异化需求。

核心能力：
1. 劳动课程 - 日常生活劳动、生产劳动、服务性劳动课程
2. 劳动实践 - 实践活动、劳动周、劳动基地
3. 劳动技能 - 技能培训、技能等级、技能认证
4. 劳动评价 - 劳动态度、劳动技能、劳动成果评价
5. 实践基地 - 基地管理、合作单位、岗位安排
6. 勤工助学 - 岗位发布、申请、安排、考核
7. 劳动档案 - 劳动经历记录、劳动素养档案
8. K12劳动教育与成人职业劳动差异化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labor_education_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LaborEducation')


# ========== 劳动配置 ==========

# 劳动类别
LABOR_CATEGORIES = {
    'daily_life': {'name': '日常生活劳动', 'description': '与个人生活起居相关的自我服务性劳动'},
    'productive': {'name': '生产劳动', 'description': '直接创造物质财富的生产性劳动'},
    'service': {'name': '服务性劳动', 'description': '为他人和社会提供服务的公益性劳动'},
    'vocational': {'name': '职业劳动', 'description': '与职业岗位相关的专业性劳动'},
    'innovative': {'name': '创新劳动', 'description': '以创新创造为导向的新型劳动'}
}

# 劳动类型
LABOR_TYPES = {
    'cooking': {'name': '烹饪', 'category': 'daily_life'},
    'cleaning': {'name': '清洁', 'category': 'daily_life'},
    'laundry': {'name': '洗衣', 'category': 'daily_life'},
    'gardening': {'name': '园艺', 'category': 'daily_life'},
    'farming': {'name': '农业', 'category': 'productive'},
    'crafts': {'name': '手工艺', 'category': 'productive'},
    'repair': {'name': '维修', 'category': 'productive'},
    'volunteer': {'name': '志愿服务', 'category': 'service'},
    'internship': {'name': '实习', 'category': 'vocational'},
    'research': {'name': '科研辅助', 'category': 'vocational'},
    'campus_work': {'name': '校园劳动', 'category': 'service'},
    'community_service': {'name': '社区服务', 'category': 'service'}
}

# 劳动课程类型
LABOR_COURSE_TYPES = {
    'theoretical': {'name': '理论', 'has_practice': False},
    'practical': {'name': '实践', 'has_practice': True},
    'integrated': {'name': '理实一体', 'has_practice': True},
    'project': {'name': '项目式', 'has_practice': True},
    'experience': {'name': '体验式', 'has_practice': True}
}

# 劳动技能等级
SKILL_LEVELS = {
    'novice': {'name': '初学者', 'level': 1, 'min_hours': 0},
    'apprentice': {'name': '学徒', 'level': 2, 'min_hours': 20},
    'proficient': {'name': '熟练', 'level': 3, 'min_hours': 60},
    'expert': {'name': '精通', 'level': 4, 'min_hours': 120},
    'master': {'name': '大师', 'level': 5, 'min_hours': 240}
}

# 实践基地类型
PRACTICE_BASE_TYPES = {
    'school': {'name': '校内', 'cooperation_type': 'self'},
    'farm': {'name': '农庄', 'cooperation_type': 'cooperation'},
    'factory': {'name': '工厂', 'cooperation_type': 'cooperation'},
    'community': {'name': '社区', 'cooperation_type': 'cooperation'},
    'enterprise': {'name': '企业', 'cooperation_type': 'cooperation'},
    'public_service': {'name': '公共服务', 'cooperation_type': 'cooperation'},
    'research': {'name': '科研', 'cooperation_type': 'cooperation'}
}

# 勤工助学岗位类型
WORK_STUDY_TYPES = {
    'library': {'name': '图书馆', 'hourly_wage': 15.0},
    'admin': {'name': '办公室', 'hourly_wage': 15.0},
    'lab': {'name': '实验室', 'hourly_wage': 18.0},
    'canteen': {'name': '食堂', 'hourly_wage': 14.0},
    'dormitory': {'name': '宿舍', 'hourly_wage': 14.0},
    'tutoring': {'name': '辅导', 'hourly_wage': 25.0},
    'research_assistant': {'name': '科研助理', 'hourly_wage': 20.0},
    'campus_maintenance': {'name': '校园维护', 'hourly_wage': 16.0}
}

# 评价维度
EVALUATION_DIMENSIONS = {
    'attitude': {'name': '劳动态度', 'weight': 0.2},
    'skill': {'name': '劳动技能', 'weight': 0.25},
    'quality': {'name': '劳动质量', 'weight': 0.25},
    'innovation': {'name': '创新精神', 'weight': 0.1},
    'cooperation': {'name': '合作精神', 'weight': 0.1},
    'safety': {'name': '安全意识', 'weight': 0.1}
}

# 劳动评价等级
LABOR_GRADES = {
    'excellent': {'name': '优秀', 'score_range': (90, 100)},
    'good': {'name': '良好', 'score_range': (80, 90)},
    'pass': {'name': '合格', 'score_range': (60, 80)},
    'fail': {'name': '不合格', 'score_range': (0, 60)}
}


class LaborEducationService:
    """劳动教育服务"""

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
                    CREATE TABLE IF NOT EXISTS labor_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_type TEXT,
                        labor_category TEXT,
                        labor_type TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        description TEXT,
                        objectives TEXT,
                        duration_hours INTEGER DEFAULT 32,
                        theory_hours INTEGER DEFAULT 8,
                        practice_hours INTEGER DEFAULT 24,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        materials_needed TEXT,
                        location TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        practice_hours REAL DEFAULT 0,
                        theory_score REAL,
                        practice_score REAL,
                        final_grade TEXT,
                        status TEXT DEFAULT 'enrolled',
                        created_at TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_activities (
                        activity_id TEXT PRIMARY KEY,
                        activity_name TEXT NOT NULL,
                        activity_type TEXT,
                        labor_category TEXT,
                        labor_type TEXT,
                        description TEXT,
                        organizer TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        location TEXT,
                        max_participants INTEGER DEFAULT 50,
                        registered_count INTEGER DEFAULT 0,
                        required_hours INTEGER DEFAULT 8,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id TEXT NOT NULL,
                        student_id INTEGER,
                        student_name TEXT,
                        register_time TEXT,
                        actual_hours REAL DEFAULT 0,
                        attendance_status TEXT DEFAULT 'registered',
                        performance TEXT,
                        evaluation TEXT,
                        created_at TEXT,
                        UNIQUE(activity_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_skills (
                        skill_id TEXT PRIMARY KEY,
                        skill_name TEXT NOT NULL,
                        labor_type TEXT,
                        description TEXT,
                        required_hours REAL DEFAULT 20,
                        difficulty TEXT DEFAULT 'medium',
                        certification_available INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS skill_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        skill_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        assessor_id INTEGER,
                        assessor_name TEXT,
                        assessment_date TEXT,
                        theory_score REAL,
                        practice_score REAL,
                        total_score REAL,
                        current_level TEXT,
                        new_level TEXT,
                        passed INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_skill_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        skill_id TEXT NOT NULL,
                        skill_name TEXT,
                        level TEXT,
                        acquired_date TEXT,
                        total_hours REAL DEFAULT 0,
                        assessment_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(student_id, skill_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS practice_bases (
                        base_id TEXT PRIMARY KEY,
                        base_name TEXT NOT NULL,
                        base_type TEXT,
                        partner_organization TEXT,
                        address TEXT,
                        contact_person TEXT,
                        contact_phone TEXT,
                        capacity INTEGER DEFAULT 30,
                        cooperation_type TEXT,
                        agreement_start TEXT,
                        agreement_end TEXT,
                        available_positions INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS base_positions (
                        position_id TEXT PRIMARY KEY,
                        base_id TEXT NOT NULL,
                        position_name TEXT NOT NULL,
                        position_desc TEXT,
                        required_skills TEXT,
                        capacity INTEGER DEFAULT 10,
                        filled_count INTEGER DEFAULT 0,
                        duration_weeks INTEGER DEFAULT 4,
                        requirements TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS position_arrangements (
                        arrangement_id TEXT PRIMARY KEY,
                        position_id TEXT NOT NULL,
                        base_id TEXT,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        supervisor TEXT,
                        evaluation_score REAL,
                        feedback TEXT,
                        status TEXT DEFAULT 'arranged',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_study_positions (
                        position_id TEXT PRIMARY KEY,
                        position_name TEXT NOT NULL,
                        position_type TEXT,
                        department TEXT,
                        supervisor_id INTEGER,
                        supervisor_name TEXT,
                        weekly_hours INTEGER DEFAULT 8,
                        hourly_wage REAL DEFAULT 15.0,
                        total_positions INTEGER DEFAULT 1,
                        filled_positions INTEGER DEFAULT 0,
                        requirements TEXT,
                        semester TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_study_applications (
                        application_id TEXT PRIMARY KEY,
                        position_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        apply_date TEXT,
                        status TEXT DEFAULT 'pending',
                        approved_by TEXT,
                        approved_at TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        total_hours REAL DEFAULT 0,
                        total_earned REAL DEFAULT 0,
                        evaluation TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(position_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_portfolios (
                        portfolio_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        total_labor_hours REAL DEFAULT 0,
                        total_courses INTEGER DEFAULT 0,
                        total_activities INTEGER DEFAULT 0,
                        total_skills INTEGER DEFAULT 0,
                        skill_list TEXT,
                        activity_history TEXT,
                        work_study_hours REAL DEFAULT 0,
                        evaluation_summary TEXT,
                        attitude_score REAL,
                        skill_score REAL,
                        quality_score REAL,
                        innovation_score REAL,
                        overall_grade TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        evaluator_id INTEGER,
                        evaluator_name TEXT,
                        evaluation_type TEXT,
                        target_id TEXT,
                        dimension_scores TEXT,
                        total_score REAL,
                        grade TEXT,
                        comment TEXT,
                        evaluation_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_awards (
                        award_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        award_name TEXT NOT NULL,
                        award_type TEXT,
                        award_level TEXT,
                        award_date TEXT,
                        description TEXT,
                        certificate_url TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('劳动教育服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 劳动课程 ==========

    def create_course(self, course_name: str, course_type: str,
                      labor_category: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"le_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_courses (
                            course_id, course_name, course_type, labor_category,
                            labor_type, education_type, grade_level, teacher_id,
                            teacher_name, description, objectives, duration_hours,
                            theory_hours, practice_hours, max_students,
                            enrolled_count, materials_needed, location, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?)
                    ''', (course_id, course_name, course_type, labor_category,
                          kwargs.get('labor_type'), kwargs.get('education_type', 'common'),
                          kwargs.get('grade_level'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('description'),
                          kwargs.get('objectives'), kwargs.get('duration_hours', 32),
                          kwargs.get('theory_hours', 8), kwargs.get('practice_hours', 24),
                          kwargs.get('max_students', 30), kwargs.get('materials_needed'),
                          kwargs.get('location'), now, now))
                    conn.commit()
                    logger.info(f'创建劳动课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建劳动课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_course(self, course_id: str, student_id: int,
                      **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM labor_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO labor_enrollments (course_id, student_id, student_name, enroll_date, status, created_at)
                        VALUES (?, ?, ?, ?, 'enrolled', ?)
                    ''', (course_id, student_id, kwargs.get('student_name'), now[:10], now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE labor_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'劳动课程报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_course_grade(self, enrollment_id: int, theory_score: float,
                            practice_score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            # 课程成绩计算：final_score = theory_score*0.4 + practice_score*0.6
            final_score = theory_score * 0.4 + practice_score * 0.6
            grade = 'excellent' if final_score >= 90 else ('good' if final_score >= 80 else ('pass' if final_score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE labor_enrollments SET
                            theory_score = ?, practice_score = ?, final_grade = ?,
                            attendance_count = ?, practice_hours = ?, status = 'completed'
                        WHERE id = ?
                    ''', (theory_score, practice_score, grade,
                          kwargs.get('attendance_count', 0),
                          kwargs.get('practice_hours', 0), enrollment_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'final_score': final_score, 'grade': grade}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录课程成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_courses(self, page: int = 1, page_size: int = 20,
                     **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_courses WHERE 1=1'
                params = []
                if filters.get('labor_category'):
                    query += ' AND labor_category = ?'
                    params.append(filters['labor_category'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('course_type'):
                    query += ' AND course_type = ?'
                    params.append(filters['course_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                courses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'courses': courses, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course(self, course_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM labor_courses WHERE course_id = ?', (course_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '课程不存在'}
                course = dict(row)
                cursor.execute('SELECT * FROM labor_enrollments WHERE course_id = ?', (course_id,))
                enrollments = [dict(e) for e in cursor.fetchall()]
                course['enrollments'] = enrollments
                return {'success': True, 'course': course}
        except Exception as e:
            logger.error(f'获取课程详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 劳动实践 ==========

    def create_activity(self, activity_name: str, activity_type: str,
                        labor_category: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"lac_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_activities (
                            activity_id, activity_name, activity_type, labor_category,
                            labor_type, description, organizer, start_date, end_date,
                            location, max_participants, registered_count, required_hours,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'scheduled', ?, ?)
                    ''', (activity_id, activity_name, activity_type, labor_category,
                          kwargs.get('labor_type'), kwargs.get('description'),
                          kwargs.get('organizer'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('location'),
                          kwargs.get('max_participants', 50),
                          kwargs.get('required_hours', 8), now, now))
                    conn.commit()
                    logger.info(f'创建劳动活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建劳动活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_activity(self, activity_id: str, student_id: int,
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM labor_activities WHERE activity_id = ?', (activity_id,))
                    activity = cursor.fetchone()
                    if not activity:
                        return {'success': False, 'error': '活动不存在'}
                    if activity[2] != 'scheduled':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if activity[0] and activity[1] >= activity[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO activity_registrations (activity_id, student_id, student_name, register_time, attendance_status, created_at)
                        VALUES (?, ?, ?, ?, 'registered', ?)
                    ''', (activity_id, student_id, kwargs.get('student_name'), now, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE labor_activities SET registered_count = registered_count + 1, updated_at = ? WHERE activity_id = ?', (now, activity_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_activity_hours(self, registration_id: int, actual_hours: float,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE activity_registrations SET
                            actual_hours = ?, attendance_status = ?, performance = ?, evaluation = ?
                        WHERE id = ?
                    ''', (actual_hours, kwargs.get('attendance_status', 'attended'),
                          kwargs.get('performance'), kwargs.get('evaluation'), registration_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'actual_hours': actual_hours}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录劳动时长失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_activities(self, page: int = 1, page_size: int = 20,
                        **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_activities WHERE 1=1'
                params = []
                if filters.get('labor_category'):
                    query += ' AND labor_category = ?'
                    params.append(filters['labor_category'])
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
                return {'success': True, 'activities': activities, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 劳动技能 ==========

    def register_skill(self, skill_name: str, labor_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            skill_id = f"lsk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_skills (
                            skill_id, skill_name, labor_type, description,
                            required_hours, difficulty, certification_available,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (skill_id, skill_name, labor_type, kwargs.get('description'),
                          kwargs.get('required_hours', 20),
                          kwargs.get('difficulty', 'medium'),
                          kwargs.get('certification_available', 1), now, now))
                    conn.commit()
                    logger.info(f'登记劳动技能: {skill_name} ({skill_id})')
                    return {'success': True, 'skill_id': skill_id}
        except Exception as e:
            logger.error(f'登记劳动技能失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_skill(self, skill_id: str, student_id: int,
                     **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"lsa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            theory_score = kwargs.get('theory_score', 0)
            practice_score = kwargs.get('practice_score', 0)
            total_score = theory_score * 0.4 + practice_score * 0.6
            passed = 1 if total_score >= 60 else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    # 获取学生当前技能等级
                    cursor.execute('SELECT level, total_hours FROM student_skill_records WHERE student_id = ? AND skill_id = ?', (student_id, skill_id))
                    record = cursor.fetchone()
                    current_level = record[0] if record else 'novice'
                    current_hours = record[1] if record else 0
                    # 获取技能信息
                    cursor.execute('SELECT skill_name, required_hours FROM labor_skills WHERE skill_id = ?', (skill_id,))
                    skill = cursor.fetchone()
                    if not skill:
                        return {'success': False, 'error': '技能不存在'}
                    skill_name = skill[0]
                    # 判定等级升降：累计时长达标 + 考核通过
                    total_hours = current_hours + kwargs.get('assessed_hours', skill[1])
                    new_level = self._determine_skill_level(total_hours, total_score, passed)
                    cursor.execute('''
                        INSERT INTO skill_assessments (
                            assessment_id, skill_id, student_id, student_name,
                            assessor_id, assessor_name, assessment_date, theory_score,
                            practice_score, total_score, current_level, new_level,
                            passed, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (assessment_id, skill_id, student_id, kwargs.get('student_name'),
                          kwargs.get('assessor_id'), kwargs.get('assessor_name'),
                          kwargs.get('assessment_date', now[:10]), theory_score,
                          practice_score, total_score, current_level, new_level,
                          passed, kwargs.get('notes'), now))
                    # 更新学生技能档案
                    cursor.execute('''
                        INSERT OR REPLACE INTO student_skill_records (
                            student_id, skill_id, skill_name, level, acquired_date,
                            total_hours, assessment_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (student_id, skill_id, skill_name, new_level,
                          now[:10], total_hours,
                          (record[0] is not None) + 1 if record else 1, now, now))
                    conn.commit()
                    return {'success': True, 'assessment_id': assessment_id,
                            'total_score': total_score, 'new_level': new_level,
                            'passed': bool(passed)}
        except Exception as e:
            logger.error(f'技能考核失败: {e}')
            return {'success': False, 'error': str(e)}

    def _determine_skill_level(self, total_hours: float, total_score: float,
                               passed: int) -> str:
        """根据累计时长和考核成绩判定技能等级"""
        if not passed or total_score < 60:
            return 'novice'
        if total_hours >= SKILL_LEVELS['master']['min_hours'] and total_score >= 90:
            return 'master'
        if total_hours >= SKILL_LEVELS['expert']['min_hours'] and total_score >= 80:
            return 'expert'
        if total_hours >= SKILL_LEVELS['proficient']['min_hours']:
            return 'proficient'
        if total_hours >= SKILL_LEVELS['apprentice']['min_hours']:
            return 'apprentice'
        return 'novice'

    def get_student_skills(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT ssr.*, ls.labor_type, ls.difficulty, ls.required_hours
                    FROM student_skill_records ssr
                    LEFT JOIN labor_skills ls ON ssr.skill_id = ls.skill_id
                    WHERE ssr.student_id = ?
                    ORDER BY ssr.updated_at DESC
                ''', (student_id,))
                skills = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'skills': skills, 'count': len(skills)}
        except Exception as e:
            logger.error(f'获取学生技能档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_skills(self, page: int = 1, page_size: int = 20,
                    **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_skills WHERE 1=1'
                params = []
                if filters.get('labor_type'):
                    query += ' AND labor_type = ?'
                    params.append(filters['labor_type'])
                if filters.get('difficulty'):
                    query += ' AND difficulty = ?'
                    params.append(filters['difficulty'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                skills = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'skills': skills, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取技能列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实践基地 ==========

    def register_practice_base(self, base_name: str, base_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            base_id = f"lbp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PRACTICE_BASE_TYPES.get(base_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO practice_bases (
                            base_id, base_name, base_type, partner_organization,
                            address, contact_person, contact_phone, capacity,
                            cooperation_type, agreement_start, agreement_end,
                            available_positions, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (base_id, base_name, base_type,
                          kwargs.get('partner_organization'), kwargs.get('address'),
                          kwargs.get('contact_person'), kwargs.get('contact_phone'),
                          kwargs.get('capacity', 30),
                          kwargs.get('cooperation_type', config.get('cooperation_type')),
                          kwargs.get('agreement_start'), kwargs.get('agreement_end'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'注册实践基地: {base_name} ({base_id})')
                    return {'success': True, 'base_id': base_id}
        except Exception as e:
            logger.error(f'注册实践基地失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_base_position(self, base_id: str, position_name: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            position_id = f"lps_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO base_positions (
                            position_id, base_id, position_name, position_desc,
                            required_skills, capacity, filled_count, duration_weeks,
                            requirements, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 'open', ?)
                    ''', (position_id, base_id, position_name,
                          kwargs.get('position_desc'), kwargs.get('required_skills'),
                          kwargs.get('capacity', 10), kwargs.get('duration_weeks', 4),
                          kwargs.get('requirements'), now))
                    cursor.execute('UPDATE practice_bases SET available_positions = available_positions + 1, updated_at = ? WHERE base_id = ?', (now, base_id))
                    conn.commit()
                    return {'success': True, 'position_id': position_id}
        except Exception as e:
            logger.error(f'添加基地岗位失败: {e}')
            return {'success': False, 'error': str(e)}

    def arrange_position(self, position_id: str, student_id: int,
                         **kwargs) -> Dict[str, Any]:
        try:
            arrangement_id = f"lar_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT base_id, capacity, filled_count, status FROM base_positions WHERE position_id = ?', (position_id,))
                    position = cursor.fetchone()
                    if not position:
                        return {'success': False, 'error': '岗位不存在'}
                    if position[3] != 'open':
                        return {'success': False, 'error': '岗位状态不允许安排'}
                    if position[1] and position[2] >= position[1]:
                        return {'success': False, 'error': '岗位名额已满'}
                    base_id = position[0]
                    cursor.execute('''
                        INSERT INTO position_arrangements (
                            arrangement_id, position_id, base_id, student_id,
                            student_name, start_date, end_date, supervisor,
                            evaluation_score, feedback, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 'arranged', ?, ?)
                    ''', (arrangement_id, position_id, base_id, student_id,
                          kwargs.get('student_name'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('supervisor'), now, now))
                    cursor.execute('UPDATE base_positions SET filled_count = filled_count + 1 WHERE position_id = ?', (position_id,))
                    if position[2] + 1 >= position[1]:
                        cursor.execute('UPDATE base_positions SET status = ? WHERE position_id = ?', ('full', position_id))
                    conn.commit()
                    return {'success': True, 'arrangement_id': arrangement_id}
        except Exception as e:
            logger.error(f'安排岗位失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_practice_bases(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM practice_bases WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})')
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                bases = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'bases': bases, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取基地列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 勤工助学 ==========

    def create_work_study_position(self, position_name: str, position_type: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            position_id = f"lwp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = WORK_STUDY_TYPES.get(position_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO work_study_positions (
                            position_id, position_name, position_type, department,
                            supervisor_id, supervisor_name, weekly_hours, hourly_wage,
                            total_positions, filled_positions, requirements, semester,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'open', ?, ?)
                    ''', (position_id, position_name, position_type,
                          kwargs.get('department'), kwargs.get('supervisor_id'),
                          kwargs.get('supervisor_name'),
                          kwargs.get('weekly_hours', 8),
                          kwargs.get('hourly_wage', config.get('hourly_wage', 15.0)),
                          kwargs.get('total_positions', 1), kwargs.get('requirements'),
                          kwargs.get('semester'), now, now))
                    conn.commit()
                    logger.info(f'发布勤工助学岗位: {position_name} ({position_id})')
                    return {'success': True, 'position_id': position_id}
        except Exception as e:
            logger.error(f'发布勤工助学岗位失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_work_study(self, position_id: str, student_id: int,
                         **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"lwa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT total_positions, filled_positions, status, hourly_wage FROM work_study_positions WHERE position_id = ?', (position_id,))
                    position = cursor.fetchone()
                    if not position:
                        return {'success': False, 'error': '岗位不存在'}
                    if position[2] != 'open':
                        return {'success': False, 'error': '岗位状态不允许申请'}
                    if position[1] >= position[0]:
                        return {'success': False, 'error': '岗位已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO work_study_applications (
                            application_id, position_id, student_id, student_name,
                            apply_date, status, start_date, end_date, total_hours,
                            total_earned, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, 0, 0, ?, ?)
                    ''', (application_id, position_id, student_id,
                          kwargs.get('student_name'), now[:10],
                          kwargs.get('start_date'), kwargs.get('end_date'), now, now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'application_id': application_id}
                    return {'success': False, 'error': '已申请该岗位'}
        except Exception as e:
            logger.error(f'申请勤工助学失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_work_study(self, application_id: str, approved: bool,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT position_id, status FROM work_study_applications WHERE application_id = ?', (application_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '申请不存在'}
                    if app[1] != 'pending':
                        return {'success': False, 'error': '申请状态不允许审核'}
                    cursor.execute('''
                        UPDATE work_study_applications SET
                            status = ?, approved_by = ?, approved_at = ?, updated_at = ?
                        WHERE application_id = ?
                    ''', (status, kwargs.get('approved_by'), now, now, application_id))
                    if approved:
                        cursor.execute('UPDATE work_study_positions SET filled_positions = filled_positions + 1, updated_at = ? WHERE position_id = ?', (now, app[0]))
                        cursor.execute('SELECT total_positions, filled_positions FROM work_study_positions WHERE position_id = ?', (app[0],))
                        pos = cursor.fetchone()
                        if pos and pos[1] >= pos[0]:
                            cursor.execute('UPDATE work_study_positions SET status = ?, updated_at = ? WHERE position_id = ?', ('full', now, app[0]))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'审核勤工助学申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_work_study_hours(self, application_id: str, hours: float,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT position_id, total_hours, total_earned FROM work_study_applications WHERE application_id = ? AND status = ?', (application_id, 'approved'))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '申请不存在或未通过审核'}
                    cursor.execute('SELECT hourly_wage FROM work_study_positions WHERE position_id = ?', (app[0],))
                    pos = cursor.fetchone()
                    hourly_wage = pos[0] if pos else 15.0
                    # 计算报酬
                    new_total_hours = app[1] + hours
                    new_total_earned = app[2] + hours * hourly_wage
                    cursor.execute('''
                        UPDATE work_study_applications SET
                            total_hours = ?, total_earned = ?, evaluation = ?, updated_at = ?
                        WHERE application_id = ?
                    ''', (new_total_hours, new_total_earned, kwargs.get('evaluation'), now, application_id))
                    conn.commit()
                    return {'success': True, 'total_hours': new_total_hours,
                            'total_earned': new_total_earned,
                            'this_payment': hours * hourly_wage}
        except Exception as e:
            logger.error(f'记录勤工助学工时失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_work_study_positions(self, page: int = 1, page_size: int = 20,
                                  **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM work_study_positions WHERE 1=1'
                params = []
                if filters.get('position_type'):
                    query += ' AND position_type = ?'
                    params.append(filters['position_type'])
                if filters.get('department'):
                    query += ' AND department = ?'
                    params.append(filters['department'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('semester'):
                    query += ' AND semester = ?'
                    params.append(filters['semester'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                positions = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'positions': positions, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取勤工助学岗位列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 劳动评价与档案 ==========

    def create_evaluation(self, student_id: int, evaluation_type: str,
                          dimension_scores: Dict[str, float],
                          **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"lev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            # 劳动评价总分计算：根据各维度权重加权计算
            total_score = 0.0
            total_weight = 0.0
            for dim, score in dimension_scores.items():
                weight = EVALUATION_DIMENSIONS.get(dim, {}).get('weight', 0)
                total_score += score * weight
                total_weight += weight
            if total_weight > 0:
                total_score = round(total_score, 2)
            # 等级判定：>=90优秀, >=80良好, >=60合格, <60不合格
            grade = 'excellent' if total_score >= 90 else ('good' if total_score >= 80 else ('pass' if total_score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_evaluations (
                            evaluation_id, student_id, student_name, evaluator_id,
                            evaluator_name, evaluation_type, target_id, dimension_scores,
                            total_score, grade, comment, evaluation_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (evaluation_id, student_id, kwargs.get('student_name'),
                          kwargs.get('evaluator_id'), kwargs.get('evaluator_name'),
                          evaluation_type, kwargs.get('target_id'),
                          json.dumps(dimension_scores, ensure_ascii=False),
                          total_score, grade, kwargs.get('comment'),
                          kwargs.get('evaluation_date', now[:10]), now))
                    conn.commit()
                    logger.info(f'创建劳动评价: 学生{student_id} ({evaluation_id}) 等级{grade}')
                    return {'success': True, 'evaluation_id': evaluation_id,
                            'total_score': total_score, 'grade': grade}
        except Exception as e:
            logger.error(f'创建劳动评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_portfolio(self, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            portfolio_id = f"lpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    # 汇总课程数据
                    cursor.execute('''
                        SELECT COUNT(*) as cnt, COALESCE(SUM(practice_hours), 0) as hours
                        FROM labor_enrollments WHERE student_id = ?
                    ''', (student_id,))
                    course_data = cursor.fetchone()
                    total_courses = course_data['cnt']
                    course_hours = course_data['hours']
                    # 汇总活动数据
                    cursor.execute('''
                        SELECT COUNT(*) as cnt, COALESCE(SUM(actual_hours), 0) as hours
                        FROM activity_registrations WHERE student_id = ?
                    ''', (student_id,))
                    activity_data = cursor.fetchone()
                    total_activities = activity_data['cnt']
                    activity_hours = activity_data['hours']
                    # 汇总技能数据
                    cursor.execute('SELECT skill_name, level FROM student_skill_records WHERE student_id = ?', (student_id,))
                    skills = [dict(s) for s in cursor.fetchall()]
                    total_skills = len(skills)
                    skill_list = json.dumps(skills, ensure_ascii=False)
                    # 汇总勤工助学数据
                    cursor.execute('''
                        SELECT COALESCE(SUM(total_hours), 0) as hours
                        FROM work_study_applications WHERE student_id = ? AND status = 'approved'
                    ''', (student_id,))
                    work_hours = cursor.fetchone()['hours'] or 0
                    # 汇总活动历史
                    cursor.execute('SELECT activity_id, actual_hours, performance FROM activity_registrations WHERE student_id = ?', (student_id,))
                    activity_history = json.dumps([dict(a) for a in cursor.fetchall()], ensure_ascii=False)
                    # 汇总评价数据
                    cursor.execute('SELECT AVG(total_score) as avg, grade FROM labor_evaluations WHERE student_id = ? GROUP BY grade', (student_id,))
                    eval_summary = json.dumps([dict(e) for e in cursor.fetchall()], ensure_ascii=False)
                    cursor.execute('SELECT dimension_scores FROM labor_evaluations WHERE student_id = ?', (student_id,))
                    dim_totals = {}
                    for row in cursor.fetchall():
                        try:
                            scores = json.loads(row['dimension_scores'])
                            for dim, score in scores.items():
                                dim_totals.setdefault(dim, []).append(score)
                        except Exception:
                            pass
                    dim_avg = {dim: round(sum(vals) / len(vals), 2) for dim, vals in dim_totals.items()}
                    total_labor_hours = course_hours + activity_hours + work_hours
                    overall_grade = 'fail'
                    if total_skills > 0 or total_labor_hours > 0:
                        overall_grade = 'pass'
                    cursor.execute('SELECT student_name FROM labor_portfolios WHERE student_id = ?', (student_id,))
                    existing = cursor.fetchone()
                    student_name = kwargs.get('student_name') or (existing['student_name'] if existing else None)
                    cursor.execute('''
                        INSERT OR REPLACE INTO labor_portfolios (
                            portfolio_id, student_id, student_name, education_type,
                            total_labor_hours, total_courses, total_activities,
                            total_skills, skill_list, activity_history, work_study_hours,
                            evaluation_summary, attitude_score, skill_score, quality_score,
                            innovation_score, overall_grade, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (portfolio_id, student_id, student_name,
                          kwargs.get('education_type', 'common'),
                          total_labor_hours, total_courses, total_activities,
                          total_skills, skill_list, activity_history, work_hours,
                          eval_summary,
                          dim_avg.get('attitude'), dim_avg.get('skill'),
                          dim_avg.get('quality'), dim_avg.get('innovation'),
                          overall_grade, now, now))
                    conn.commit()
                    return {'success': True, 'portfolio_id': portfolio_id,
                            'total_labor_hours': total_labor_hours,
                            'total_skills': total_skills}
        except Exception as e:
            logger.error(f'更新劳动档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_portfolio(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM labor_portfolios WHERE student_id = ?', (student_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '劳动档案不存在'}
                portfolio = dict(row)
                # 解析JSON字段
                for field in ['skill_list', 'activity_history', 'evaluation_summary']:
                    if portfolio.get(field):
                        try:
                            portfolio[field] = json.loads(portfolio[field])
                        except Exception:
                            pass
                return {'success': True, 'portfolio': portfolio}
        except Exception as e:
            logger.error(f'获取劳动档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_award(self, student_id: int, award_name: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            award_id = f"law_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_awards (
                            award_id, student_id, student_name, award_name,
                            award_type, award_level, award_date, description,
                            certificate_url, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (award_id, student_id, kwargs.get('student_name'), award_name,
                          kwargs.get('award_type', 'outstanding_student'),
                          kwargs.get('award_level'),
                          kwargs.get('award_date', now[:10]),
                          kwargs.get('description'), kwargs.get('certificate_url'), now))
                    conn.commit()
                    logger.info(f'记录劳动表彰: {award_name} ({award_id})')
                    return {'success': True, 'award_id': award_id}
        except Exception as e:
            logger.error(f'记录劳动表彰失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_awards(self, student_id: int = None, page: int = 1,
                    page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_awards WHERE 1=1'
                params = []
                if student_id is not None:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                awards = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'awards': awards, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取表彰列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 课程类别分布
                if education_type:
                    cursor.execute('SELECT labor_category, COUNT(*) FROM labor_courses WHERE education_type = ? GROUP BY labor_category', (education_type,))
                else:
                    cursor.execute('SELECT labor_category, COUNT(*) FROM labor_courses GROUP BY labor_category')
                category_dist = [{'category': row[0], 'count': row[1]} for row in cursor.fetchall()]
                # 活动参与统计
                cursor.execute('SELECT COUNT(*) as total, COALESCE(SUM(registered_count), 0) as registered FROM labor_activities')
                activity_stats = cursor.fetchone()
                activity_participation = {
                    'total_activities': activity_stats[0] or 0,
                    'total_registrations': activity_stats[1] or 0
                }
                # 技能等级分布
                cursor.execute('SELECT level, COUNT(*) FROM student_skill_records GROUP BY level')
                skill_level_dist = [{'level': row[0], 'count': row[1]} for row in cursor.fetchall()]
                # 基地数量
                cursor.execute('SELECT COUNT(*) FROM practice_bases')
                base_count = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM practice_bases WHERE status = ?', ('active',))
                active_base_count = cursor.fetchone()[0] or 0
                # 勤工助学统计
                cursor.execute('SELECT COUNT(*) as total, COALESCE(SUM(filled_positions), 0) as filled FROM work_study_positions')
                ws_stats = cursor.fetchone()
                cursor.execute('SELECT COALESCE(SUM(total_hours), 0), COALESCE(SUM(total_earned), 0) FROM work_study_applications WHERE status = ?', ('approved',))
                ws_payment = cursor.fetchone()
                work_study_stats = {
                    'total_positions': ws_stats[0] or 0,
                    'filled_positions': ws_stats[1] or 0,
                    'total_hours': ws_payment[0] or 0,
                    'total_earned': ws_payment[1] or 0
                }
                # 评价等级分布
                cursor.execute('SELECT grade, COUNT(*) FROM labor_evaluations GROUP BY grade')
                eval_grade_dist = [{'grade': row[0], 'count': row[1]} for row in cursor.fetchall()]
                return {'success': True, 'statistics': {
                    'category_distribution': category_dist,
                    'activity_participation': activity_participation,
                    'skill_level_distribution': skill_level_dist,
                    'base_count': base_count,
                    'active_base_count': active_base_count,
                    'work_study_stats': work_study_stats,
                    'evaluation_grade_distribution': eval_grade_dist
                }}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = LaborEducationService()
    print('劳动教育服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
