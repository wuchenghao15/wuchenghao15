#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育劳动教育服务 (v15.25.0)
====================================
提供劳动课程管理、劳动实践组织、劳动技能培训、劳动素养评估、
劳动教育基地、劳动教育资源、劳动教育评价、劳动教育研究等综合管理服务。

核心能力：
1. 劳动课程 - 课程管理、选课、课程安排、课程评价
2. 劳动实践 - 实践组织、报名、记录、成果管理
3. 技能培训 - 技能分类、培训计划、培训记录、考核认证
4. 素养评估 - 评估维度、评估标准、评估实施、结果分析、成长档案
5. 教育基地 - 基地管理、资源配置、合作协议、活动开展
6. 资源管理 - 教材资源、师资资源、设施资源、设备资源管理
7. 教育评价 - 评价体系、评价指标、评价实施、结果反馈
8. 教育研究 - 研究课题、研究成果、研究报告、学术交流
9. 统计分析 - 综合统计、趋势分析、报表生成
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_labor_education_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LaborEducation')


# ========== 劳动教育配置 ==========

LABOR_TYPES = {
    'daily': {'name': '日常生活劳动', 'description': '个人生活自理、家庭事务处理'},
    'production': {'name': '生产劳动', 'description': '工农业生产、产品制造'},
    'service': {'name': '服务性劳动', 'description': '社会服务、公益服务'},
    'technical': {'name': '技术劳动', 'description': '技术应用、工艺操作'},
    'creative': {'name': '创意劳动', 'description': '创新设计、文化创作'},
    'social_practice': {'name': '社会实践', 'description': '社会调查、社区服务'},
    'volunteer': {'name': '志愿服务', 'description': '公益志愿、义务劳动'},
    'work_study': {'name': '勤工俭学', 'description': '有偿劳动、实践锻炼'}
}

COURSE_TYPES = {
    'required': {'name': '必修课程', 'compulsory': True},
    'elective': {'name': '选修课程', 'compulsory': False},
    'practice': {'name': '实践课程', 'compulsory': False},
    'comprehensive': {'name': '综合课程', 'compulsory': False},
    'school_based': {'name': '校本课程', 'compulsory': False},
    'special': {'name': '特色课程', 'compulsory': False},
    'research': {'name': '研究性学习', 'compulsory': False},
    'project': {'name': '项目式学习', 'compulsory': False}
}

PRACTICE_TYPES = {
    'school': {'name': '校内实践', 'location': '校内'},
    'off_school': {'name': '校外实践', 'location': '校外'},
    'community': {'name': '社区实践', 'location': '社区'},
    'enterprise': {'name': '企业实践', 'location': '企业'},
    'labor_base': {'name': '劳动基地', 'location': '基地'},
    'farm': {'name': '农场实践', 'location': '农场'},
    'factory': {'name': '工厂实践', 'location': '工厂'},
    'service': {'name': '服务实践', 'location': '服务场所'}
}

SKILL_CATEGORIES = {
    'life': {'name': '生活技能', 'description': '日常生活所需技能'},
    'vocational': {'name': '职业技能', 'description': '职业岗位所需技能'},
    'professional': {'name': '专业技能', 'description': '专业领域技能'},
    'general': {'name': '通用技能', 'description': '跨领域通用技能'},
    'innovation': {'name': '创新技能', 'description': '创新思维与方法'},
    'teamwork': {'name': '团队协作', 'description': '团队合作能力'},
    'communication': {'name': '沟通能力', 'description': '人际沟通表达'},
    'problem_solving': {'name': '问题解决', 'description': '分析解决问题'}
}

ASSESSMENT_DIMENSIONS = {
    'attitude': {'name': '劳动态度', 'weight': 0.15},
    'skill': {'name': '劳动技能', 'weight': 0.20},
    'achievement': {'name': '劳动成果', 'weight': 0.20},
    'innovation': {'name': '劳动创新', 'weight': 0.15},
    'cooperation': {'name': '劳动合作', 'weight': 0.10},
    'responsibility': {'name': '劳动责任', 'weight': 0.10},
    'safety': {'name': '劳动安全', 'weight': 0.05},
    'habit': {'name': '劳动习惯', 'weight': 0.05}
}

BASE_TYPES = {
    'labor': {'name': '劳动教育基地', 'purpose': '劳动教育实践'},
    'social': {'name': '社会实践基地', 'purpose': '社会实践活动'},
    'innovation': {'name': '创新创业基地', 'purpose': '创新创业实践'},
    'volunteer': {'name': '志愿服务基地', 'purpose': '志愿服务活动'},
    'school_enterprise': {'name': '校企合作基地', 'purpose': '校企合作实践'},
    'study_travel': {'name': '研学基地', 'purpose': '研学旅行活动'},
    'community': {'name': '社区基地', 'purpose': '社区实践活动'},
    'farm': {'name': '农场基地', 'purpose': '农业劳动实践'}
}

RESOURCE_TYPES = {
    'textbook': {'name': '教材资源', 'category': 'teaching'},
    'teacher': {'name': '师资资源', 'category': 'human'},
    'facility': {'name': '设施资源', 'category': 'physical'},
    'equipment': {'name': '设备资源', 'category': 'physical'},
    'network': {'name': '网络资源', 'category': 'digital'},
    'case': {'name': '案例资源', 'category': 'teaching'},
    'course': {'name': '课程资源', 'category': 'teaching'},
    'evaluation': {'name': '评价资源', 'category': 'assessment'}
}

RESEARCH_TYPES = {
    'theory': {'name': '劳动教育理论', 'focus': '理论研究'},
    'practice': {'name': '劳动教育实践', 'focus': '实践探索'},
    'policy': {'name': '劳动教育政策', 'focus': '政策研究'},
    'evaluation': {'name': '劳动教育评价', 'focus': '评价体系'},
    'curriculum': {'name': '劳动教育课程', 'focus': '课程建设'},
    'teacher': {'name': '劳动教育师资', 'focus': '师资培养'},
    'model': {'name': '劳动教育模式', 'focus': '模式创新'},
    'innovation': {'name': '劳动教育创新', 'focus': '创新发展'}
}


class LaborEducationService:
    """教育劳动教育服务"""

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
                        labor_type TEXT NOT NULL,
                        course_type TEXT NOT NULL,
                        education_type TEXT,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 2,
                        location TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        objectives TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_schedules (
                        schedule_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        weekday INTEGER,
                        start_time TEXT,
                        end_time TEXT,
                        location TEXT,
                        week_range TEXT,
                        created_at TEXT,
                        FOREIGN KEY(course_id) REFERENCES labor_courses(course_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_practice (
                        practice_id TEXT PRIMARY KEY,
                        practice_name TEXT NOT NULL,
                        practice_type TEXT NOT NULL,
                        education_type TEXT,
                        grade_level INTEGER,
                        organizer TEXT,
                        description TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_participants INTEGER DEFAULT 50,
                        registered_count INTEGER DEFAULT 0,
                        safety_requirements TEXT,
                        status TEXT DEFAULT 'scheduled',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS practice_records (
                        record_id TEXT PRIMARY KEY,
                        practice_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        registration_date TEXT,
                        attendance INTEGER DEFAULT 0,
                        performance TEXT,
                        score REAL,
                        reflection TEXT,
                        status TEXT DEFAULT 'registered',
                        FOREIGN KEY(practice_id) REFERENCES labor_practice(practice_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_skills (
                        skill_id TEXT PRIMARY KEY,
                        skill_name TEXT NOT NULL,
                        skill_category TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        proficiency_levels TEXT,
                        duration_hours INTEGER,
                        prerequisites TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS skill_training (
                        training_id TEXT PRIMARY KEY,
                        skill_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        hours_completed INTEGER DEFAULT 0,
                        proficiency_level TEXT,
                        assessment_result TEXT,
                        certificate_no TEXT,
                        status TEXT DEFAULT 'in_progress',
                        FOREIGN KEY(skill_id) REFERENCES labor_skills(skill_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_literacy (
                        literacy_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        academic_year TEXT,
                        total_hours INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS literacy_assessment (
                        assessment_id TEXT PRIMARY KEY,
                        literacy_id TEXT NOT NULL,
                        assessment_date TEXT,
                        dimension TEXT,
                        score REAL,
                        comment TEXT,
                        assessor TEXT,
                        created_at TEXT,
                        FOREIGN KEY(literacy_id) REFERENCES labor_literacy(literacy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_education_base (
                        base_id TEXT PRIMARY KEY,
                        base_name TEXT NOT NULL,
                        base_type TEXT NOT NULL,
                        education_type TEXT,
                        address TEXT,
                        contact_person TEXT,
                        contact_phone TEXT,
                        description TEXT,
                        capacity INTEGER,
                        facilities TEXT,
                        cooperation_status TEXT DEFAULT 'active',
                        cooperation_agreement TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS base_resources (
                        resource_id TEXT PRIMARY KEY,
                        base_id TEXT NOT NULL,
                        resource_name TEXT NOT NULL,
                        resource_type TEXT,
                        quantity INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        FOREIGN KEY(base_id) REFERENCES labor_education_base(base_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_education_resource (
                        resource_id TEXT PRIMARY KEY,
                        resource_name TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        file_path TEXT,
                        url TEXT,
                        provider TEXT,
                        usage_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_management (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_id TEXT NOT NULL,
                        operation_type TEXT,
                        operator TEXT,
                        operation_time TEXT,
                        details TEXT,
                        FOREIGN KEY(resource_id) REFERENCES labor_education_resource(resource_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_education_evaluation (
                        evaluation_id TEXT PRIMARY KEY,
                        evaluation_name TEXT NOT NULL,
                        education_type TEXT,
                        target_type TEXT,
                        dimensions TEXT,
                        weight_config TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        result_id TEXT PRIMARY KEY,
                        evaluation_id TEXT NOT NULL,
                        target_id INTEGER,
                        target_name TEXT,
                        education_type TEXT,
                        scores TEXT,
                        total_score REAL,
                        grade TEXT,
                        feedback TEXT,
                        evaluator TEXT,
                        evaluation_date TEXT,
                        FOREIGN KEY(evaluation_id) REFERENCES labor_education_evaluation(evaluation_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labor_education_research (
                        research_id TEXT PRIMARY KEY,
                        research_name TEXT NOT NULL,
                        research_type TEXT NOT NULL,
                        education_type TEXT,
                        lead_researcher TEXT,
                        team_members TEXT,
                        description TEXT,
                        objectives TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        budget REAL,
                        status TEXT DEFAULT 'in_progress',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS research_records (
                        record_id TEXT PRIMARY KEY,
                        research_id TEXT NOT NULL,
                        record_type TEXT,
                        content TEXT,
                        author TEXT,
                        record_date TEXT,
                        file_path TEXT,
                        FOREIGN KEY(research_id) REFERENCES labor_education_research(research_id)
                    )
                ''')
                conn.commit()
                logger.info('教育劳动教育服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 劳动课程 ==========

    def create_labor_course(self, course_name: str, labor_type: str,
                            course_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"lbc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_courses (
                            course_id, course_name, labor_type, course_type,
                            education_type, grade_level, teacher_id, teacher_name,
                            semester, weekly_hours, location, max_students,
                            enrolled_count, description, objectives, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?)
                    ''', (course_id, course_name, labor_type, course_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('semester'), kwargs.get('weekly_hours', 2),
                          kwargs.get('location'), kwargs.get('max_students', 30),
                          kwargs.get('description'), kwargs.get('objectives'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建劳动课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建劳动课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_labor_course(self, course_id: str, student_id: int,
                            student_name: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT max_students, enrolled_count, status, education_type
                        FROM labor_courses WHERE course_id = ?
                    ''', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    if course[3] and education_type and course[3] != education_type:
                        return {'success': False, 'error': '课程类型不匹配'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO labor_literacy (literacy_id, student_id, student_name,
                            education_type, grade_level, academic_year, total_hours, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 0, 'active', ?)
                    ''', (f"lit_{uuid.uuid4().hex[:12]}", student_id, student_name,
                          education_type, kwargs.get('grade_level'),
                          kwargs.get('academic_year', now[:4]), now))
                    cursor.execute('UPDATE labor_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?',
                                 (now, course_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'劳动选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_course_schedule(self, course_id: str, weekday: int,
                            start_time: str, end_time: str, **kwargs) -> Dict[str, Any]:
        try:
            schedule_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT course_id FROM labor_courses WHERE course_id = ?', (course_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '课程不存在'}
                    cursor.execute('''
                        INSERT INTO course_schedules (schedule_id, course_id, weekday,
                            start_time, end_time, location, week_range, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (schedule_id, course_id, weekday, start_time, end_time,
                          kwargs.get('location'), kwargs.get('week_range'), now))
                    conn.commit()
                    return {'success': True, 'schedule_id': schedule_id}
        except Exception as e:
            logger.error(f'添加课程安排失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course_schedule(self, course_id: str = None, student_id: int = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if course_id:
                    cursor.execute('SELECT * FROM course_schedules WHERE course_id = ?', (course_id,))
                    schedules = [dict(s) for s in cursor.fetchall()]
                else:
                    cursor.execute('SELECT * FROM course_schedules')
                    schedules = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'schedules': schedules}
        except Exception as e:
            logger.error(f'获取课程安排失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 劳动实践 ==========

    def create_labor_practice(self, practice_name: str, practice_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            practice_id = f"lbp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_practice (
                            practice_id, practice_name, practice_type, education_type,
                            grade_level, organizer, description, location,
                            start_date, end_date, max_participants, registered_count,
                            safety_requirements, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'scheduled', ?, ?)
                    ''', (practice_id, practice_name, practice_type,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('organizer'), kwargs.get('description'),
                          kwargs.get('location'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('max_participants', 50),
                          kwargs.get('safety_requirements'), now, now))
                    conn.commit()
                    logger.info(f'创建劳动实践: {practice_name} ({practice_id})')
                    return {'success': True, 'practice_id': practice_id}
        except Exception as e:
            logger.error(f'创建劳动实践失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_practice(self, practice_id: str, student_id: int,
                          student_name: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT max_participants, registered_count, status, education_type
                        FROM labor_practice WHERE practice_id = ?
                    ''', (practice_id,))
                    practice = cursor.fetchone()
                    if not practice:
                        return {'success': False, 'error': '实践活动不存在'}
                    if practice[2] != 'scheduled':
                        return {'success': False, 'error': '实践活动状态不允许报名'}
                    if practice[0] and practice[1] >= practice[0]:
                        return {'success': False, 'error': '名额已满'}
                    if practice[3] and education_type and practice[3] != education_type:
                        return {'success': False, 'error': '实践类型不匹配'}
                    record_id = f"prr_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT OR IGNORE INTO practice_records (record_id, practice_id, student_id,
                            student_name, registration_date, status)
                        VALUES (?, ?, ?, ?, ?, 'registered')
                    ''', (record_id, practice_id, student_id, student_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE labor_practice SET registered_count = registered_count + 1, updated_at = ? WHERE practice_id = ?',
                                     (now, practice_id))
                        conn.commit()
                        return {'success': True, 'record_id': record_id}
                    return {'success': False, 'error': '已报名该实践'}
        except Exception as e:
            logger.error(f'实践报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_practice_attendance(self, record_id: str, attended: bool = True) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE practice_records SET attendance = ?, status = ? WHERE record_id = ?',
                                 (1 if attended else 0, 'completed' if attended else 'absent', record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'attendance': attended}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'记录实践考勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_practice(self, record_id: str, performance: str,
                          score: float = None, reflection: str = None) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE practice_records SET performance = ?, score = ?, reflection = ?, status = ? WHERE record_id = ?',
                                 (performance, score, reflection, 'evaluated', record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'评价实践表现失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 技能培训 ==========

    def create_skill(self, skill_name: str, skill_category: str, **kwargs) -> Dict[str, Any]:
        try:
            skill_id = f"skl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_skills (
                            skill_id, skill_name, skill_category, education_type,
                            description, proficiency_levels, duration_hours,
                            prerequisites, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (skill_id, skill_name, skill_category,
                          kwargs.get('education_type'), kwargs.get('description'),
                          json.dumps(kwargs.get('proficiency_levels', ['入门', '初级', '中级', '高级'])),
                          kwargs.get('duration_hours', 20), kwargs.get('prerequisites'), now))
                    conn.commit()
                    logger.info(f'创建技能: {skill_name} ({skill_id})')
                    return {'success': True, 'skill_id': skill_id}
        except Exception as e:
            logger.error(f'创建技能失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_skill_training(self, skill_id: str, student_id: int,
                             student_name: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            training_id = f"trn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT skill_id, education_type FROM labor_skills WHERE skill_id = ? AND status = ?',
                                 (skill_id, 'active'))
                    skill = cursor.fetchone()
                    if not skill:
                        return {'success': False, 'error': '技能不存在或已停用'}
                    if skill[1] and education_type and skill[1] != education_type:
                        return {'success': False, 'error': '技能类型不匹配'}
                    cursor.execute('''
                        INSERT INTO skill_training (training_id, skill_id, student_id,
                            student_name, education_type, start_date, hours_completed, status)
                        VALUES (?, ?, ?, ?, ?, ?, 0, 'in_progress')
                    ''', (training_id, skill_id, student_id, student_name, education_type, now[:10]))
                    conn.commit()
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'开始技能培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_hours(self, training_id: str, hours: float) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT hours_completed, status FROM skill_training WHERE training_id = ?', (training_id,))
                    training = cursor.fetchone()
                    if not training:
                        return {'success': False, 'error': '培训记录不存在'}
                    if training[1] != 'in_progress':
                        return {'success': False, 'error': '培训已结束'}
                    new_hours = training[0] + hours
                    cursor.execute('UPDATE skill_training SET hours_completed = ? WHERE training_id = ?', (new_hours, training_id))
                    conn.commit()
                    return {'success': True, 'total_hours': new_hours}
        except Exception as e:
            logger.error(f'记录培训学时失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_skill_assessment(self, training_id: str, proficiency_level: str,
                                   result: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            certificate_no = f"SCL{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if result == 'pass' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE skill_training SET proficiency_level = ?, assessment_result = ?, certificate_no = ?, status = ? WHERE training_id = ?',
                                 (proficiency_level, result, certificate_no, 'completed', training_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'certificate_no': certificate_no}
                    return {'success': False, 'error': '培训记录不存在'}
        except Exception as e:
            logger.error(f'完成技能考核失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 素养评估 ==========

    def create_literacy_record(self, student_id: int, student_name: str,
                               education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            literacy_id = f"lit_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_literacy (
                            literacy_id, student_id, student_name, education_type,
                            grade_level, academic_year, total_hours, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (literacy_id, student_id, student_name, education_type,
                          kwargs.get('grade_level'), kwargs.get('academic_year', now[:4]),
                          now, now))
                    conn.commit()
                    return {'success': True, 'literacy_id': literacy_id}
        except Exception as e:
            logger.error(f'创建素养档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_assessment_record(self, literacy_id: str, dimension: str,
                              score: float, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"ast_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT literacy_id FROM labor_literacy WHERE literacy_id = ?', (literacy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '素养档案不存在'}
                    cursor.execute('''
                        INSERT INTO literacy_assessment (assessment_id, literacy_id,
                            assessment_date, dimension, score, comment, assessor, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (assessment_id, literacy_id, now[:10], dimension, score,
                          kwargs.get('comment'), kwargs.get('assessor'), now))
                    conn.commit()
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'添加评估记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_literacy_score(self, literacy_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT dimension, score FROM literacy_assessment WHERE literacy_id = ?', (literacy_id,))
                assessments = cursor.fetchall()
                if not assessments:
                    return {'success': False, 'error': '暂无评估数据'}
                total_score = 0.0
                total_weight = 0.0
                for dimension, score in assessments:
                    weight = ASSESSMENT_DIMENSIONS.get(dimension, {}).get('weight', 0.125)
                    total_score += score * weight
                    total_weight += weight
                if total_weight > 0:
                    total_score = round(total_score / total_weight, 2)
                return {'success': True, 'total_score': total_score, 'assessment_count': len(assessments)}
        except Exception as e:
            logger.error(f'计算素养得分失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_literacy_hours(self, literacy_id: str, hours: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT total_hours FROM labor_literacy WHERE literacy_id = ?', (literacy_id,))
                    literacy = cursor.fetchone()
                    if not literacy:
                        return {'success': False, 'error': '素养档案不存在'}
                    new_hours = literacy[0] + hours
                    cursor.execute('UPDATE labor_literacy SET total_hours = ?, updated_at = ? WHERE literacy_id = ?',
                                 (new_hours, now, literacy_id))
                    conn.commit()
                    return {'success': True, 'total_hours': new_hours}
        except Exception as e:
            logger.error(f'更新素养学时失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_literacy_profile(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_literacy WHERE student_id = ?'
                params = [student_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                literacy = cursor.fetchone()
                if not literacy:
                    return {'success': False, 'error': '素养档案不存在'}
                literacy_dict = dict(literacy)
                cursor.execute('SELECT * FROM literacy_assessment WHERE literacy_id = ? ORDER BY assessment_date DESC',
                             (literacy_dict['literacy_id'],))
                assessments = [dict(a) for a in cursor.fetchall()]
                literacy_dict['assessments'] = assessments
                return {'success': True, 'literacy': literacy_dict}
        except Exception as e:
            logger.error(f'获取素养档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育基地 ==========

    def create_education_base(self, base_name: str, base_type: str, **kwargs) -> Dict[str, Any]:
        try:
            base_id = f"bas_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_education_base (
                            base_id, base_name, base_type, education_type,
                            address, contact_person, contact_phone, description,
                            capacity, facilities, cooperation_status,
                            cooperation_agreement, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (base_id, base_name, base_type, kwargs.get('education_type'),
                          kwargs.get('address'), kwargs.get('contact_person'),
                          kwargs.get('contact_phone'), kwargs.get('description'),
                          kwargs.get('capacity'), json.dumps(kwargs.get('facilities', [])),
                          kwargs.get('cooperation_agreement'), now, now))
                    conn.commit()
                    logger.info(f'创建教育基地: {base_name} ({base_id})')
                    return {'success': True, 'base_id': base_id}
        except Exception as e:
            logger.error(f'创建教育基地失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_base_resource(self, base_id: str, resource_name: str,
                          resource_type: str, **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"brs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT base_id FROM labor_education_base WHERE base_id = ?', (base_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '基地不存在'}
                    cursor.execute('''
                        INSERT INTO base_resources (resource_id, base_id, resource_name,
                            resource_type, quantity, status, created_at)
                        VALUES (?, ?, ?, ?, ?, 'available', ?)
                    ''', (resource_id, base_id, resource_name, resource_type,
                          kwargs.get('quantity', 1), now))
                    conn.commit()
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'添加基地资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_base_cooperation(self, base_id: str, status: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE labor_education_base SET cooperation_status = ?, cooperation_agreement = ?, updated_at = ? WHERE base_id = ?',
                                 (status, kwargs.get('cooperation_agreement'), now, base_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '基地不存在'}
        except Exception as e:
            logger.error(f'更新基地合作状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_education_bases(self, base_type: str = None, education_type: str = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_education_base WHERE 1=1'
                params = []
                if base_type:
                    query += ' AND base_type = ?'
                    params.append(base_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                bases = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'bases': bases, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取基地列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源管理 ==========

    def create_resource(self, resource_name: str, resource_type: str, **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"rsr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_education_resource (
                            resource_id, resource_name, resource_type, education_type,
                            description, file_path, url, provider,
                            usage_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'available', ?, ?)
                    ''', (resource_id, resource_name, resource_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('file_path'), kwargs.get('url'),
                          kwargs.get('provider'), now, now))
                    conn.commit()
                    logger.info(f'创建资源: {resource_name} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'创建资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def use_resource(self, resource_id: str, operator: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM labor_education_resource WHERE resource_id = ?', (resource_id,))
                    resource = cursor.fetchone()
                    if not resource:
                        return {'success': False, 'error': '资源不存在'}
                    if resource[0] != 'available':
                        return {'success': False, 'error': '资源不可用'}
                    cursor.execute('UPDATE labor_education_resource SET usage_count = usage_count + 1 WHERE resource_id = ?', (resource_id,))
                    cursor.execute('INSERT INTO resource_management (resource_id, operation_type, operator, operation_time, details) VALUES (?, ?, ?, ?, ?)',
                                 (resource_id, 'use', operator, now, '资源使用'))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'使用资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_resource(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'resource_name' in kwargs:
                        updates.append('resource_name = ?')
                        params.append(kwargs['resource_name'])
                    if 'description' in kwargs:
                        updates.append('description = ?')
                        params.append(kwargs['description'])
                    if 'status' in kwargs:
                        updates.append('status = ?')
                        params.append(kwargs['status'])
                    if 'provider' in kwargs:
                        updates.append('provider = ?')
                        params.append(kwargs['provider'])
                    if updates:
                        updates.append('updated_at = ?')
                        params.append(now)
                        params.append(resource_id)
                        cursor.execute(f'UPDATE labor_education_resource SET {", ".join(updates)} WHERE resource_id = ?', params)
                        conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_resources(self, resource_type: str = None, education_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_education_resource WHERE 1=1'
                params = []
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资源列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育评价 ==========

    def create_evaluation(self, evaluation_name: str, **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"eva_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            dimensions = kwargs.get('dimensions', list(ASSESSMENT_DIMENSIONS.keys()))
            weight_config = {d: ASSESSMENT_DIMENSIONS[d]['weight'] for d in dimensions}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_education_evaluation (
                            evaluation_id, evaluation_name, education_type,
                            target_type, dimensions, weight_config, description,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (evaluation_id, evaluation_name, kwargs.get('education_type'),
                          kwargs.get('target_type'), json.dumps(dimensions),
                          json.dumps(weight_config), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建评价体系: {evaluation_name} ({evaluation_id})')
                    return {'success': True, 'evaluation_id': evaluation_id}
        except Exception as e:
            logger.error(f'创建评价体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_evaluation(self, evaluation_id: str, target_id: int,
                           target_name: str, scores: Dict[str, float],
                           **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"evr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT weight_config, education_type FROM labor_education_evaluation WHERE evaluation_id = ?', (evaluation_id,))
                    evaluation = cursor.fetchone()
                    if not evaluation:
                        return {'success': False, 'error': '评价体系不存在'}
                    weight_config = json.loads(evaluation[0])
                    total_score = 0.0
                    total_weight = 0.0
                    for dim, score in scores.items():
                        weight = weight_config.get(dim, 0.125)
                        total_score += score * weight
                        total_weight += weight
                    if total_weight > 0:
                        total_score = round(total_score / total_weight, 2)
                    grade = 'excellent' if total_score >= 90 else ('good' if total_score >= 80 else ('pass' if total_score >= 60 else 'fail'))
                    cursor.execute('''
                        INSERT INTO evaluation_results (
                            result_id, evaluation_id, target_id, target_name,
                            education_type, scores, total_score, grade,
                            feedback, evaluator, evaluation_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, evaluation_id, target_id, target_name,
                          evaluation[1], json.dumps(scores), total_score,
                          grade, kwargs.get('feedback'), kwargs.get('evaluator'),
                          now[:10]))
                    conn.commit()
                    return {'success': True, 'result_id': result_id, 'total_score': total_score, 'grade': grade}
        except Exception as e:
            logger.error(f'执行评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_results(self, target_id: int = None, evaluation_id: str = None,
                               education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evaluation_results WHERE 1=1'
                params = []
                if target_id:
                    query += ' AND target_id = ?'
                    params.append(target_id)
                if evaluation_id:
                    query += ' AND evaluation_id = ?'
                    params.append(evaluation_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY evaluation_date DESC'
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f'获取评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_evaluation_feedback(self, result_id: str, feedback: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE evaluation_results SET feedback = ? WHERE result_id = ?', (feedback, result_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '评价结果不存在'}
        except Exception as e:
            logger.error(f'更新评价反馈失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育研究 ==========

    def create_research_project(self, research_name: str, research_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            research_id = f"rsr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO labor_education_research (
                            research_id, research_name, research_type, education_type,
                            lead_researcher, team_members, description, objectives,
                            start_date, end_date, budget, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (research_id, research_name, research_type,
                          kwargs.get('education_type'), kwargs.get('lead_researcher'),
                          json.dumps(kwargs.get('team_members', [])),
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('budget', 0), now, now))
                    conn.commit()
                    logger.info(f'创建研究项目: {research_name} ({research_id})')
                    return {'success': True, 'research_id': research_id}
        except Exception as e:
            logger.error(f'创建研究项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_research_record(self, research_id: str, record_type: str,
                            content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"rrc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT research_id FROM labor_education_research WHERE research_id = ?', (research_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '研究项目不存在'}
                    cursor.execute('''
                        INSERT INTO research_records (record_id, research_id, record_type,
                            content, author, record_date, file_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, research_id, record_type, content,
                          kwargs.get('author'), now[:10], kwargs.get('file_path')))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加研究记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_research_project(self, research_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE labor_education_research SET status = ?, end_date = ?, updated_at = ? WHERE research_id = ?',
                                 ('completed', now[:10], now, research_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '研究项目不存在'}
        except Exception as e:
            logger.error(f'完成研究项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_research_projects(self, research_type: str = None, education_type: str = None,
                              status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM labor_education_research WHERE 1=1'
                params = []
                if research_type:
                    query += ' AND research_type = ?'
                    params.append(research_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取研究项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_labor_education_statistics(self, education_type: str = None,
                                        start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                query = 'SELECT COUNT(*) FROM labor_courses WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                stats['total_courses'] = cursor.fetchone()[0]

                query = 'SELECT COUNT(*) FROM labor_practice WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                stats['total_practices'] = cursor.fetchone()[0]

                query = 'SELECT COUNT(*) FROM labor_literacy WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                stats['total_students'] = cursor.fetchone()[0]

                query = 'SELECT COUNT(*) FROM labor_education_base WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                stats['total_bases'] = cursor.fetchone()[0]

                query = 'SELECT COUNT(*) FROM labor_education_resource WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                stats['total_resources'] = cursor.fetchone()[0]

                query = 'SELECT COUNT(*) FROM labor_education_research WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                stats['total_research'] = cursor.fetchone()[0]

                cursor.execute('SELECT SUM(total_hours) FROM labor_literacy WHERE 1=1' + (' AND education_type = ?' if education_type else ''), params)
                total_hours = cursor.fetchone()[0]
                stats['total_labor_hours'] = total_hours or 0

                cursor.execute('SELECT AVG(total_score) FROM evaluation_results WHERE 1=1' + (' AND education_type = ?' if education_type else ''), params)
                avg_score = cursor.fetchone()[0]
                stats['average_score'] = round(avg_score, 2) if avg_score else 0

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}